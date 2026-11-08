package ar.edu.itba.sds.tp5;

import ar.edu.itba.sds.tp5.calibration.GridSearch;
import ar.edu.itba.sds.tp5.data.EventParser;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.FreePedestrianCheck;
import ar.edu.itba.sds.tp5.engine.Integrator;
import ar.edu.itba.sds.tp5.engine.SfmParameters;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import ar.edu.itba.sds.tp5.engine.layer.LayerConstants;
import ar.edu.itba.sds.tp5.engine.layer.Layers;
import ar.edu.itba.sds.tp5.io.DirectionSeries;
import ar.edu.itba.sds.tp5.io.OutputFiles;
import ar.edu.itba.sds.tp5.metrics.Ecm;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

public final class Main {
    /** Frames del ajuste de la velocidad inicial (D12). */
    public static final int DEFAULT_V0_FRAMES = 5;
    /** Tope de la corrida extendida, en intervalos experimentales (unos 60 s). */
    public static final int EXTENDED_INTERVALS = 900;

    private static final Set<String> COMMON = Set.of("data", "dt-div", "v0-frames", "delta-a", "integrator", "rho", "frontal-deg", "f-tie", "f-horizon", "f-gate", "f-distance");

    private Main() { }

    public static void main(String[] args) {
        try { execute(args); }
        catch (IllegalArgumentException | IOException e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        }
    }

    public static void execute(String[] args) throws IOException {
        if (args.length == 0 || args[0].equals("--help")) {
            System.out.println("""
                    baseline [opciones] [--layer none|a|b|f --p1 X --p2 Y] [--out outputs/baseline]
                                 todos los eventos: evento_XX.txt y ecm.txt
                    run --event N [opciones] [--layer none|a|b|f --p1 X --p2 Y] [--out outputs/run] [--direction-series true]
                                 un solo evento; con --direction-series, también direccion_XX.txt (e_t y e_target)
                    grid --layer a|b|f --p1-values X,Y,... --p2-values X,Y,... --out archivo [opciones]
                                 una fila por par y evento, sin archivos de trayectoria
                    integrator-check
                                 errores de Verlet y Beeman contra el peatón libre analítico
                    Parámetros: A (p1 = t_a, p2 = l), B (p1 = t_a, p2 = k), F (p1 = A_p, p2 = B_p)
                    Opciones: [--data data] [--dt-div 64] [--v0-frames 5] [--delta-a 0.1] [--rho 0.9] [--f-tie metric|angular] [--frontal-deg 5] [--f-horizon Infinity] [--f-gate on|off] [--f-distance centers|edges] [--integrator beeman|verlet]
                    """);
            return;
        }
        switch (args[0]) {
            case "baseline" -> simulate(options(args, with("out", "layer", "p1", "p2", "direction-series")), null);
            case "run" -> {
                Map<String, String> o = options(args, with("event", "out", "layer", "p1", "p2", "direction-series"));
                if (!o.containsKey("event")) throw new IllegalArgumentException("run necesita --event");
                simulate(o, Integer.parseInt(o.get("event")));
            }
            case "grid" -> grid(options(args, with("layer", "p1-values", "p2-values", "out")));
            case "integrator-check" -> {
                options(args, Set.of());
                System.out.println("integrador dt_div error_posicion error_velocidad");
                for (Integrator integrator : Integrator.values())
                    for (int div : new int[] { 16, 32, 64, 128 }) {
                        FreePedestrianCheck.Errors e = FreePedestrianCheck.measure(integrator, div);
                        System.out.printf(Locale.ROOT, "%s %d %.3e %.3e%n", integrator, div, e.position(), e.velocity());
                    }
            }
            default -> throw new IllegalArgumentException("Comando desconocido: " + args[0]);
        }
    }

    private static Set<String> with(String... extra) {
        Set<String> allowed = new HashSet<>(COMMON);
        allowed.addAll(List.of(extra));
        return allowed;
    }

    private static int dtDiv(Map<String, String> o) { return Integer.parseInt(o.getOrDefault("dt-div", String.valueOf(Simulation.DEFAULT_DT_DIV))); }
    private static int v0Frames(Map<String, String> o) { return Integer.parseInt(o.getOrDefault("v0-frames", String.valueOf(DEFAULT_V0_FRAMES))); }
    private static double deltaA(Map<String, String> o) { return Double.parseDouble(o.getOrDefault("delta-a", String.valueOf(SfmParameters.DEFAULT_DELTA_A))); }
    private static LayerConstants constants(Map<String, String> o) {
        return LayerConstants.of(Double.parseDouble(o.getOrDefault("rho", String.valueOf(LayerConstants.DEFAULT_RHO))),
                Double.parseDouble(o.getOrDefault("frontal-deg", String.valueOf(LayerConstants.DEFAULT_FRONTAL_DEGREES))),
                switch (o.getOrDefault("f-tie", "metric")) {
                    case "metric" -> LayerConstants.FrontalTie.METRIC;
                    case "angular" -> LayerConstants.FrontalTie.ANGULAR;
                    default -> throw new IllegalArgumentException("--f-tie debe ser metric o angular: " + o.get("f-tie"));
                }).withFHorizon(Double.parseDouble(o.getOrDefault("f-horizon", "Infinity")))
                .withFVariant(switch (o.getOrDefault("f-gate", "on")) {
                    case "on" -> true;
                    case "off" -> false;
                    default -> throw new IllegalArgumentException("--f-gate debe ser on u off: " + o.get("f-gate"));
                }, switch (o.getOrDefault("f-distance", "centers")) {
                    case "centers" -> 0.0;
                    case "edges" -> 2 * SfmParameters.defaults().radius();
                    default -> throw new IllegalArgumentException("--f-distance debe ser centers o edges: " + o.get("f-distance"));
                });
    }
    private static Integrator integrator(Map<String, String> o) { return o.containsKey("integrator") ? Integrator.parse(o.get("integrator")) : Integrator.DEFAULT; }

