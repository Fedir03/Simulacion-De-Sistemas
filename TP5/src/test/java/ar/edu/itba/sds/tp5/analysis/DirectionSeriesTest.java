package ar.edu.itba.sds.tp5.analysis;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.data.EventParser;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Integrator;
import ar.edu.itba.sds.tp5.engine.SfmParameters;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import ar.edu.itba.sds.tp5.engine.layer.LayerConstants;
import ar.edu.itba.sds.tp5.engine.layer.Layers;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class DirectionSeriesTest {
    private static Simulation simulation(AvoidanceLayer layer) {
        return new Simulation(SfmParameters.defaults(), Integrator.DEFAULT, Simulation.DEFAULT_DT_DIV, layer);
    }

    private static List<String> series(Path dir, PedestrianEvent e, AvoidanceLayer layer) throws IOException {
        Path file = dir.resolve("direccion.txt");
        DirectionSeries.write(file, e, simulation(layer), layer, 5);
        return Files.readAllLines(file);
    }

    @Test
    void hasOneRowPerOutputRowAndUnitDirections(@TempDir Path dir) throws IOException {
        PedestrianEvent e = EventParser.parse(Path.of("data")).get(11);
        AvoidanceLayer f = Layers.of("f", 0.9, 2.5, LayerConstants.defaults());
        Simulation.Result run = simulation(f).run(new Agent[] { Agent.from(e, 0, 5), Agent.from(e, 1, 5) }, e.dtExp(), e.windowIntervals());
        List<String> lines = series(dir, e, f);
        assertEquals(run.rows().size() + 1, lines.size());
        boolean anyOn = false;
        for (int k = 1; k < lines.size(); k++) {
            String[] p = lines.get(k).split(" ");
            assertEquals(run.rows().get(k - 1)[0], Double.parseDouble(p[0]), 1e-6);
            for (int base : new int[] { 1, 6 }) {
                if (p[base].equals("NaN")) continue;
                assertEquals(1, Math.hypot(Double.parseDouble(p[base + 3]), Double.parseDouble(p[base + 4])), 1e-5);
                anyOn |= p[base].equals("1");
            }
        }
        assertTrue(anyOn);
    }

    @Test
    void withoutALayerTheTargetDirectionIsTheFinalOne(@TempDir Path dir) throws IOException {
        PedestrianEvent e = EventParser.parse(Path.of("data")).get(2);
        List<String> lines = series(dir, e, AvoidanceLayer.NONE);
        for (int k = 1; k < lines.size(); k++) {
            String[] p = lines.get(k).split(" ");
            if (p[1].equals("NaN")) continue;
            assertEquals("0", p[1]);
            assertEquals(p[2], p[4]);
            assertEquals(p[3], p[5]);
        }
    }
}
