package ar.edu.itba.sds.tp3;

import ar.edu.itba.sds.tp3.engine.*;
import ar.edu.itba.sds.tp3.engine.obstacles.ObstacleGenerators;
import ar.edu.itba.sds.tp3.io.StageFile;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.io.*;
import java.nio.file.*;
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
                    generate [--n 100] [--seed 42] [--out archivo.txt] [--obstacles-out config.txt]
                             [--obstacle-algorithm random|none|single|funnel|semicircle|posts]
                               random:     [--obstacle-count 2] [--obstacle-radius 0.05] [--obstacle-seed <seed>]
                               single:     [--obstacle-x L/2] [--obstacle-y W/2] [--obstacle-radius 0.1]
                               funnel:     [--obstacle-funnel-length 0.3] [--obstacle-max-radius ∞] [--obstacle-grid 0.001]
                               semicircle: [--obstacle-free-radius 0.36] [--obstacle-goals right|both]
                                           [--obstacle-max-radius ∞] [--obstacle-grid 0.001]
                               posts:      [--obstacle-radius 0.05]
                             [--obstacles archivo.txt (con --obstacle-algorithm, el algoritmo agrega obstáculos a los del archivo)]
                             [--length 1.2] [--width 0.68] [--goal-width 0.2]
                             [--radius 0.0175] [--mass 0.025] [--speed 1.0]
                    simulate --input archivo.txt [--time 30] [--every 1 | --dt 0.01] [--out archivo.txt]
                             --dt escribe estados exactos cada dt segundos en vez de cada --every eventos
                    Salidas predeterminadas: TP3/generated/initial.txt y TP3/generated/simulation.txt
                    """);
            return;
        }
        Set<String> allowed = switch (args[0]) {
            case "generate" -> Set.of("n", "seed", "obstacles", "out", "obstacles-out", "length", "width", "goal-width", "radius", "mass", "speed",
                    "obstacle-algorithm", "obstacle-count", "obstacle-radius", "obstacle-seed", "obstacle-x", "obstacle-y",
                    "obstacle-funnel-length", "obstacle-free-radius", "obstacle-goals", "obstacle-max-radius", "obstacle-grid");
            case "simulate" -> Set.of("input", "time", "every", "dt", "out");
            default -> throw new IllegalArgumentException("Comando desconocido: " + args[0]);
        };
        Map<String, String> options = new HashMap<>();
        for (int i = 1; i < args.length; i += 2) {
            if (!args[i].startsWith("--") || i + 1 >= args.length) throw new IllegalArgumentException("Se esperaba --opción valor");
            String key = args[i].substring(2);
            if (!allowed.contains(key) || options.put(key, args[i + 1]) != null) throw new IllegalArgumentException("Opción inválida o repetida: " + key);
        }
        if (args[0].equals("generate")) {
            SimulationConfig c = new SimulationConfig(value(options, "length", "1.2"), value(options, "width", "0.68"),
                    value(options, "goal-width", "0.2"), value(options, "radius", "0.0175"), value(options, "mass", "0.025"), value(options, "speed", "1"));
            long seed = Long.parseLong(options.getOrDefault("seed", "42"));
            boolean generatorOptions = options.keySet().stream().anyMatch(key -> key.startsWith("obstacle-"));
            boolean fromFile = options.containsKey("obstacles"), withAlgorithm = !fromFile || options.containsKey("obstacle-algorithm");
            if (fromFile && generatorOptions && !withAlgorithm)
                throw new IllegalArgumentException("Para combinar --obstacles con opciones --obstacle-*, indicar --obstacle-algorithm");
            String algorithm = options.getOrDefault("obstacle-algorithm", "random");
            Map<String, String> params = new HashMap<>();
            options.forEach((key, v) -> { if (key.startsWith("obstacle-") && !key.equals("obstacle-algorithm")) params.put(key.substring(9), v); });
            // Los obstáculos del archivo son la base; el algoritmo, si se indica, agrega obstáculos respetándolos.
            List<Obstacle> obstacles = new ArrayList<>(fromFile ? StageFile.readObstacles(Path.of(options.get("obstacles"))) : List.of());
            if (withAlgorithm) obstacles.addAll(ObstacleGenerators.create(algorithm, params)
                    .generate(c, Long.parseLong(options.getOrDefault("obstacle-seed", Long.toString(seed))), List.copyOf(obstacles)));
            var stage = StageGeneration.generate(c, Integer.parseInt(options.getOrDefault("n", "100")),
                    seed, obstacles);
            Path out = output(options, "initial.txt");
            StageFile.write(out, stage);
            System.out.println("Condición inicial: " + out + " | K=" + obstacles.size());
            if (options.containsKey("obstacles-out")) {
                Path config = Path.of(options.get("obstacles-out"));
                StageFile.writeObstacles(config, obstacles);
                System.out.println("Obstáculos: " + config);
            }
        } else {
            if (!options.containsKey("input")) throw new IllegalArgumentException("Falta --input");
            Path input = Path.of(options.get("input")), out = output(options, "simulation.txt");
            if (input.toAbsolutePath().normalize().equals(out.toAbsolutePath().normalize())
                    || Files.exists(out) && Files.isSameFile(input, out)) throw new IllegalArgumentException("Entrada y salida deben ser distintas");
            double endTime = value(options, "time", "30");
            int every = Integer.parseInt(options.getOrDefault("every", "1"));
            double dt = value(options, "dt", "0");
            if (!Double.isFinite(endTime) || endTime < 0 || every <= 0) throw new IllegalArgumentException("Tiempo o frecuencia inválidos");
            if (options.containsKey("dt") && (options.containsKey("every") || !(dt > 0)))
                throw new IllegalArgumentException("--dt debe ser positivo y excluye --every");
            var stage = StageFile.read(input);
            try (BufferedWriter w = StageFile.writer(out)) {
                StageFile.header(w, stage);
                long start = System.nanoTime();
                var result = new CollisionSimulator(stage).run(endTime, every, dt,
                        (t, e, g, p) -> StageFile.frame(w, t, e, g, p));
                // Tiempo de ejecución del ciclo de eventos, escritura incluida; excluye arranque de la JVM y lectura.
                double runtime = (System.nanoTime() - start) / 1e9;
                w.write("# tf=" + result.time() + (dt > 0 ? " outputInterval=" + dt : " outputEvery=" + every) + " events=" + result.events() + " Ng=" + result.goals()
                        + " t90=" + result.t90() + " runtime=" + runtime);
                w.newLine();
                System.out.println("Trayectoria: " + out + " | eventos=" + result.events() + " goles=" + result.goals()
                        + " t90=" + result.t90() + " runtime=" + runtime + "s");
            }
        }
    }
    private static double value(Map<String, String> options, String key, String fallback) {
        return Double.parseDouble(options.getOrDefault(key, fallback));
    }
    private static Path output(Map<String, String> options, String name) {
        if (options.containsKey("out")) return Path.of(options.get("out"));
        // Independiente del cwd: ubica el módulo desde target/classes o desde su JAR.
        try {
            Path code = Path.of(Main.class.getProtectionDomain().getCodeSource().getLocation().toURI());
            Path base = Files.isDirectory(code) ? code : code.getParent();
            while (base != null) {
                if (Files.isDirectory(base.resolve("enunciado")) && Files.exists(base.resolve("pom.xml")))
                    return base.resolve("generated").resolve(name);
                base = base.getParent();
            }
        } catch (java.net.URISyntaxException e) { throw new IllegalStateException(e); }
        throw new IllegalArgumentException("No se pudo ubicar TP3; indicar --out");
    }
}
