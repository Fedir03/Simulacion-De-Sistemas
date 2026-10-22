package ar.edu.itba.sds.tp4.bench;

import ar.edu.itba.sds.tp4.engine.billiard.BilliardSimulator;
import ar.edu.itba.sds.tp4.models.BilliardConfig;
import java.io.*;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;

/** Benchmark reanudable del Sistema 2 para F4 (tiempo de ejecución en función de N). */
public final class Tp4RuntimeBenchmark {
    private Tp4RuntimeBenchmark() { }
    private static final String HEADER = "order,n,seed,runtime_s,steps,used_count,status,session,finished_at";
    private static final Set<String> OPTIONS = Set.of("out", "ns", "seeds", "tf", "dt", "dt2", "x0",
            "order-seed", "batch", "warmup", "warmup-tol", "warmup-max", "warmup-seed");

    public static void main(String[] args) {
        try { run(parse(args), args); }
        catch (IllegalArgumentException | IOException e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        }
    }

    private static Map<String, String> parse(String[] args) {
        Map<String, String> result = new LinkedHashMap<>();
        for (int i = 0; i < args.length; i += 2) {
            if (!args[i].startsWith("--") || i + 1 >= args.length) throw new IllegalArgumentException("Se esperaba --opción valor");
            String key = args[i].substring(2);
            if (!OPTIONS.contains(key) || result.put(key, args[i + 1]) != null)
                throw new IllegalArgumentException("Opción inválida o repetida: " + args[i]);
        }
        return result;
    }

    private static void run(Map<String, String> options, String[] originalArgs) throws IOException {
        Path out = Path.of(required(options, "out"));
        int[] ns = Arrays.stream(required(options, "ns").split(",")).map(String::trim).mapToInt(Integer::parseInt).toArray();
        int seeds = integer(options, "seeds", 10), batch = integer(options, "batch", Integer.MAX_VALUE);
        double tf = number(options, "tf", 30), dt = number(options, "dt", 1e-5), dt2 = number(options, "dt2", 0.04);
        double x0 = number(options, "x0", 0.0175), warmupTol = number(options, "warmup-tol", 0.05);
        int warmupMax = integer(options, "warmup-max", 30);
        long orderSeed = whole(options, "order-seed", 20261020), warmupSeed = whole(options, "warmup-seed", 1000);
        String warmupSpec = options.getOrDefault("warmup", "300:5,600:0.32");
        if (ns.length == 0 || seeds < 1 || batch < 1 || tf <= 0 || dt <= 0 || dt2 <= 0 || warmupMax < 2)
            throw new IllegalArgumentException("Parámetros inválidos");

        String heap = fixedHeap();
        String protocol = "{\"engine\":\"TP4 BilliardSimulator\",\"N\":" + Arrays.toString(ns)
                + ",\"seeds\":" + seeds + ",\"tf\":" + tf + ",\"dt\":" + dt + ",\"dt2\":" + dt2
                + ",\"x0\":" + x0 + ",\"order_seed\":" + orderSeed + ",\"warmup\":\"" + warmupSpec
                + "\",\"warmup_seed\":" + warmupSeed + ",\"warmup_tolerance\":" + warmupTol
                + ",\"warmup_max\":" + warmupMax + ",\"heap\":\"" + heap
                + "\",\"timer\":\"System.nanoTime alrededor de BilliardSimulator.run, sin I/O\"}";
        Files.createDirectories(out);
        Path protocolFile = out.resolve("protocol.json"), runsFile = out.resolve("runs.csv");
        if (Files.exists(protocolFile) && !Files.readString(protocolFile).strip().equals(protocol))
            throw new IllegalArgumentException("La carpeta contiene otro protocolo; usá otra --out o los mismos parámetros");
        if (!Files.exists(protocolFile)) Files.writeString(protocolFile, protocol + System.lineSeparator());

        List<long[]> order = new ArrayList<>();
        for (int n : ns) for (long seed = 1; seed <= seeds; seed++) order.add(new long[]{n, seed});
        Collections.shuffle(order, new Random(orderSeed));
        Set<String> done = new HashSet<>();
        for (String[] row : readRows(runsFile)) done.add(row[1] + "," + row[2]);
        int session = sessionCount(out.resolve("sessions.csv")) + 1;

        System.err.printf("Sesión %d | heap %s | %d/%d corridas hechas%n", session, heap, done.size(), order.size());
        String warmupResult = warmup(warmupSpec, warmupSeed, warmupTol, warmupMax, dt, dt2, x0);
        append(out.resolve("sessions.csv"), session + ",start," + Instant.now() + ",\""
                + String.join(" ", originalArgs).replace("\"", "\"\"") + "\",\"" + warmupResult.replace("\"", "\"\"") + "\"");

        if (!Files.exists(runsFile)) append(runsFile, HEADER);
        int ran = 0;
        for (int i = 0; i < order.size() && ran < batch; i++) {
            int n = (int) order.get(i)[0]; long seed = order.get(i)[1];
            if (done.contains(n + "," + seed)) continue;
            Result result = timed(n, seed, tf, dt, dt2, x0);
            append(runsFile, i + "," + n + "," + seed + "," + result.runtime + "," + result.summary.steps()
                    + "," + result.summary.usedCount() + "," + result.summary.status().name().toLowerCase(Locale.ROOT)
                    + "," + session + "," + Instant.now());
            if (result.summary.status() != BilliardSimulator.Status.COMPLETED)
                throw new IllegalStateException("La corrida divergió: N=" + n + ", seed=" + seed);
            done.add(n + "," + seed); ran++;
            System.err.printf(Locale.ROOT, "[%d/%d] N=%d semilla=%d: %.3f s%n", done.size(), order.size(), n, seed, result.runtime);
        }
        append(out.resolve("sessions.csv"), session + ",end," + Instant.now() + ",runs=" + ran + ",complete=" + (done.size() == order.size()));
        System.err.println(done.size() == order.size() ? "Medición completa: " + out
                : "Faltan " + (order.size() - done.size()) + " corridas; reanudá con el mismo comando");
    }

