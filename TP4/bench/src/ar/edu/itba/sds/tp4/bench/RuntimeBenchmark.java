package ar.edu.itba.sds.tp4.bench;

import ar.edu.itba.sds.tp4.engine.billiard.BilliardSimulator.Status;
import java.io.*;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.time.ZonedDateTime;
import java.util.*;

/**
 * Tiempo de ejecución vs N en una sola JVM calentada y reutilizada (D12), por rondas. Adaptado del RuntimeBenchmark de TP3:
 * 1. Heap fijo: exige -Xms igual a -Xmx (TP3 y TP4 con -Xms2g -Xmx2g).
 * 2. Calentamiento descartado: para cada par N:tf de --warmup repite (N, warmup-seed, tf) hasta que dos corridas
 *    consecutivas difieran menos de warmup-tol, con un máximo de warmup-max. Se repite en cada reanudación.
 * 3. Medición: la ronda r usa la semilla r y recorre los N en el orden de Collections.shuffle con un Random(order-seed)
 *    compartido entre rondas, así el orden de la ronda r no depende de --rounds. System.gc() antes de cada corrida y una
 *    fila en runs.csv con flush y sync después de cerrar su observables.txt. Al reanudar se saltean los pares (N, semilla)
 *    ya medidos; --batch k corta después de k corridas.
 * Sin control propio: el control de máquina es el de TP3 (scripts/sim_gen/control_tp3.sh antes y después de la tanda).
 */
public final class RuntimeBenchmark {
    private RuntimeBenchmark() { }
    private static final String RUNS_HEADER = "round,position,n,seed,runtime_s,steps,status,used_final,session,finished_at,finished_at_local";
    private static final Set<String> OPTIONS = Set.of("out", "ns", "rounds", "tf", "order-seed", "batch", "warmup",
            "warmup-tol", "warmup-max", "warmup-seed");

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
        for (String key : List.of("out", "ns", "rounds", "warmup"))
            if (!options.containsKey(key))
                throw new IllegalArgumentException("Falta --" + key + " (uso: --out DIR --ns 100,200 --rounds 10 --warmup 300:1,600:0.5)");
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
        int rounds = Integer.parseInt(options.get("rounds"));
        double tf = Double.parseDouble(options.getOrDefault("tf", "30"));
        long orderSeed = Long.parseLong(options.getOrDefault("order-seed", "20261022"));
        int batch = Integer.parseInt(options.getOrDefault("batch", Integer.toString(Integer.MAX_VALUE)));
        double warmupTol = Double.parseDouble(options.getOrDefault("warmup-tol", "0.05"));
        int warmupMax = Integer.parseInt(options.getOrDefault("warmup-max", "30"));
        long warmupSeed = Long.parseLong(options.getOrDefault("warmup-seed", "1000"));
        if (ns.length == 0 || Arrays.stream(ns).distinct().count() != ns.length || rounds < 1 || batch < 1 || warmupMax < 2
                || !(tf > 0) || !(warmupTol > 0))
            throw new IllegalArgumentException("Parámetros inválidos (N repetidos, rondas, batch, tf o calentamiento)");

        // Sin rounds ni batch: se pueden agregar rondas o cortar en tandas sin cambiar el protocolo
        String protocol = "{\"case\": " + c.describeJson() + ", \"ns\": " + Arrays.toString(ns) + ", \"tf\": " + tf
                + ", \"rounds\": \"la ronda r usa la semilla r; orden de los N: Collections.shuffle con un Random(order_seed) compartido entre rondas\""
                + ", \"order_seed\": " + orderSeed + ", \"warmup\": {\"ns\": " + Arrays.toString(warmupNs) + ", \"tf\": " + Arrays.toString(warmupTfs)
                + ", \"seed\": " + warmupSeed + ", \"tolerance\": " + warmupTol + ", \"max_reps\": " + warmupMax + "}"
                + ", \"heap\": " + q(heap) + ", \"gc_before_each_run\": true"
                + ", \"timer\": \"System.nanoTime alrededor de BilliardSimulator.run, con observables.txt escrito (como Main billiard)\"}";
        Files.createDirectories(out);
        Path protocolFile = out.resolve("protocol.json"), runsFile = out.resolve("runs.csv"), sessionsFile = out.resolve("sessions.jsonl");
        if (Files.exists(protocolFile)) {
            if (!Files.readString(protocolFile).strip().equals(protocol))
                throw new IllegalArgumentException("La carpeta tiene otro protocolo (" + protocolFile + "); usar otra --out o los mismos parámetros");
        } else Files.writeString(protocolFile, protocol + System.lineSeparator());

        // Orden determinista: al reanudar se recorre la misma lista y se saltean los pares ya medidos.
        List<int[]> order = new ArrayList<>(); // {ronda, posición, N}
        Random random = new Random(orderSeed);
        for (int r = 1; r <= rounds; r++) {
            List<Integer> round = new ArrayList<>();
            for (int n : ns) round.add(n);
            Collections.shuffle(round, random);
            for (int p = 0; p < round.size(); p++) order.add(new int[]{r, p, round.get(p)});
        }
        Set<String> done = new HashSet<>();
        for (String[] row : readRuns(runsFile)) done.add(row[2] + "," + row[3]);
        int session = (int) lines(sessionsFile).stream().filter(l -> l.contains("\"event\": \"start\"")).count() + 1;

