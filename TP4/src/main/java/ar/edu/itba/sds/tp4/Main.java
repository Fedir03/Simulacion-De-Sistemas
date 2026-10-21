package ar.edu.itba.sds.tp4;

import ar.edu.itba.sds.tp4.engine.GridCapacity;
import ar.edu.itba.sds.tp4.engine.billiard.BilliardSimulator;
import ar.edu.itba.sds.tp4.engine.cim.CellIndexMethod;
import ar.edu.itba.sds.tp4.engine.oscillator.IntegrationOptions;
import ar.edu.itba.sds.tp4.engine.oscillator.IntegrationOptions.AccelerationUpdate;
import ar.edu.itba.sds.tp4.engine.oscillator.IntegrationOptions.PredictedVelocity;
import ar.edu.itba.sds.tp4.engine.oscillator.IntegrationOptions.VerletVelocity;
import ar.edu.itba.sds.tp4.engine.oscillator.OscillatorStudy;
import ar.edu.itba.sds.tp4.engine.oscillator.Scheme;
import ar.edu.itba.sds.tp4.io.BilliardFiles;
import ar.edu.itba.sds.tp4.io.OscillatorFiles;
import ar.edu.itba.sds.tp4.models.BilliardConfig;
import ar.edu.itba.sds.tp4.models.Oscillator;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

