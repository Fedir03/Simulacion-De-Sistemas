package ar.edu.itba.sds.tp5.diagnostics;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.data.EventParser;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import ar.edu.itba.sds.tp5.engine.layer.LateralTargetLayer;
import ar.edu.itba.sds.tp5.engine.layer.LayerConstants;
import ar.edu.itba.sds.tp5.engine.layer.RepulsiveDirectionLayer;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;

class RunTraceTest {
    private static final LayerConstants C = LayerConstants.defaults();

    @Test
    void traceCountsTheSameSwitchesAsTheSimulation() throws IOException {
        List<PedestrianEvent> events = EventParser.parse(Path.of("data"));
        for (PedestrianEvent e : events) {
            RunTrace.Trace a = RunTrace.run(e, LateralTargetLayer.a(0.5, 0, C), 0.5, C, 5);
            RunTrace.Trace f = RunTrace.run(e, new RepulsiveDirectionLayer(0.5, 2, C), Double.POSITIVE_INFINITY, C, 5);
            for (RunTrace.Trace t : List.of(a, f)) {
                int fromTrace = t.switches().size();
                int fromSimulation = t.result().layerSwitches()[0] + t.result().layerSwitches()[1];
                assertEquals(fromSimulation, fromTrace, "evento " + e.number());
            }
        }
    }

    @Test
    void contactEpisodesMatchTheContactFlag() throws IOException {
        for (PedestrianEvent e : EventParser.parse(Path.of("data"))) {
            RunTrace.Trace t = RunTrace.run(e, AvoidanceLayer.NONE, 1, C, 5);
            assertEquals(t.result().anyContact(), !t.contacts().isEmpty(), "evento " + e.number());
            for (RunTrace.Contact c : t.contacts()) {
                assertTrue(c.end() >= c.start());
                assertTrue(c.maxOverlap() > 0);
            }
            assertFalse(t.switches().stream().anyMatch(RunTrace.Switch::on), "sin capa no se activa nada");
        }
    }
}
