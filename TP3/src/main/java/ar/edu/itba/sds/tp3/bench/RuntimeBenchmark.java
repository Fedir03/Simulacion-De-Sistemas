package ar.edu.itba.sds.tp3.bench;

import java.io.*;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;

/**
 * Tiempo de ejecución vs N en una sola JVM calentada y reutilizada (TP4 D12). Protocolo:
 * 1. Heap fijo: exige -Xms igual a -Xmx, para que el recolector no redimensione el heap en medio de una tanda.
 * 2. Calentamiento descartado: para cada par N:tf de --warmup repite (N, warmup-seed, tf) hasta que dos corridas
 *    consecutivas difieran menos de warmup-tol, con un máximo de warmup-max. Se repite en cada reanudación.
 * 3. Control (una vez por carpeta): (control-n, control-seed, tf), para repetirlo con --control-only otro día.
 * 4. Medición: todos los pares (N, semilla 1..seeds) en orden mezclado con Random(order-seed), System.gc() antes de
 *    cada corrida y una fila en runs.csv con flush y sync. Al reanudar se saltean los pares ya medidos; --batch k
 *    corta después de k corridas.
 * El caso (motor y condición inicial) es un TimedCase; este driver no conoce el motor.
 */
public final class RuntimeBenchmark {
    private RuntimeBenchmark() { }
    private static final String RUNS_HEADER = "order,n,seed,runtime_s,events,goals,t90,session,finished_at";
    private static final Set<String> OPTIONS = Set.of("out", "ns", "seeds", "tf", "order-seed", "batch", "warmup",
            "warmup-tol", "warmup-max", "warmup-seed", "control-n", "control-seed", "control-only", "expected-total-h");

    public static Map<String, String> parse(String[] args) {
        Map<String, String> options = new LinkedHashMap<>();
        for (int i = 0; i < args.length; i += 2) {
            if (!args[i].startsWith("--") || i + 1 >= args.length) throw new IllegalArgumentException("Se esperaba --opción valor");
            if (options.put(args[i].substring(2), args[i + 1]) != null) throw new IllegalArgumentException("Opción repetida: " + args[i]);
        }
        return options;
    }

