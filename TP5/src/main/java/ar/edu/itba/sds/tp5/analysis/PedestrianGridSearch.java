package ar.edu.itba.sds.tp5.analysis;

import ar.edu.itba.sds.tp5.data.FrontalTrim;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Integrator;
import ar.edu.itba.sds.tp5.engine.SfmParameters;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.layer.LayerConstants;
import ar.edu.itba.sds.tp5.engine.layer.Layers;
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
 * Calibración individual opcional (punto c): parámetros por peatón. Para cada evento corre todas las combinaciones
 * (p1, p2) del peatón 1 por (p1, p2) del peatón 2 de la grilla, o sea 4 parámetros por evento. Los dos peatones
 * interactúan, así que no se pueden calibrar por separado. Las combinaciones con los dos pares iguales son la grilla
 * de 2 parámetros.
 */
public final class PedestrianGridSearch {
    private PedestrianGridSearch() { }

    public static List<String> run(String layer, double[] p1Values, double[] p2Values, List<PedestrianEvent> events,
                                   SfmParameters params, LayerConstants constants, Integrator integrator, int dtDiv, int v0Frames) {
        List<double[]> pairs = new ArrayList<>();
        for (double p1 : p1Values) for (double p2 : p2Values) pairs.add(new double[] { p1, p2 });
        int n = pairs.size();
        List<String> lines = new ArrayList<>();
        for (PedestrianEvent e : events) {
            Agent[] agents = { Agent.from(e, 0, v0Frames), Agent.from(e, 1, v0Frames) };
            lines.addAll(IntStream.range(0, n * n).parallel().mapToObj(k -> {
                double[] first = pairs.get(k / n), second = pairs.get(k % n);
                Simulation sim = new Simulation(params, integrator, dtDiv,
                        Layers.perPedestrian(layer, first[0], first[1], second[0], second[1], constants));
                ContactMonitor contacts = new ContactMonitor(params.radius());
                Simulation.Result result = sim.run(agents, e.dtExp(), e.windowIntervals(), contacts);
                Ecm.Event ecm = Ecm.of(e, result);
                Ecm.Pedestrian a = ecm.pedestrians()[0], b = ecm.pedestrians()[1];
                return String.format(Locale.ROOT, "%s %s %s %s %d %.6f %.6f %.6f %.6f %.6f %.6f %b %.4f", first[0], first[1], second[0], second[1],
                        e.number(), ecm.ecm1Excluding(), ecm.ecm2(), a.ecm1Excluding(), b.ecm1Excluding(), a.ecm2(), b.ecm2(),
                        contacts.stats().anyContact(), contacts.stats().minDistance());
            }).toList());
        }
        return lines;
    }

    public static void write(Path file, String layer, FrontalTrim.Options trim, List<String> lines) throws IOException {
        Files.createDirectories(file.toAbsolutePath().getParent());
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(file, StandardCharsets.UTF_8))) {
            out.print("# capa=" + layer + " por_peaton" + (trim.enabled() ? " " + trim.label() : "") + "\n");
            out.print("# p1_1 p2_1 p1_2 p2_2 evento ecm1_excl ecm2 ecm1_excl_1 ecm1_excl_2 ecm2_1 ecm2_2 contacto d_min\n");
            for (String line : lines) out.print(line + "\n");
        }
    }
}
