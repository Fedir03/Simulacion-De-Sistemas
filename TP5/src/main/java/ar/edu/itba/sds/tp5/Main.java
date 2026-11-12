package ar.edu.itba.sds.tp5;

import ar.edu.itba.sds.tp5.data.EventParser;
import ar.edu.itba.sds.tp5.data.FrontalTrim;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.FreePedestrianCheck;
import ar.edu.itba.sds.tp5.engine.Integrator;
import ar.edu.itba.sds.tp5.engine.SfmParameters;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import ar.edu.itba.sds.tp5.engine.layer.LayerConstants;
import ar.edu.itba.sds.tp5.engine.layer.Layers;
import ar.edu.itba.sds.tp5.io.OutputFiles;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * Motor de la entrega: simula cada evento y escribe su trayectoria (evento_XX.txt). No calcula observables: ECM,
 * distancia mínima, contactos y calibración están en el paquete analysis (ar.edu.itba.sds.tp5.analysis.AnalysisMain),
 * que no va al ZIP. Las opciones y la corrida de un evento son públicas para que el análisis las use igual.
 */
public final class Main {
    /** Frames del ajuste de la velocidad inicial (D12). */
    public static final int DEFAULT_V0_FRAMES = 5;
    /** Tope de la corrida extendida, en intervalos experimentales (unos 60 s). */
    public static final int EXTENDED_INTERVALS = 900;

    private static final Set<String> COMMON = Set.of("data", "dt-div", "v0-frames", "delta-a", "integrator", "rho", "frontal-deg", "f-tie", "f-horizon", "f-gate", "f-distance",
            "trim", "trim-deg", "trim-persist", "trim-half", "trim-target", "trim-shared", "trim-shared-x");

    /** Opciones comunes, para el texto de ayuda del motor y del análisis. */
    public static final String OPTIONS_HELP = """
            Parámetros: A (p1 = t_a, p2 = l), B (p1 = t_a, p2 = k), F (p1 = A_p, p2 = B_p)
            Opciones: [--data data] [--dt-div 64] [--v0-frames 5] [--delta-a 0.1] [--rho 0.9] [--f-tie metric|angular] [--frontal-deg 5] [--f-horizon Infinity] [--f-gate on|off] [--f-distance centers|edges] [--integrator beeman|verlet]
            Recorte al tramo frontal (D3): [--trim on|off] [--trim-deg 45] [--trim-persist 5] [--trim-half 2] [--trim-target common|own] [--trim-shared on|off] [--trim-shared-x 1.5]
            """;

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
                                 todos los eventos: evento_XX.txt
                    run --event N [opciones] [--layer none|a|b|f --p1 X --p2 Y] [--out outputs/run]
                                 un solo evento: evento_XX.txt
                    integrator-check
                                 errores de Verlet y Beeman contra el peatón libre analítico
                    """ + OPTIONS_HELP);
            return;
        }
        switch (args[0]) {
            case "baseline" -> simulate(options(args, with("out", "layer", "p1", "p2")), null);
            case "run" -> {
                Map<String, String> o = options(args, with("event", "out", "layer", "p1", "p2"));
                if (!o.containsKey("event")) throw new IllegalArgumentException("run necesita --event");
                simulate(o, Integer.parseInt(o.get("event")));
            }
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

    /** Opciones comunes más las del comando. */
    public static Set<String> with(String... extra) {
        Set<String> allowed = new HashSet<>(COMMON);
        allowed.addAll(List.of(extra));
        return allowed;
    }

    public static int dtDiv(Map<String, String> o) { return Integer.parseInt(o.getOrDefault("dt-div", String.valueOf(Simulation.DEFAULT_DT_DIV))); }
    public static int v0Frames(Map<String, String> o) { return Integer.parseInt(o.getOrDefault("v0-frames", String.valueOf(DEFAULT_V0_FRAMES))); }
    public static double deltaA(Map<String, String> o) { return Double.parseDouble(o.getOrDefault("delta-a", String.valueOf(SfmParameters.DEFAULT_DELTA_A))); }
    public static LayerConstants constants(Map<String, String> o) {
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
    public static Integrator integrator(Map<String, String> o) { return o.containsKey("integrator") ? Integrator.parse(o.get("integrator")) : Integrator.DEFAULT; }

    /** Corrida configurada según las opciones: capa, integrador, Δt y δ_a. */
    public static Simulation simulation(Map<String, String> o) {
        return new Simulation(SfmParameters.withDeltaA(deltaA(o)), integrator(o), dtDiv(o), layer(o));
    }

    /** Encabezado de los archivos de salida de la corrida. */
    public static OutputFiles.RunInfo runInfo(Map<String, String> o) {
        return new OutputFiles.RunInfo(integrator(o).name(), dtDiv(o), v0Frames(o), deltaA(o), layer(o).label(), FrontalTrim.Options.parse(o).label());
    }

    public static Path out(Map<String, String> o, Integer onlyEvent) {
        return Path.of(o.getOrDefault("out", onlyEvent == null ? "outputs/baseline" : "outputs/run"));
    }

    private static void simulate(Map<String, String> o, Integer onlyEvent) throws IOException {
        Simulation sim = simulation(o);
        OutputFiles.RunInfo info = runInfo(o);
        Path out = out(o, onlyEvent);
        int v0Frames = v0Frames(o), count = 0;
        for (PedestrianEvent e : events(o, FrontalTrim.Options.parse(o))) {
            if (onlyEvent != null && e.number() != onlyEvent) continue;
            Simulation.Result result = sim.run(agents(e, v0Frames), e.dtExp(), e.windowIntervals());
            OutputFiles.writeTrajectory(out.resolve(String.format("evento_%02d.txt", e.number())), e, result, info);
            count++;
        }
        if (count == 0) throw new IllegalArgumentException("No existe el evento " + onlyEvent);
        System.out.println("Salida: " + out + " | eventos=" + count + " | " + integrator(o) + " dt_exp/" + dtDiv(o) + " | " + layer(o).label());
    }

    public static AvoidanceLayer layer(Map<String, String> o) {
        String name = o.getOrDefault("layer", "none");
        if (name.equalsIgnoreCase("none")) {
            if (o.containsKey("p1") || o.containsKey("p2")) throw new IllegalArgumentException("--p1 y --p2 necesitan --layer");
            return AvoidanceLayer.NONE;
        }
        if (!o.containsKey("p1") || !o.containsKey("p2")) throw new IllegalArgumentException("La capa necesita --p1 y --p2");
        return Layers.of(name, Double.parseDouble(o.get("p1")), Double.parseDouble(o.get("p2")), constants(o));
    }

    /** Eventos del LEEME, recortados al tramo frontal según las opciones (sin recorte con --trim off). */
    public static List<PedestrianEvent> events(Map<String, String> o, FrontalTrim.Options trim) throws IOException {
        return FrontalTrim.apply(EventParser.parse(Path.of(o.getOrDefault("data", "data"))), trim);
    }

    /** Los dos agentes del evento, con la velocidad inicial ajustada con {@code v0Frames} cuadros (D12). */
    public static Agent[] agents(PedestrianEvent e, int v0Frames) {
        return new Agent[] { Agent.from(e, 0, v0Frames), Agent.from(e, 1, v0Frames) };
    }

    public static double[] values(String text) {
        return Arrays.stream(text.split(",")).mapToDouble(s -> Double.parseDouble(s.trim())).toArray();
    }

    public static Map<String, String> options(String[] args, Set<String> allowed) {
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
