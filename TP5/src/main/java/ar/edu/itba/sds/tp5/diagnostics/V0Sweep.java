package ar.edu.itba.sds.tp5.diagnostics;

import ar.edu.itba.sds.tp5.Main;
import ar.edu.itba.sds.tp5.analysis.AnalysisMain;
import ar.edu.itba.sds.tp5.analysis.EcmReport;
import ar.edu.itba.sds.tp5.data.FrontalTrim;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/** Barrido diagnóstico de D12, fuera del motor y del ZIP. No recalibra las capas. */
public final class V0Sweep {
    private V0Sweep() { }

    private static final List<Map<String, String>> CONFIGS = List.of(
            Map.of("layer", "A", "p1", "3", "p2", "0.5"),
            Map.of("layer", "B", "p1", "3.5", "p2", "1"));

    /** Tolera solamente el redondeo numérico, no un exceso físico de rapidez. */
    static boolean exceedsDesired(double speed, double desired) {
        return speed - desired > 1e-9;
    }

    public static void main(String[] args) throws IOException {
        Map<String, String> options = new HashMap<>();
        if (args.length % 2 != 0) throw new IllegalArgumentException("Se esperan pares --opcion valor");
        for (int i = 0; i < args.length; i += 2) options.put(args[i].substring(2), args[i + 1]);
        int start = Integer.parseInt(options.getOrDefault("start", "2"));
        if (start < 2) throw new IllegalArgumentException("El ajuste necesita al menos 2 cuadros");
        List<PedestrianEvent> events = Main.events(options, FrontalTrim.Options.parse(options));
        // El ajuste usa observaciones presentes y debe quedar dentro de la ventana del evento.
        int available = events.stream().flatMapToInt(e -> java.util.stream.IntStream.range(0, 2).map(i -> {
            var t = e.pedestrian(i);
            int count = 0;
            for (int f : t.frames()) if (f >= e.firstFrame() && f <= e.lastFrame()) count++;
            return count;
        })).min().orElseThrow();
        int end = Math.min(available, Integer.parseInt(options.getOrDefault("max", "" + available)));
        if (start > end) throw new IllegalArgumentException("No hay suficientes cuadros para el barrido");
        Path out = Path.of(options.getOrDefault("out", "outputs/pilot/sensitivity_v0/sweep"));
        Files.createDirectories(out);
        try (PrintWriter csv = new PrintWriter(Files.newBufferedWriter(out.resolve("sweep.csv"), StandardCharsets.UTF_8));
             PrintWriter speeds = new PrintWriter(Files.newBufferedWriter(out.resolve("speeds.csv"), StandardCharsets.UTF_8));
             PrintWriter log = new PrintWriter(Files.newBufferedWriter(out.resolve("criterio.txt"), StandardCharsets.UTF_8))) {
            csv.println("frames,layer,p1,p2,ecm1,ecm2,contact_events,speed_events,valid");
            speeds.println("frames,event,pedestrian,v0,vd,difference,exceeds_desired");
            log.printf("Inicio=%d; paso=1; máximo disponible=%d%n", start, end);
            log.println("Barrido completo hasta el mínimo de observaciones disponibles entre todos los peatones de todos los eventos.");
            for (var e : events) for (int i = 0; i < 2; i++) {
                int count = 0;
                for (int f : e.pedestrian(i).frames()) if (f >= e.firstFrame() && f <= e.lastFrame()) count++;
                if (count == available) log.printf("Límite: evento %d, peatón %d, %d observaciones en la ventana.%n", e.number(), i + 1, count);
            }
            log.println("Inválido por capa si hay algún choque o si |v0| > vd en algún peatón (tolerancia numérica 1e-9 m/s).");
            log.println("Las condiciones de invalidez no interrumpen el barrido. Los choques se miden en cada paso de integración (distancia entre centros < 2R), dentro de la ventana experimental.");
            for (int n = start; n <= end; n++) {
                List<String> speedHits = new ArrayList<>();
                for (int k = 0; k < events.size(); k++) for (int i = 0; i < 2; i++) {
                    var e = events.get(k);
                    Agent a = Agent.from(e, i, n);
                    double speed = Math.hypot(a.vx0(), a.vy0());
                    double difference = speed - a.desiredSpeed();
                    boolean hit = exceedsDesired(speed, a.desiredSpeed());
                    if (hit) speedHits.add(e.number() + ":" + (i + 1));
                    speeds.printf(Locale.ROOT, "%d,%d,%d,%.12f,%.12f,%.12f,%b%n", n, e.number(), i + 1,
                            speed, a.desiredSpeed(), difference, hit);
                }
                for (var config : CONFIGS) {
                    var run = new HashMap<>(options);
                    run.putAll(config);
                    run.put("v0-frames", "" + n);
                    String layer = config.get("layer");
                    var sim = Main.simulation(run);
                    List<EcmReport.EventReport> reports = new ArrayList<>();
                    List<String> contacts = new ArrayList<>();
                    for (var e : events) {
                        var report = AnalysisMain.run(sim, e, n, Main.contactRadius(run));
                        reports.add(report);
                        if (report.contacts().anyContact()) {
                            contacts.add("" + e.number());
                        }
                    }
                    EcmReport.write(out.resolve(layer + "/v0_" + n + "/ecm.txt"), reports, Main.runInfo(run));
                    double ecm1 = reports.stream().mapToDouble(r -> r.ecm().ecm1Excluding()).average().orElseThrow();
                    double ecm2 = reports.stream().mapToDouble(r -> r.ecm().ecm2()).average().orElseThrow();
                    boolean valid = contacts.isEmpty() && speedHits.isEmpty();
                    csv.printf(Locale.ROOT, "%d,%s,%s,%s,%.12f,%.12f,%s,%s,%b%n", n, layer,
                            config.get("p1"), config.get("p2"), ecm1, ecm2, String.join(";", contacts),
                            String.join(";", speedHits), valid);
                    log.printf(Locale.ROOT, "n=%d %s: ECM1=%.6f; choques=%s; excesos vd=%s; válido=%b%n", n, layer, ecm1, contacts, speedHits, valid);
                }
                if (n % 10 == 0 || n == end) System.out.printf("Barrido: %d/%d cuadros%n", n, end);
            }
        }
        System.out.println("Barrido completo: " + out + " (" + start + " a " + end + " cuadros)");
    }
}
