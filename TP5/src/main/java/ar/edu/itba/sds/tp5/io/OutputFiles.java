package ar.edu.itba.sds.tp5.io;

import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.metrics.Ecm;
import java.io.BufferedWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;

/** Archivos de salida del motor. Sin marcas de tiempo, para que dos corridas iguales den archivos idénticos. */
public final class OutputFiles {
    private OutputFiles() { }

    /** Parámetros de la corrida, para el encabezado de cada archivo. */
    public record RunInfo(String integrator, int dtDiv, int v0Frames, double deltaA, String layer) {
        String header() {
            return String.format(Locale.ROOT, "integrator=%s dt_div=%d v0_frames=%d delta_a=%s %s", integrator, dtDiv, v0Frames, deltaA, layer);
        }
    }

    /** Una fila por evento, con la llegada de cada peatón y, si no llega en la ventana, la de la corrida extendida. */
    public record EventReport(PedestrianEvent event, Simulation.Result sim, Ecm.Event ecm, double[] arrivalExtended) { }

    public static void writeTrajectory(Path file, PedestrianEvent e, Simulation.Result sim, RunInfo info) throws IOException {
        Files.createDirectories(file.toAbsolutePath().getParent());
        try (BufferedWriter out = Files.newBufferedWriter(file, StandardCharsets.UTF_8)) {
            out.write(String.format(Locale.ROOT, "# evento=%d id1=%d id2=%d frame_inicial=%d frame_final=%d dt_exp=%s %s\n",
                    e.number(), e.left().id(), e.right().id(), e.firstFrame(), e.lastFrame(), e.dtExp(), info.header()));
            out.write("# t x1 y1 vx1 vy1 x2 y2 vx2 vy2\n");
            for (double[] row : sim.rows()) {
                StringBuilder line = new StringBuilder(96);
                for (int c = 0; c < row.length; c++) {
                    if (c > 0) line.append(' ');
                    line.append(String.format(Locale.ROOT, "%.6f", row[c]));
                }
                out.write(line.append('\n').toString());
            }
        }
    }

    public static void writeEcmReport(Path file, List<EventReport> reports, RunInfo info) throws IOException {
        Files.createDirectories(file.toAbsolutePath().getParent());
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(file, StandardCharsets.UTF_8))) {
            out.println("# " + info.header());
            out.println("# evento peaton id ecm1_excl ecm1_relleno ecm2 N1 N2 t_end t_llegada anticipacion t_llegada_ext");
            int early = 0;
            double maxAdvance = 0, sumExcl = 0, sumFilled = 0, sum2 = 0;
            for (EventReport r : reports) {
                double tEnd = r.event().windowIntervals() * r.event().dtExp();
                for (int i = 0; i < 2; i++) {
                    Ecm.Pedestrian p = r.ecm().pedestrians()[i];
                    double arrival = r.sim().arrival()[i], advance = tEnd - arrival;
                    if (!Double.isNaN(arrival)) { early++; maxAdvance = Math.max(maxAdvance, advance); }
                    out.printf(Locale.ROOT, "%d %d %d %.6f %.6f %.6f %d %d %.4f %.4f %.4f %.4f%n", r.event().number(), i + 1,
                            r.event().pedestrian(i).id(), p.ecm1Excluding(), p.ecm1Filled(), p.ecm2(), p.n1(), p.n2(),
                            tEnd, arrival, advance, r.arrivalExtended()[i]);
                }
                sumExcl += r.ecm().ecm1Excluding();
                sumFilled += r.ecm().ecm1Filled();
                sum2 += r.ecm().ecm2();
            }
            int m = reports.size();
            out.println("# evento ecm1_excl ecm1_relleno ecm2 d_min_sim t_d_min contacto d_min_exp t_d_min_exp");
            for (EventReport r : reports) {
                PedestrianEvent.MinDistance exp = r.event().minDistance();
                out.printf(Locale.ROOT, "E %d %.6f %.6f %.6f %.4f %.4f %b %.4f %.4f%n", r.event().number(), r.ecm().ecm1Excluding(),
                        r.ecm().ecm1Filled(), r.ecm().ecm2(), r.sim().minDistance(), r.sim().minDistanceTime(), r.sim().anyContact(),
                        exp.distance(), (exp.frame() - r.event().firstFrame()) * r.event().dtExp());
            }
            out.printf(Locale.ROOT, "# poblacional ecm1_excl=%.6f ecm1_relleno=%.6f ecm2=%.6f%n", sumExcl / m, sumFilled / m, sum2 / m);
            out.printf(Locale.ROOT, "# llegan_en_ventana=%d de %d, anticipacion_maxima=%.4f s%n", early, 2 * m, maxAdvance);
            out.println("# orden_ecm1 " + orderComparison(reports));
        }
    }

    /** Compara el orden de los eventos (de menor a mayor ECM 1) entre las dos variantes. */
    static String orderComparison(List<EventReport> reports) {
        List<Integer> excl = order(reports, r -> r.ecm().ecm1Excluding());
        List<Integer> filled = order(reports, r -> r.ecm().ecm1Filled());
        if (excl.equals(filled)) return "sin_cambios excl=relleno=" + excl;
        List<Integer> moved = new ArrayList<>();
        for (int k = 0; k < excl.size(); k++) if (!excl.get(k).equals(filled.get(k))) moved.add(excl.get(k));
        return "cambia excl=" + excl + " relleno=" + filled + " eventos_movidos=" + moved;
    }

    private static List<Integer> order(List<EventReport> reports, java.util.function.ToDoubleFunction<EventReport> key) {
        return reports.stream().sorted(Comparator.comparingDouble(key)).map(r -> r.event().number()).toList();
    }
}
