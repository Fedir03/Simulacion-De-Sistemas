package ar.edu.itba.sds.tp4;

import ar.edu.itba.sds.tp4.engine.oscillator.IntegrationOptions;
import ar.edu.itba.sds.tp4.engine.oscillator.IntegrationOptions.AccelerationUpdate;
import ar.edu.itba.sds.tp4.engine.oscillator.IntegrationOptions.PredictedVelocity;
import ar.edu.itba.sds.tp4.engine.oscillator.IntegrationOptions.VerletVelocity;
import ar.edu.itba.sds.tp4.engine.oscillator.OscillatorStudy;
import ar.edu.itba.sds.tp4.engine.oscillator.Scheme;
import ar.edu.itba.sds.tp4.io.OscillatorFiles;
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
                    """);
            return;
        }
        Set<String> common = Set.of("mass", "k", "gamma", "amplitude", "tf", "verlet-velocity", "vv-velocity", "acceleration-update", "out");
        Set<String> specific = switch (args[0]) {
            case "oscillator-ecm" -> Set.of("dt-min", "dt-max", "count", "dts");
            case "oscillator-trajectory" -> Set.of("dt");
            default -> throw new IllegalArgumentException("Comando desconocido: " + args[0]);
        };
        Map<String, String> options = new HashMap<>();
        for (int i = 1; i < args.length; i += 2) {
            if (!args[i].startsWith("--") || i + 1 >= args.length) throw new IllegalArgumentException("Se esperaba --opción valor");
            String key = args[i].substring(2);
            if (!common.contains(key) && !specific.contains(key) || options.put(key, args[i + 1]) != null)
                throw new IllegalArgumentException("Opción inválida o repetida: " + key);
        }
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