    private static void simulate(Map<String, String> o, Integer onlyEvent) throws IOException {
        int dtDiv = dtDiv(o), v0Frames = v0Frames(o);
        double deltaA = deltaA(o);
        Integrator integrator = integrator(o);
        AvoidanceLayer layer = layer(o);
        Path out = Path.of(o.getOrDefault("out", onlyEvent == null ? "outputs/baseline" : "outputs/run"));
        Simulation sim = new Simulation(SfmParameters.withDeltaA(deltaA), integrator, dtDiv, layer);
        OutputFiles.RunInfo info = new OutputFiles.RunInfo(integrator.name(), dtDiv, v0Frames, deltaA, layer.label());

        List<OutputFiles.EventReport> reports = new ArrayList<>();
        for (PedestrianEvent e : EventParser.parse(Path.of(o.getOrDefault("data", "data")))) {
            if (onlyEvent != null && e.number() != onlyEvent) continue;
            OutputFiles.EventReport report = run(sim, e, v0Frames);
            OutputFiles.writeTrajectory(out.resolve(String.format("evento_%02d.txt", e.number())), e, report.sim(), info);
            if (Boolean.parseBoolean(o.getOrDefault("direction-series", "false")))
                DirectionSeries.write(out.resolve(String.format("direccion_%02d.txt", e.number())), e, sim, layer, v0Frames);
            reports.add(report);
        }
        if (reports.isEmpty()) throw new IllegalArgumentException("No existe el evento " + onlyEvent);
        OutputFiles.writeEcmReport(out.resolve("ecm.txt"), reports, info);
        System.out.println("Salida: " + out + " | eventos=" + reports.size() + " | " + integrator + " dt_exp/" + dtDiv + " | " + layer.label());
    }

    private static AvoidanceLayer layer(Map<String, String> o) {
        String name = o.getOrDefault("layer", "none");
        if (name.equalsIgnoreCase("none")) {
            if (o.containsKey("p1") || o.containsKey("p2")) throw new IllegalArgumentException("--p1 y --p2 necesitan --layer");
            return AvoidanceLayer.NONE;
        }
        if (!o.containsKey("p1") || !o.containsKey("p2")) throw new IllegalArgumentException("La capa necesita --p1 y --p2");
        return Layers.of(name, Double.parseDouble(o.get("p1")), Double.parseDouble(o.get("p2")), constants(o));
    }

    private static void grid(Map<String, String> o) throws IOException {
        for (String key : List.of("layer", "p1-values", "p2-values", "out"))
            if (!o.containsKey(key)) throw new IllegalArgumentException("grid necesita --" + key);
        double[] p1 = values(o.get("p1-values")), p2 = values(o.get("p2-values"));
        String layer = o.get("layer");
        List<GridSearch.Row> rows = GridSearch.run(layer, p1, p2, EventParser.parse(Path.of(o.getOrDefault("data", "data"))),
                SfmParameters.withDeltaA(deltaA(o)), constants(o), integrator(o), dtDiv(o), v0Frames(o));
        GridSearch.write(Path.of(o.get("out")), layer, rows);
        System.out.println("Grilla: " + o.get("out") + " | capa=" + layer + " | pares=" + p1.length * p2.length);
    }

    private static double[] values(String text) {
        return Arrays.stream(text.split(",")).mapToDouble(s -> Double.parseDouble(s.trim())).toArray();
    }

    /** Corre el evento en su ventana y, si alguien no llegó, hasta el tope para saber cuándo llegaría. */
    public static OutputFiles.EventReport run(Simulation sim, PedestrianEvent e, int v0Frames) {
        Agent[] agents = { Agent.from(e, 0, v0Frames), Agent.from(e, 1, v0Frames) };
        Simulation.Result result = sim.run(agents, e.dtExp(), e.windowIntervals());
        double[] extended = result.arrival().clone();
        if (Double.isNaN(extended[0]) || Double.isNaN(extended[1]))
            extended = sim.run(agents, e.dtExp(), EXTENDED_INTERVALS).arrival();
        return new OutputFiles.EventReport(e, result, Ecm.of(e, result), extended);
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
}