    public static void run(TimedCase c, Map<String, String> options, String[] originalArgs) throws IOException {
        for (String key : options.keySet()) if (!OPTIONS.contains(key)) throw new IllegalArgumentException("Opción inválida: " + key);
        if (!options.containsKey("out") || !options.containsKey("ns") || !options.containsKey("warmup"))
            throw new IllegalArgumentException("Faltan --out, --ns o --warmup (pares N:tf, p. ej. 300:5,600:0.3)");
        String heap = fixedHeap();
        Path out = Path.of(options.get("out"));
        int[] ns = Arrays.stream(options.get("ns").split(",")).mapToInt(s -> Integer.parseInt(s.trim())).toArray();
        String[] warmupSpec = options.get("warmup").split(",");
        int[] warmupNs = new int[warmupSpec.length];
        double[] warmupTfs = new double[warmupSpec.length];
        for (int i = 0; i < warmupSpec.length; i++) {
            String[] pair = warmupSpec[i].trim().split(":");
            if (pair.length != 2) throw new IllegalArgumentException("--warmup espera pares N:tf separados por comas");
            warmupNs[i] = Integer.parseInt(pair[0]);
            warmupTfs[i] = Double.parseDouble(pair[1]);
            if (!(warmupTfs[i] > 0)) throw new IllegalArgumentException("tf de calentamiento inválido");
        }
        int seeds = Integer.parseInt(options.getOrDefault("seeds", "10"));
        double tf = Double.parseDouble(options.getOrDefault("tf", "30"));
        long orderSeed = Long.parseLong(options.getOrDefault("order-seed", "20261020"));
        int batch = Integer.parseInt(options.getOrDefault("batch", Integer.toString(Integer.MAX_VALUE)));
        double warmupTol = Double.parseDouble(options.getOrDefault("warmup-tol", "0.05"));
        int warmupMax = Integer.parseInt(options.getOrDefault("warmup-max", "30"));
        long warmupSeed = Long.parseLong(options.getOrDefault("warmup-seed", "1000"));
        int controlN = Integer.parseInt(options.getOrDefault("control-n", "400"));
        long controlSeed = Long.parseLong(options.getOrDefault("control-seed", "1"));
        boolean controlOnly = Boolean.parseBoolean(options.getOrDefault("control-only", "false"));
        if (seeds < 1 || batch < 1 || warmupMax < 2 || !(tf > 0)) throw new IllegalArgumentException("Parámetros inválidos");

        String protocol = "{\"case\": " + c.describeJson() + ", \"ns\": " + Arrays.toString(ns) + ", \"seeds\": " + seeds + ", \"tf\": " + tf
                + ", \"order_seed\": " + orderSeed + ", \"warmup\": {\"ns\": " + Arrays.toString(warmupNs) + ", \"tf\": " + Arrays.toString(warmupTfs)
                + ", \"seed\": " + warmupSeed + ", \"tolerance\": " + warmupTol + ", \"max_reps\": " + warmupMax + "}"
                + ", \"control\": {\"n\": " + controlN + ", \"seed\": " + controlSeed + ", \"tf\": " + tf
                + ", \"criterion\": \"runtime dentro de media ± 2σ (n−1) de las semillas de n en summary.csv\"}"
                + ", \"heap\": " + q(heap) + ", \"gc_before_each_run\": true, \"timer\": \"System.nanoTime alrededor de la simulación\"}";
        Files.createDirectories(out);
        Path protocolFile = out.resolve("protocol.json"), runsFile = out.resolve("runs.csv");
        if (Files.exists(protocolFile)) {
            if (!Files.readString(protocolFile).strip().equals(protocol))
                throw new IllegalArgumentException("La carpeta tiene otro protocolo (" + protocolFile + "); usar otra --out o los mismos parámetros");
        } else {
            if (controlOnly) throw new IllegalArgumentException("--control-only requiere una carpeta con una medición previa");
            Files.writeString(protocolFile, protocol + System.lineSeparator());
        }

        // Orden determinista: al reanudar se recorre la misma lista y se saltean los pares ya medidos.
        List<long[]> order = new ArrayList<>();
        for (int n : ns) for (long s = 1; s <= seeds; s++) order.add(new long[]{n, s});
        Collections.shuffle(order, new Random(orderSeed));
        Set<String> done = new HashSet<>();
        for (String[] row : readRuns(runsFile)) done.add(row[1] + "," + row[2]);
        int session = (int) lines(out.resolve("sessions.jsonl")).stream().filter(l -> l.contains("\"event\": \"start\"")).count() + 1;

        String started = Instant.now().toString();
        System.err.println("Sesión " + session + " | heap " + heap + " | " + done.size() + "/" + order.size() + " corridas hechas");
        String warmup = warmup(c, warmupNs, warmupTfs, warmupSeed, warmupTol, warmupMax);
        append(out.resolve("sessions.jsonl"), "{\"session\": " + session + ", \"event\": \"start\", \"at\": " + q(started)
                + ", \"mode\": " + q(controlOnly ? "control-only" : "measure") + ", \"command\": " + q(String.join(" ", originalArgs))
                + ", \"jvm_args\": " + q(String.join(" ", ManagementFactory.getRuntimeMXBean().getInputArguments()))
                + ", \"java\": " + q(System.getProperty("java.vendor") + " " + System.getProperty("java.version"))
                + ", \"git_head\": " + q(gitHead()) + ", \"expected_total_h\": " + options.getOrDefault("expected-total-h", "null")
                + ", \"warmup\": " + warmup + "}");

        if (controlOnly || !Files.exists(out.resolve("control.jsonl"))) {
            TimedCase.RunResult r = timed(c, controlN, controlSeed, tf);
            String line = "{\"session\": " + session + ", \"at\": " + q(Instant.now().toString()) + ", \"n\": " + controlN + ", \"seed\": " + controlSeed
                    + ", \"tf\": " + tf + ", \"runtime_s\": " + r.runtimeSeconds() + ", \"events\": " + r.events() + ", \"goals\": " + r.goals() + "}";
            append(out.resolve(controlOnly ? "control_rechecks.jsonl" : "control.jsonl"), line);
            System.err.printf(Locale.ROOT, "Control N=%d semilla=%d: %.3f s, eventos=%d%n", controlN, controlSeed, r.runtimeSeconds(), r.events());
        }

        int ran = 0;
        if (!controlOnly) {
            if (!Files.exists(runsFile)) append(runsFile, RUNS_HEADER);
            for (int i = 0; i < order.size() && ran < batch; i++) {
                int n = (int) order.get(i)[0];
                long seed = order.get(i)[1];
                if (done.contains(n + "," + seed)) continue;
                TimedCase.RunResult r = timed(c, n, seed, tf);
                append(runsFile, i + "," + n + "," + seed + "," + r.runtimeSeconds() + "," + r.events() + "," + r.goals() + "," + r.t90()
                        + "," + session + "," + Instant.now());
                done.add(n + "," + seed);
                ran++;
                System.err.printf(Locale.ROOT, "[%d/%d] N=%d semilla=%d: %.3f s, eventos=%d%n", done.size(), order.size(), n, seed, r.runtimeSeconds(), r.events());
                writeSummaryAndMeta(out, controlN);
            }
        }
        append(out.resolve("sessions.jsonl"), "{\"session\": " + session + ", \"event\": \"end\", \"at\": " + q(Instant.now().toString())
                + ", \"runs\": " + ran + ", \"complete\": " + (done.size() == order.size()) + "}");
        writeSummaryAndMeta(out, controlN);
        System.err.println(done.size() == order.size() ? "Medición completa: " + out : "Faltan " + (order.size() - done.size()) + " corridas; reanudar con el mismo comando");
    }

