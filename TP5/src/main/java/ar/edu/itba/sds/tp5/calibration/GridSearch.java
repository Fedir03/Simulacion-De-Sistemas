package ar.edu.itba.sds.tp5.calibration;

import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Integrator;
import ar.edu.itba.sds.tp5.engine.SfmParameters;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.layer.LayerConstants;
import ar.edu.itba.sds.tp5.engine.layer.Layers;
import ar.edu.itba.sds.tp5.metrics.Ecm;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.stream.IntStream;

/**
 * Corre una capa en todos los eventos para cada par (p1, p2) y escribe una fila por par y evento. Las corridas son
 * deterministas e independientes, así que el resultado no depende del paralelismo.
 */
public final class GridSearch {
    private GridSearch() { }

    /** Una fila del archivo: resultado de un par en un evento. */
    public record Row(double p1, double p2, int event, Ecm.Event ecm, Simulation.Result sim) {
        String line() {
            Ecm.Pedestrian a = ecm.pedestrians()[0], b = ecm.pedestrians()[1];
            return String.format(Locale.ROOT, "%s %s %d %.6f %.6f %.6f %d %d %d %d %b %.4f %.4f %.4f %.4f %d %d", p1, p2, event,
                    ecm.ecm1Excluding(), ecm.ecm1Filled(), ecm.ecm2(), a.n1(), b.n1(), a.n2(), b.n2(), sim.anyContact(),
                    sim.minDistance(), sim.minDistanceTime(), sim.arrival()[0], sim.arrival()[1],
                    sim.layerSwitches()[0], sim.layerSwitches()[1]);
        }
    }

    public static List<Row> run(String layer, double[] p1Values, double[] p2Values, List<PedestrianEvent> events,
                                SfmParameters params, LayerConstants constants, Integrator integrator, int dtDiv, int v0Frames) {
        List<double[]> pairs = new ArrayList<>();
        for (double p1 : p1Values) for (double p2 : p2Values) pairs.add(new double[] { p1, p2 });
        return IntStream.range(0, pairs.size()).parallel().boxed().flatMap(k -> {
            double p1 = pairs.get(k)[0], p2 = pairs.get(k)[1];
            Simulation sim = new Simulation(params, integrator, dtDiv, Layers.of(layer, p1, p2, constants));
            List<Row> rows = new ArrayList<>(events.size());
            for (PedestrianEvent e : events) {
                Agent[] agents = { Agent.from(e, 0, v0Frames), Agent.from(e, 1, v0Frames) };
                Simulation.Result result = sim.run(agents, e.dtExp(), e.windowIntervals());
                rows.add(new Row(p1, p2, e.number(), Ecm.of(e, result), result));
            }
            return rows.stream();
        }).toList();
    }

    public static void write(Path file, String layer, List<Row> rows) throws IOException {
        Files.createDirectories(file.toAbsolutePath().getParent());
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(file, StandardCharsets.UTF_8))) {
            out.print("# capa=" + layer + "\n");
            out.print("# p1 p2 evento ecm1_excl ecm1_relleno ecm2 N1_1 N1_2 N2_1 N2_2 contacto d_min t_d_min t_llegada1 t_llegada2 conmutaciones1 conmutaciones2\n");
            for (Row row : rows) out.print(row.line() + "\n");
        }
    }
}
