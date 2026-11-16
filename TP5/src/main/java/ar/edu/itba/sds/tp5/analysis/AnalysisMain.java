package ar.edu.itba.sds.tp5.analysis;

import ar.edu.itba.sds.tp5.Main;
import ar.edu.itba.sds.tp5.data.EventParser;
import ar.edu.itba.sds.tp5.data.FrontalTrim;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.SfmParameters;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.Simulator;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import ar.edu.itba.sds.tp5.io.OutputFiles;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Análisis (no va al ZIP): corre el motor y calcula los observables. Mismos comandos y archivos que tenía el motor antes
 * de separarlo: baseline y run escriben evento_XX.txt (idéntico al del motor) y además ecm.txt; grid escribe una fila
 * por par y evento; trim-export, el recorte. Uso: java -cp target/tp5.jar ar.edu.itba.sds.tp5.analysis.AnalysisMain ...
 */
public final class AnalysisMain {
    private AnalysisMain() { }

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
                    Con --model cpm, todos los comandos corren el CPM en lugar del SFM, con las mismas capas.
                    baseline [opciones] [--layer none|a|b|f|e --p1 X --p2 Y] [--out outputs/baseline] [--direction-series true]
                                 todos los eventos: evento_XX.txt y ecm.txt
                    run --event N [opciones] [--layer none|a|b|f|e --p1 X --p2 Y] [--out outputs/run] [--direction-series true]
                                 un solo evento; con --direction-series, también direccion_XX.txt (e_t y e_target)
                    grid --layer a|b|f|e --p1-values X,Y,... --p2-values X,Y,... --out archivo [--event N] [opciones]
                                 una fila por par y evento, sin archivos de trayectoria
                                 alternativa: --pairs-file archivo (dos columnas p1 p2), sin ejes cartesianos
                    grid-ped --layer a|b|f|e --p1-values ... --p2-values ... --out archivo
                                 calibración individual opcional: un par (p1, p2) por peatón, 4 parámetros por evento
                    trim-export [--out outputs/recorte] [opciones]
                                 trayectorias_recortadas.csv y recorte_eventos.csv: el recorte que usa el motor
                    """ + Main.OPTIONS_HELP);
            return;
        }
        switch (args[0]) {
            case "baseline" -> simulate(Main.options(args, Main.with("out", "layer", "p1", "p2", "direction-series")), null);
            case "run" -> {
                Map<String, String> o = Main.options(args, Main.with("event", "out", "layer", "p1", "p2", "direction-series"));
                if (!o.containsKey("event")) throw new IllegalArgumentException("run necesita --event");
                simulate(o, Integer.parseInt(o.get("event")));
            }
            case "grid" -> grid(Main.options(args, Main.with("layer", "p1-values", "p2-values", "pairs-file", "out", "event")));
            case "grid-ped" -> pedestrianGrid(Main.options(args, Main.with("layer", "p1-values", "p2-values", "out")));
            case "trim-export" -> {
                Map<String, String> o = Main.options(args, Main.with("out"));
                FrontalTrim.Options trim = FrontalTrim.Options.parse(o);
                Path out = Path.of(o.getOrDefault("out", "outputs/recorte"));
                TrimExport.write(out, EventParser.parse(Path.of(o.getOrDefault("data", "data"))), trim, Main.v0Frames(o));
                System.out.println("Recorte: " + out + " | " + trim.label());
            }
            default -> throw new IllegalArgumentException("Comando desconocido: " + args[0]);
        }
    }

    private static void simulate(Map<String, String> o, Integer onlyEvent) throws IOException {
        Simulator sim = Main.simulation(o);
        AvoidanceLayer layer = Main.layer(o);
        OutputFiles.RunInfo info = Main.runInfo(o);
        Path out = Main.out(o, onlyEvent);
        int v0Frames = Main.v0Frames(o);
        double radius = Main.contactRadius(o);
        List<EcmReport.EventReport> reports = new ArrayList<>();
        for (PedestrianEvent e : Main.events(o, FrontalTrim.Options.parse(o))) {
            if (onlyEvent != null && e.number() != onlyEvent) continue;
            EcmReport.EventReport report = run(sim, e, v0Frames, radius);
            OutputFiles.writeTrajectory(out.resolve(String.format("evento_%02d.txt", e.number())), e, report.sim(), info);
            if (Boolean.parseBoolean(o.getOrDefault("direction-series", "false")))
                DirectionSeries.write(out.resolve(String.format("direccion_%02d.txt", e.number())), e, sim, layer, v0Frames);
            reports.add(report);
        }
        if (reports.isEmpty()) throw new IllegalArgumentException("No existe el evento " + onlyEvent);
        EcmReport.write(out.resolve("ecm.txt"), reports, info);
        System.out.println("Salida: " + out + " | eventos=" + reports.size() + " | " + Main.modelLabel(o) + " | " + layer.label());
    }

    /** Corre el evento en su ventana, midiendo contactos en cada paso y, si alguien no llegó, hasta el tope para saber cuándo llegaría. */
    public static EcmReport.EventReport run(Simulator sim, PedestrianEvent e, int v0Frames, double radius) {
        Agent[] agents = Main.agents(e, v0Frames);
        ContactMonitor contacts = new ContactMonitor(radius);
        Simulation.Result result = sim.run(agents, e.dtExp(), e.windowIntervals(), contacts);
        double[] extended = result.arrival().clone();
        if (Double.isNaN(extended[0]) || Double.isNaN(extended[1]))
            extended = sim.run(agents, e.dtExp(), Main.EXTENDED_INTERVALS).arrival();
        return new EcmReport.EventReport(e, result, Ecm.of(e, result), contacts.stats(), extended);
    }

    /** Calibración individual opcional: 4 parámetros por evento (un par por peatón). */
    private static void pedestrianGrid(Map<String, String> o) throws IOException {
        for (String key : List.of("layer", "p1-values", "p2-values", "out"))
            if (!o.containsKey(key)) throw new IllegalArgumentException("grid-ped necesita --" + key);
        double[] p1 = Main.values(o.get("p1-values")), p2 = Main.values(o.get("p2-values"));
        String layer = o.get("layer");
        FrontalTrim.Options trim = FrontalTrim.Options.parse(o);
        List<String> lines = PedestrianGridSearch.run(layer, p1, p2, Main.events(o, trim),
                l -> Main.simulator(o, l), Main.contactRadius(o), Main.constants(o), Main.v0Frames(o));
        PedestrianGridSearch.write(Path.of(o.get("out")), layer + (Main.cpm(o) ? " modelo=CPM" : ""), trim, lines);
        int pairs = p1.length * p2.length;
        System.out.println("Grilla por peatón: " + o.get("out") + " | capa=" + layer + " | combinaciones por evento=" + pairs * pairs);
    }

    private static void grid(Map<String, String> o) throws IOException {
        for (String key : List.of("layer", "out"))
            if (!o.containsKey(key)) throw new IllegalArgumentException("grid necesita --" + key);
        List<double[]> pairs = new ArrayList<>();
        if (o.containsKey("pairs-file")) {
            if (o.containsKey("p1-values") || o.containsKey("p2-values"))
                throw new IllegalArgumentException("Usar --pairs-file o los dos ejes, no ambos");
            for (String line : Files.readAllLines(Path.of(o.get("pairs-file")))) {
                String text = line.strip();
                if (text.isEmpty() || text.startsWith("#")) continue;
                String[] fields = text.split("\\s+");
                if (fields.length != 2) throw new IllegalArgumentException("Se esperan dos columnas p1 p2");
                double a = Double.parseDouble(fields[0]), b = Double.parseDouble(fields[1]);
                if (!Double.isFinite(a) || !Double.isFinite(b)) throw new IllegalArgumentException("Par no finito");
                pairs.add(new double[] { a, b });
            }
            if (pairs.isEmpty()) throw new IllegalArgumentException("Archivo de pares vacío");
        } else {
            for (String key : List.of("p1-values", "p2-values"))
                if (!o.containsKey(key)) throw new IllegalArgumentException("grid necesita --" + key);
            for (double a : Main.values(o.get("p1-values")))
                for (double b : Main.values(o.get("p2-values"))) pairs.add(new double[] { a, b });
        }
        String layer = o.get("layer");
        FrontalTrim.Options trim = FrontalTrim.Options.parse(o);
        List<PedestrianEvent> events = Main.events(o, trim);
        if (o.containsKey("event")) {
            int number = Integer.parseInt(o.get("event"));
            events = events.stream().filter(e -> e.number() == number).toList();
            if (events.isEmpty()) throw new IllegalArgumentException("No existe el evento " + number);
        }
        List<GridSearch.Row> rows = GridSearch.runPairs(layer, pairs, events,
                l -> Main.simulator(o, l), Main.contactRadius(o), Main.constants(o), Main.v0Frames(o));
        GridSearch.write(Path.of(o.get("out")), layer, trim, rows);
        System.out.println("Grilla: " + o.get("out") + " | capa=" + layer + " | pares=" + pairs.size());
    }
}