    /** Exige -Xms y -Xmx presentes e iguales; devuelve el valor. */
    private static String fixedHeap() {
        String xms = null, xmx = null;
        for (String a : ManagementFactory.getRuntimeMXBean().getInputArguments()) {
            if (a.startsWith("-Xms")) xms = a.substring(4).toLowerCase(Locale.ROOT);
            if (a.startsWith("-Xmx")) xmx = a.substring(4).toLowerCase(Locale.ROOT);
        }
        if (xms == null || xmx == null || !xms.equals(xmx))
            throw new IllegalArgumentException("Heap fijo requerido: correr con -Xms y -Xmx iguales (p. ej. -Xms1g -Xmx1g); recibido -Xms=" + xms + " -Xmx=" + xmx);
        return "-Xms" + xms + " -Xmx" + xmx;
    }

    private static TimedCase.RunResult timed(TimedCase c, int n, long seed, double tf) throws IOException {
        c.prepare(n, seed);
        System.gc();
        return c.runTimed(tf);
    }

    private static String warmup(TimedCase c, int[] ns, double[] tfs, long seed, double tol, int max) throws IOException {
        StringJoiner blocks = new StringJoiner(", ", "[", "]");
        for (int w = 0; w < ns.length; w++) {
            int n = ns[w];
            double tf = tfs[w];
            List<Double> times = new ArrayList<>();
            boolean converged = false;
            while (times.size() < max && !converged) {
                times.add(timed(c, n, seed, tf).runtimeSeconds());
                int k = times.size();
                converged = k >= 2 && Math.abs(times.get(k - 1) - times.get(k - 2)) / times.get(k - 2) < tol;
            }
            double total = times.stream().mapToDouble(Double::doubleValue).sum();
            System.err.printf(Locale.ROOT, "Calentamiento N=%d: %d repeticiones, %.1f s descartados, %s%n", n, times.size(), total,
                    converged ? "estable" : "SIN estabilizar (máximo de repeticiones)");
            blocks.add("{\"n\": " + n + ", \"tf\": " + tf + ", \"seed\": " + seed + ", \"runtimes_s\": " + times + ", \"discarded_s\": " + total
                    + ", \"converged\": " + converged + "}");
        }
        return blocks.toString();
    }