    private record Result(double runtime, BilliardSimulator.Summary summary) { }

    private static Result timed(int n, long seed, double tf, double dt, double dt2, double x0) throws IOException {
        BilliardConfig config = BilliardConfig.of(n, seed, x0, dt, dt2, tf);
        BilliardSimulator simulator = BilliardSimulator.fromGrid(config, BilliardSimulator.defaultFinder(config));
        System.gc();
        long start = System.nanoTime();
        BilliardSimulator.Summary summary = simulator.run(frame -> { });
        return new Result((System.nanoTime() - start) / 1e9, summary);
    }

    private static String warmup(String spec, long seed, double tolerance, int max, double dt, double dt2, double x0) throws IOException {
        StringJoiner report = new StringJoiner(";");
        for (String item : spec.split(",")) {
            String[] pair = item.trim().split(":");
            if (pair.length != 2) throw new IllegalArgumentException("--warmup espera pares N:tf separados por comas");
            int n = Integer.parseInt(pair[0]); double tf = Double.parseDouble(pair[1]);
            List<Double> times = new ArrayList<>(); boolean stable = false;
            while (times.size() < max && !stable) {
                times.add(timed(n, seed, tf, dt, dt2, x0).runtime);
                int size = times.size();
                stable = size >= 2 && Math.abs(times.get(size - 1) - times.get(size - 2)) / times.get(size - 2) < tolerance;
            }
            System.err.printf(Locale.ROOT, "Warmup N=%d: %d repeticiones, %s%n", n, times.size(), stable ? "estable" : "sin estabilizar");
            report.add("N=" + n + " times=" + times + " stable=" + stable);
        }
        return report.toString();
    }

    private static String fixedHeap() {
        String xms = null, xmx = null;
        for (String arg : ManagementFactory.getRuntimeMXBean().getInputArguments()) {
            if (arg.startsWith("-Xms")) xms = arg.substring(4).toLowerCase(Locale.ROOT);
            if (arg.startsWith("-Xmx")) xmx = arg.substring(4).toLowerCase(Locale.ROOT);
        }
        if (xms == null || !xms.equals(xmx)) throw new IllegalArgumentException("Se requiere heap fijo, por ejemplo -Xms2g -Xmx2g");
        return "-Xms" + xms + " -Xmx" + xmx;
    }

    private static List<String[]> readRows(Path path) throws IOException {
        if (!Files.exists(path)) return List.of();
        return Files.readAllLines(path).stream().filter(line -> !line.isBlank() && !line.startsWith("order,"))
                .map(line -> line.split(",")).toList();
    }

    private static int sessionCount(Path path) throws IOException {
        if (!Files.exists(path)) return 0;
        return (int) Files.readAllLines(path).stream().filter(line -> line.matches("^[0-9]+,start,.*")).count();
    }

    private static void append(Path path, String line) throws IOException {
        try (FileOutputStream stream = new FileOutputStream(path.toFile(), true)) {
            stream.write((line + System.lineSeparator()).getBytes(StandardCharsets.UTF_8));
            stream.flush(); stream.getFD().sync();
        }
    }

    private static String required(Map<String, String> options, String key) {
        String value = options.get(key);
        if (value == null) throw new IllegalArgumentException("Falta --" + key);
        return value;
    }
    private static int integer(Map<String, String> o, String k, int d) { return Integer.parseInt(o.getOrDefault(k, Integer.toString(d))); }
    private static long whole(Map<String, String> o, String k, long d) { return Long.parseLong(o.getOrDefault(k, Long.toString(d))); }
    private static double number(Map<String, String> o, String k, double d) { return Double.parseDouble(o.getOrDefault(k, Double.toString(d))); }
}