        // Antes del calentamiento: lanza procesos (git, java -version) que no tienen que caer entre corridas medidas
        String environment = environment();
        long already = order.stream().filter(o -> done.contains(o[2] + "," + o[0])).count();
        System.err.printf(Locale.ROOT, "Sesión %d | heap %s | chequeo de máquina: %s | %d/%d corridas hechas%n",
                session, heap, machineCheck(), already, order.size());
        String warmup = warmup(c, out.resolve("warmup"), warmupNs, warmupTfs, warmupSeed, warmupTol, warmupMax);
        append(sessionsFile, "{\"session\": " + session + ", \"event\": \"start\", \"command\": " + q(String.join(" ", originalArgs))
                + ", \"rounds\": " + rounds + ", \"batch\": " + (batch == Integer.MAX_VALUE ? "null" : batch)
                + ", \"environment\": " + environment + ", \"warmup\": " + warmup + "}");
        if (!Files.exists(runsFile)) append(runsFile, RUNS_HEADER);

        int ran = 0;
        for (int[] o : order) {
            if (ran >= batch) break;
            int round = o[0], position = o[1], n = o[2];
            long seed = round;
            if (done.contains(n + "," + seed)) continue;
            Path dir = out.resolve("runs").resolve("n" + n + "_s" + seed);
            TimedCase.RunResult r = timed(c, n, seed, tf, dir);
            if (r.status() != Status.COMPLETED) {
                append(sessionsFile, "{\"session\": " + session + ", \"event\": \"abort\", \"at\": " + q(Instant.now().toString())
                        + ", \"n\": " + n + ", \"seed\": " + seed + ", \"status\": " + q(r.status().name()) + "}");
                writeMeta(out, environment, order.size(), done.size());
                throw new IllegalStateException("N=" + n + " semilla=" + seed + " terminó con estado " + r.status() + " en el paso " + r.steps()
                        + "; no se registra (ver " + dir.resolve("observables.txt") + ")");
            }
            ZonedDateTime now = ZonedDateTime.now();
            append(runsFile, round + "," + position + "," + n + "," + seed + "," + r.runtimeSeconds() + "," + r.steps() + ","
                    + r.status().name().toLowerCase(Locale.ROOT) + "," + r.usedCount() + "," + session + "," + now.toInstant() + "," + now.toOffsetDateTime());
            done.add(n + "," + seed);
            ran++;
            System.err.printf(Locale.ROOT, "[%d/%d] ronda %d, posición %d: N=%d semilla=%d: %.3f s, %d pasos (%.2f µs/paso)%n", done.size(), order.size(),
                    round, position, n, seed, r.runtimeSeconds(), r.steps(), 1e6 * r.runtimeSeconds() / r.steps());
            writeMeta(out, environment, order.size(), done.size());
        }
        long measured = order.stream().filter(o -> done.contains(o[2] + "," + o[0])).count();
        boolean complete = measured == order.size();
        append(sessionsFile, "{\"session\": " + session + ", \"event\": \"end\", \"at\": " + q(Instant.now().toString())
                + ", \"runs\": " + ran + ", \"complete\": " + complete + "}");
        writeMeta(out, environment, order.size(), measured);
        System.err.println(complete ? "Medición completa: " + out : "Faltan " + (order.size() - measured) + " corridas; reanudar con el mismo comando");
    }

    /** Exige -Xms y -Xmx presentes e iguales; devuelve el valor. */
    private static String fixedHeap() {
        String xms = null, xmx = null;
        for (String a : ManagementFactory.getRuntimeMXBean().getInputArguments()) {
            if (a.startsWith("-Xms")) xms = a.substring(4).toLowerCase(Locale.ROOT);
            if (a.startsWith("-Xmx")) xmx = a.substring(4).toLowerCase(Locale.ROOT);
        }
        if (xms == null || xmx == null || !xms.equals(xmx))
            throw new IllegalArgumentException("Heap fijo requerido: correr con -Xms y -Xmx iguales (D12: -Xms2g -Xmx2g); recibido -Xms=" + xms + " -Xmx=" + xmx);
        return "-Xms" + xms + " -Xmx" + xmx;
    }

    private static TimedCase.RunResult timed(TimedCase c, int n, long seed, double tf, Path dir) throws IOException {
        c.prepare(n, seed, tf, dir);
        System.gc();
        return c.runTimed();
    }

    private static String warmup(TimedCase c, Path dir, int[] ns, double[] tfs, long seed, double tol, int max) throws IOException {
        StringJoiner blocks = new StringJoiner(", ", "[", "]");
        for (int w = 0; w < ns.length; w++) {
            int n = ns[w];
            double tf = tfs[w];
            List<Double> times = new ArrayList<>();
            boolean converged = false;
            while (times.size() < max && !converged) {
                times.add(timed(c, n, seed, tf, dir).runtimeSeconds());
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

    private static void writeMeta(Path out, String environment, long planned, long measured) throws IOException {
        String meta = "{\n\"protocol\": " + Files.readString(out.resolve("protocol.json")).strip()
                + ",\n\"runs_planned\": " + planned + ",\n\"runs_measured\": " + measured
                + ",\n\"environment\": " + environment
                + ",\n\"sessions\": [\n" + String.join(",\n", lines(out.resolve("sessions.jsonl"))) + "\n]\n}\n";
        Files.writeString(out.resolve("meta.json"), meta);
    }

    /** Compilación (build-info.properties), git al correr, JVM, máquina y chequeo de máquina, con fecha local y UTC. */
    private static String environment() {
        ZonedDateTime now = ZonedDateTime.now();
        String status = command("git", "status", "--porcelain");
        var os = ManagementFactory.getOperatingSystemMXBean();
        long ram = os instanceof com.sun.management.OperatingSystemMXBean sun ? sun.getTotalMemorySize() : -1;
        String java = Path.of(System.getProperty("java.home"), "bin", "java").toString();
        String reference = System.getProperty("bench.machine_reference");
        return "{\"at_utc\": " + q(now.toInstant().toString()) + ", \"at_local\": " + q(now.toOffsetDateTime().toString())
                + ", \"zone\": " + q(now.getZone().getId())
                + ", \"build\": " + json(buildInfo())
                + ", \"git_at_run\": {\"head\": " + q(command("git", "rev-parse", "HEAD")) + ", \"branch\": " + q(command("git", "rev-parse", "--abbrev-ref", "HEAD"))
                + ", \"dirty\": " + (status == null ? "null" : !status.isEmpty()) + ", \"status_porcelain\": " + q(status) + "}"
                + ", \"jvm\": {\"args\": " + q(String.join(" ", ManagementFactory.getRuntimeMXBean().getInputArguments()))
                + ", \"java_home\": " + q(System.getProperty("java.home")) + ", \"java\": " + q(System.getProperty("java.vendor") + " " + System.getProperty("java.version"))
                + ", \"java_version_output\": " + q(command(java, "-version")) + "}"
                + ", \"machine\": {\"hostname\": " + q(command("hostname")) + ", \"computername\": " + q(System.getenv("COMPUTERNAME"))
                + ", \"processor_identifier\": " + q(System.getenv("PROCESSOR_IDENTIFIER")) + ", \"os\": " + q(System.getProperty("os.name") + " " + System.getProperty("os.version"))
                + ", \"arch\": " + q(System.getProperty("os.arch")) + ", \"processors\": " + Runtime.getRuntime().availableProcessors() + ", \"ram_bytes\": " + ram + "}"
                + ", \"machine_check\": {\"result\": " + q(machineCheck()) + ", \"reference_file\": " + q(reference)
                + ", \"reference\": " + json(load(reference)) + "}}";
    }

    private static String machineCheck() { return System.getProperty("bench.machine_check", "sin chequeo (no se lanzó con runtime_tp4.sh)"); }

    /** build-info.properties de build_runtime_tp4.sh, en la raíz de las clases del bench. */
    private static Properties buildInfo() {
        Properties p = new Properties();
        try (InputStream in = RuntimeBenchmark.class.getResourceAsStream("/build-info.properties")) {
            if (in == null) p.setProperty("error", "build-info.properties no está en el classpath");
            else p.load(new InputStreamReader(in, StandardCharsets.UTF_8));
        } catch (IOException e) { p.setProperty("error", e.getMessage()); }
        return p;
    }

    private static Properties load(String file) {
        Properties p = new Properties();
        if (file == null) return p;
        try (Reader in = Files.newBufferedReader(Path.of(file), StandardCharsets.UTF_8)) { p.load(in); }
        catch (IOException e) { p.setProperty("error", "no se pudo leer: " + e.getMessage()); }
        return p;
    }

    private static String json(Properties p) {
        StringJoiner all = new StringJoiner(", ", "{", "}");
        for (String key : new TreeSet<>(p.stringPropertyNames())) all.add(q(key) + ": " + q(p.getProperty(key)));
        return all.toString();
    }

    /** Salida (stdout y stderr) del comando sin espacios al borde, o null si falla. */
    private static String command(String... cmd) {
        try {
            Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
            String output = new String(p.getInputStream().readAllBytes(), StandardCharsets.UTF_8).strip();
            return p.waitFor() == 0 ? output : null;
        } catch (IOException e) { return null; }
        catch (InterruptedException e) { Thread.currentThread().interrupt(); return null; }
    }

    private static List<String[]> readRuns(Path file) throws IOException {
        List<String[]> rows = new ArrayList<>();
        for (String line : lines(file)) if (!line.startsWith("round,")) rows.add(line.split(","));
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

    private static String q(String s) {
        if (s == null) return "null";
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t") + "\"";
    }
}