public final class Main {
    private Main() { }
    public static void main(String[] args) {
        try { execute(args); }
        catch (IllegalArgumentException | IOException e) {
            System.err.println("Error: " + e.getMessage()); System.exit(1);
        }
    }
    public static void execute(String[] args) throws IOException {
        if (args.length == 0 || args[0].equals("--help")) {
            System.out.println("""
                    oscillator-ecm [--dt-min 1e-6] [--dt-max 5e-3] [--count 13] [--dts 1e-3,1e-4,...] [--out archivo.txt]
                                   ECM(dt) de los 4 esquemas contra la solución analítica; --dts reemplaza al barrido logarítmico
                    oscillator-trajectory [--dt 1e-3] [--out archivo.txt]
                                   x(t) analítica y de los 4 esquemas
                    Opciones comunes del oscilador:
                      [--mass 70] [--k 1e4] [--gamma 100] [--amplitude 1] [--tf 5]
                      [--verlet-velocity backward|euler]          v(t) para f(t) en Verlet original
                      [--vv-velocity euler|half-step]             v predicha para f(t+dt) en Velocity Verlet
                      [--acceleration-update predicted|corrected] a(t+dt) que Beeman y Velocity Verlet pasan al paso siguiente
                    Salidas predeterminadas: TP4/outputs/sistema1/ecm.txt y TP4/outputs/sistema1/trajectory.txt
                    grid-nmax      N máx colocable con la grilla (cuadrada/hex, 2 anclajes, separaciones extra), sin obstáculos y con x0=r
                    billiard [--n 100] [--seed 1] [--x0 0.0175|none] [--dt 1e-4] [--dt2 0.04] [--tf 30]
                             [--until tf|t100] [--dynamic no|yes] [--out carpeta]
                                   Sistema 2 (Verlet, CIM). Escribe observables.txt (t E_tot E_cin E_el Nu) cada dt2 y,
                                   con --dynamic yes, dynamic.txt (id x y vx vy used). dt2 debe ser múltiplo de dt y tf de dt2.
                                   --until t100 corta en el primer cuadro con todas las partículas usadas.
                                   Salida predeterminada: TP4/outputs/sistema2/
                    """);
            return;
        }
        if (args[0].equals("grid-nmax")) {
            if (args.length > 1) throw new IllegalArgumentException("grid-nmax no recibe opciones");
            GridCapacity.report(System.out);
            return;
        }
        if (args[0].equals("billiard")) {
            billiard(options(args, Set.of("n", "seed", "x0", "dt", "dt2", "tf", "until", "dynamic", "out")));
            return;
        }
        Set<String> common = Set.of("mass", "k", "gamma", "amplitude", "tf", "verlet-velocity", "vv-velocity", "acceleration-update", "out");
        Set<String> specific = switch (args[0]) {
            case "oscillator-ecm" -> Set.of("dt-min", "dt-max", "count", "dts");
            case "oscillator-trajectory" -> Set.of("dt");
            default -> throw new IllegalArgumentException("Comando desconocido: " + args[0]);
        };
        Set<String> allowed = new HashSet<>(common);
        allowed.addAll(specific);
        Map<String, String> options = options(args, allowed);
        Oscillator defaults = Oscillator.defaults();
        Oscillator o = new Oscillator(value(options, "mass", defaults.mass()), value(options, "k", defaults.k()),
                value(options, "gamma", defaults.gamma()), value(options, "amplitude", defaults.amplitude()), value(options, "tf", defaults.finalTime()));
        IntegrationOptions d = IntegrationOptions.defaults();
        IntegrationOptions opt = new IntegrationOptions(
                enumValue(options, "verlet-velocity", VerletVelocity.class, d.verletVelocity()),
                enumValue(options, "vv-velocity", PredictedVelocity.class, d.velocityVerletPrediction()),
                enumValue(options, "acceleration-update", AccelerationUpdate.class, d.accelerationUpdate()));

        if (args[0].equals("oscillator-ecm")) {
            double[] dts = options.containsKey("dts")
                    ? Arrays.stream(options.get("dts").split(",")).mapToDouble(s -> Double.parseDouble(s.trim())).toArray()
                    : OscillatorStudy.logSpaced(value(options, "dt-min", 1e-6), value(options, "dt-max", 5e-3),
                    Integer.parseInt(options.getOrDefault("count", "13")));
            List<OscillatorStudy.Result> results = new ArrayList<>();
            for (Scheme s : Scheme.values())
                for (double dt : dts) results.add(OscillatorStudy.run(o, s, dt, opt));
            Path out = output(options, "sistema1/ecm.txt");
            OscillatorFiles.writeEcm(out, o, opt, results);
            System.out.println("ECM: " + out + " | " + dts.length + " dt × " + Scheme.values().length + " esquemas");
        } else {
            double dt = value(options, "dt", 1e-3);
            int steps = OscillatorStudy.steps(o, dt);
            double[][] x = new double[Scheme.values().length][];
            for (Scheme s : Scheme.values()) x[s.ordinal()] = s.integrate(o, dt, steps, opt);
            Path out = output(options, "sistema1/trajectory.txt");
            OscillatorFiles.writeTrajectory(out, o, opt, dt, steps, x);
            System.out.println("Trayectoria: " + out + " | pasos=" + steps);
        }
    }
    private static void billiard(Map<String, String> options) throws IOException {
        String x0 = options.getOrDefault("x0", "0.0175");
        BilliardConfig c = BilliardConfig.of(Integer.parseInt(options.getOrDefault("n", "100")),
                Long.parseLong(options.getOrDefault("seed", "1")),
                x0.equals("none") ? BilliardConfig.NO_OBSTACLES : Double.parseDouble(x0),
                value(options, "dt", 1e-4), value(options, "dt2", 0.04), value(options, "tf", 30));
        boolean untilT100 = choice(options, "until", "tf", "t100").equals("t100");
        boolean dynamic = choice(options, "dynamic", "no", "yes").equals("yes");
        int m = CellIndexMethod.maxValidM(2 * c.domainRadius(), 0, c.radius());
        Path dir = output(options, "sistema2");
        BilliardSimulator sim = BilliardSimulator.fromGrid(c, CellIndexMethod.forCircle(m, c.domainRadius()));
        try (BilliardFiles files = new BilliardFiles(dir, c, "cim M=" + m, dynamic)) {
            // Tiempo de ejecución (D11): solo la simulación con su escritura; sin arranque de la JVM ni colocación
            long start = System.nanoTime();
            BilliardSimulator.Summary s = sim.run(files, untilT100);
            double runtime = (System.nanoTime() - start) / 1e9;
            files.footer(s, runtime);
            System.out.println("Billar: " + dir + " | estado=" + s.status() + " t=" + s.time() + " Nu=" + s.usedCount()
                    + "/" + c.n() + " runtime=" + runtime + "s");
        }
    }
    private static String choice(Map<String, String> options, String key, String fallback, String other) {
        String v = options.getOrDefault(key, fallback);
        if (!v.equals(fallback) && !v.equals(other))
            throw new IllegalArgumentException("--" + key + " debe ser " + fallback + " o " + other + ": " + v);
        return v;
    }
    private static Map<String, String> options(String[] args, Set<String> allowed) {
        Map<String, String> options = new HashMap<>();
        for (int i = 1; i < args.length; i += 2) {
            if (!args[i].startsWith("--") || i + 1 >= args.length) throw new IllegalArgumentException("Se esperaba --opción valor");
            String key = args[i].substring(2);
            if (!allowed.contains(key) || options.put(key, args[i + 1]) != null)
                throw new IllegalArgumentException("Opción inválida o repetida: " + key);
        }
        return options;
    }
    private static double value(Map<String, String> options, String key, double fallback) {
        return options.containsKey(key) ? Double.parseDouble(options.get(key)) : fallback;
    }
    private static <E extends Enum<E>> E enumValue(Map<String, String> options, String key, Class<E> type, E fallback) {
        return options.containsKey(key) ? IntegrationOptions.parse(type, options.get(key)) : fallback;
    }
    private static Path output(Map<String, String> options, String name) {
        if (options.containsKey("out")) return Path.of(options.get("out"));
        // Independiente del cwd: ubica el módulo desde target/classes o desde su JAR.
        try {
            Path code = Path.of(Main.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            Path base = Files.isDirectory(code) ? code : code.getParent();
            while (base != null) {
                if (Files.isDirectory(base.resolve("src").resolve("main")) && Files.exists(base.resolve("pom.xml")))
                    return base.resolve("outputs").resolve(name);
                base = base.getParent();
            }
        } catch (java.net.URISyntaxException e) { throw new IllegalStateException(e); }
        throw new IllegalArgumentException("No se pudo ubicar TP4; indicar --out");
    }
}