    private static void writeSummaryAndMeta(Path out, int controlN) throws IOException {
        Map<Integer, List<String[]>> byN = new TreeMap<>();
        for (String[] row : readRuns(out.resolve("runs.csv"))) byN.computeIfAbsent(Integer.parseInt(row[1]), k -> new ArrayList<>()).add(row);
        StringBuilder summary = new StringBuilder("n,realizations,runtime_mean_s,runtime_std_s,events_mean,goals_mean").append(System.lineSeparator());
        double[] control = null;
        for (var e : byN.entrySet()) {
            double[] times = e.getValue().stream().mapToDouble(r -> Double.parseDouble(r[3])).toArray();
            double mean = Arrays.stream(times).average().orElse(Double.NaN), std = std(times, mean);
            summary.append(e.getKey()).append(',').append(times.length).append(',').append(mean).append(',').append(std).append(',')
                    .append(e.getValue().stream().mapToDouble(r -> Double.parseDouble(r[4])).average().orElse(Double.NaN)).append(',')
                    .append(e.getValue().stream().mapToDouble(r -> Double.parseDouble(r[5])).average().orElse(Double.NaN)).append(System.lineSeparator());
            if (e.getKey() == controlN) control = new double[]{mean, std, times.length};
        }
        Files.writeString(out.resolve("summary.csv"), summary.toString());

        String band = control == null || control[2] < 2 ? "null"
                : "{\"n\": " + controlN + ", \"realizations\": " + (int) control[2] + ", \"mean_s\": " + control[0] + ", \"std_s\": " + control[1]
                + ", \"low_s\": " + (control[0] - 2 * control[1]) + ", \"high_s\": " + (control[0] + 2 * control[1]) + "}";
        StringBuilder meta = new StringBuilder("{\n\"protocol\": ").append(Files.readString(out.resolve("protocol.json")).strip())
                .append(",\n\"jar\": ").append(q(codeSource())).append(",\n\"band_2sigma\": ").append(band)
                .append(",\n\"control\": ").append(withCheck(lines(out.resolve("control.jsonl")), control))
                .append(",\n\"control_rechecks\": ").append(withCheck(lines(out.resolve("control_rechecks.jsonl")), control))
                .append(",\n\"sessions\": [\n").append(String.join(",\n", lines(out.resolve("sessions.jsonl")))).append("\n]\n}\n");
        Files.writeString(out.resolve("meta.json"), meta.toString());
    }

    /** Agrega within_2sigma a cada medición de control según la banda media ± 2σ de summary.csv (null si aún no hay banda). */
    private static String withCheck(List<String> controls, double[] band) {
        StringJoiner all = new StringJoiner(",\n  ", "[\n  ", "\n]");
        if (controls.isEmpty()) return "[]";
        for (String line : controls) {
            String value = "null";
            if (band != null && band[2] >= 2) {
                int at = line.indexOf("\"runtime_s\": ") + 13;
                double t = Double.parseDouble(line.substring(at, line.indexOf(',', at)));
                value = Boolean.toString(Math.abs(t - band[0]) <= 2 * band[1]);
            }
            all.add(line.substring(0, line.length() - 1) + ", \"within_2sigma\": " + value + "}");
        }
        return all.toString();
    }

    private static double std(double[] v, double mean) {
        if (v.length < 2) return Double.NaN;
        double s = 0;
        for (double x : v) s += (x - mean) * (x - mean);
        return Math.sqrt(s / (v.length - 1));
    }

    private static List<String[]> readRuns(Path file) throws IOException {
        List<String[]> rows = new ArrayList<>();
        for (String line : lines(file)) if (!line.startsWith("order,")) rows.add(line.split(","));
        return rows;
    }

    private static List<String> lines(Path file) throws IOException {
        if (!Files.exists(file)) return List.of();
        return Files.readAllLines(file).stream().filter(l -> !l.isBlank()).toList();
    }

    /** Agrega una línea y la fuerza a disco, para no perder corridas si se corta la luz o se mata el proceso. */
    private static void append(Path file, String line) throws IOException {
        try (FileOutputStream stream = new FileOutputStream(file.toFile(), true)) {
            stream.write((line + System.lineSeparator()).getBytes(StandardCharsets.UTF_8));
            stream.flush();
            stream.getFD().sync();
        }
    }

    private static String gitHead() {
        try {
            // --dirty marca si el código medido tiene cambios sin commit.
            Process p = new ProcessBuilder("git", "describe", "--always", "--dirty", "--abbrev=40").redirectErrorStream(true).start();
            String head = new String(p.getInputStream().readAllBytes(), StandardCharsets.UTF_8).strip();
            return p.waitFor() == 0 ? head : "desconocido";
        } catch (IOException e) { return "desconocido"; }
        catch (InterruptedException e) { Thread.currentThread().interrupt(); return "desconocido"; }
    }

    private static String codeSource() {
        try { return Path.of(RuntimeBenchmark.class.getProtectionDomain().getCodeSource().getLocation().toURI()).toString(); }
        catch (Exception e) { return "desconocido"; }
    }

    private static String q(String s) {
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
    }
}
