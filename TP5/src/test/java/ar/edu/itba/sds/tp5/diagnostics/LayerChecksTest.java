package ar.edu.itba.sds.tp5.diagnostics;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
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
import ar.edu.itba.sds.tp5.analysis.Ecm;
import ar.edu.itba.sds.tp5.analysis.MotionMonitor;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;

class LayerChecksTest {
    private static final LayerConstants C = LayerConstants.defaults();
    private static final Object[][] PAIRS = { { "a", 2.5, 2.5 }, { "a", 4.0, 0.5 }, { "b", 2.5, 4.0 }, { "b", 4.5, 1.0 }, { "f", 0.9, 2.5 }, { "f", 0.8, 3.0 } };

    private static Simulation.Result run(PedestrianEvent e, AvoidanceLayer layer) {
        return run(e, layer, null);
    }

    private static Simulation.Result run(PedestrianEvent e, AvoidanceLayer layer, Simulation.StepObserver observer) {
        Simulation sim = new Simulation(SfmParameters.defaults(), Integrator.DEFAULT, Simulation.DEFAULT_DT_DIV, layer);
        return sim.run(new Agent[] { Agent.from(e, 0, 5), Agent.from(e, 1, 5) }, e.dtExp(), e.windowIntervals(), observer);
    }

    @Test
    void theRecorderDoesNotChangeTheRunAndCountsTheSameSwitches() throws IOException {
        for (PedestrianEvent e : EventParser.parse(Path.of("data"))) {
            MotionMonitor motion = new MotionMonitor();
            Simulation.Result expected = run(e, Layers.of("f", 0.9, 2.5, C), motion);
            LayerChecks.Run recorded = LayerChecks.run(e, "f", 0.9, 2.5, C);
            assertEquals(expected.rows().size(), recorded.result().rows().size());
            for (int k = 0; k < expected.rows().size(); k++)
                assertArrayEquals(expected.rows().get(k), recorded.result().rows().get(k), 0.0);
            for (int i = 0; i < 2; i++)
                assertEquals(motion.layerSwitches()[i], recorded.recorder().stats(i).switchesCheck(), "evento " + e.number() + ", agente " + i);
        }
    }

    /** Auditoría, ítem 9: en los 19 eventos, sin pasar por un desempate, la corrida reflejada es el espejo exacto. */
    @Test
    void withoutATieTheMirroredEventIsAnExactMirror() throws IOException {
        List<PedestrianEvent> events = EventParser.parse(Path.of("data"));
        int checked = 0;
        for (Object[] p : PAIRS) {
            for (PedestrianEvent e : events) {
                LayerChecks.Run direct = LayerChecks.run(e, (String) p[0], (double) p[1], (double) p[2], C);
                LayerChecks.Run mirrored = LayerChecks.run(LayerChecks.mirror(e), (String) p[0], (double) p[1], (double) p[2], C);
                if (direct.ties() + mirrored.ties() > 0) continue;
                checked++;
                double difference = LayerChecks.mirrorDifference(direct.result(), mirrored.result());
                assertTrue(difference < 1e-9, p[0] + " " + p[1] + " " + p[2] + ", evento " + e.number() + ": " + difference);
            }
        }
        assertTrue(checked > 0);
    }

    /** Después de corregir el desempate, en ningún paso de los 19 eventos F termina a la izquierda en un desempate. */
    @Test
    void afterTheCorrectionNoTieEndsOnTheLeft() throws IOException {
        for (PedestrianEvent e : EventParser.parse(Path.of("data")))
            for (double[] p : new double[][] { { 0.9, 2.5 }, { 0.8, 3.0 } }) {
                LayerChecks.Run r = LayerChecks.run(e, "f", p[0], p[1], C);
                assertEquals(0, r.recorder().stats(0).tieLeft() + r.recorder().stats(1).tieLeft(), "evento " + e.number());
            }
    }

    /** Prueba 4a: el par que generó los datos los reproduce exactamente; otro par, no. */
    @Test
    void theGeneratingPairHasZeroErrorOnItsSyntheticData() throws IOException {
        List<PedestrianEvent> events = EventParser.parse(Path.of("data"));
        AvoidanceLayer source = Layers.of("a", 2.5, 1.5, C);
        double other = 0;
        for (PedestrianEvent e : events) {
            PedestrianEvent data = LayerChecks.syntheticEvent(e, run(e, source));
            Ecm.Event same = Ecm.of(data, run(e, source));
            assertEquals(0, same.ecm1Excluding(), 0.0, "evento " + e.number());
            assertEquals(0, same.ecm2(), 0.0, "evento " + e.number());
            other += Ecm.of(data, run(e, Layers.of("a", 2.5, 2.5, C))).ecm1Excluding();
        }
        assertTrue(other > 0);
    }

    /** Prueba 4c: la moneda decide el lado y conserva el resto de la dirección. */
    @Test
    void theCoinChoosesTheSideAndKeepsTheRestOfTheDirection() {
        AvoidanceLayer base = Layers.of("a", 2, 1, C);
        double[] rule = new double[2], right = new double[2], left = new double[2];
        // j a la izquierda de i, que va por +x: la regla esquiva a la derecha (−y)
        base.direction(0, 0, 4, 0.5, -1, 0, 1, 1, 0, rule);
        AvoidanceLayer coin = LayerChecks.coinSide(base, new boolean[] { true, false });
        assertTrue(coin.forAgent(0).direction(0, 0, 4, 0.5, -1, 0, 1, 1, 0, right));
        assertTrue(coin.forAgent(1).direction(0, 0, 4, 0.5, -1, 0, 1, 1, 0, left));
        assertEquals(rule[0], right[0], 1e-12);
        assertEquals(rule[1], right[1], 1e-12);
        assertEquals(rule[0], left[0], 1e-12);
        assertEquals(-rule[1], left[1], 1e-12);
        // Sin choque predicho no hace nada
        assertFalse(coin.forAgent(0).direction(0, 0, 4, 3, -1, 0, 1, 1, 0, new double[2]));
    }
}
