package ar.edu.itba.sds.tp5.engine.cpm;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import ar.edu.itba.sds.tp5.engine.layer.EggLayer;
import ar.edu.itba.sds.tp5.engine.layer.LateralTargetLayer;
import ar.edu.itba.sds.tp5.engine.layer.LayerConstants;
import org.junit.jupiter.api.Test;

class CpmSimulationTest {
    private static final CpmParameters P = CpmParameters.withDeltaA(0.1);
    private static final double DT_EXP = 1 / 15.0;

    private static Simulation.Result run(AvoidanceLayer layer, int intervals, Agent... agents) {
        return new CpmSimulation(P, layer).run(agents, DT_EXP, intervals);
    }

    private static Agent[] headOn(double offset) {
        return new Agent[] { new Agent(0, 0, 1.3, 0, 10, 0, 1.3), new Agent(8, offset, -1.3, 0, -2, offset, 1.3) };
    }

    @Test void speedAndRadiusAreInverse() {
        for (double s : new double[] { 0, 0.3, 0.9, 1.29 }) assertEquals(s, P.speed(P.radiusFor(s, 1.3), 1.3), 1e-12);
        assertEquals(P.rMax(), P.radiusFor(2, 1.3));
        assertEquals(0.1 / (2 * 1.3), new CpmSimulation(P, AvoidanceLayer.NONE).dt(headOn(0)), 1e-15);
    }

    @Test void rowsFallOnTheExperimentalGridAndEndAtTheLastInstant() {
        Simulation.Result r = run(AvoidanceLayer.NONE, 30, new Agent(0, 0, 1, 0, 100, 0, 1));
        assertEquals(30 * Simulation.ROWS_PER_INTERVAL + 1, r.rows().size());
        for (int k = 0; k < r.rows().size(); k++) assertEquals(k * DT_EXP / 4, r.rows().get(k)[0], 1e-12);
        assertEquals(1 + 5, r.rows().get(0).length);   // t, x, y, vx, vy, r
    }

    /** Agente libre que arranca quieto: el radio crece r_max Δt/τ por paso y la rapidez llega a v_d en τ (1 − r_min/r_max). */
    @Test void freeAgentRelaxesToItsDesiredSpeedTowardTheTarget() {
        Simulation.Result r = run(AvoidanceLayer.NONE, 30, new Agent(0, 0, 0, 0, 100, 3, 1.4));
        double[] last = r.rows().get(r.rows().size() - 1);
        assertEquals(1.4, Math.hypot(last[3], last[4]), 1e-12);
        assertEquals(P.rMax(), last[5], 1e-12);
        assertEquals(3 / Math.hypot(100, 3), last[4] / 1.4, 1e-9);
        // a t = 0,2 s (antes de τ (1 − r_min/r_max) = 0,3 s) todavía no llegó
        assertTrue(Math.hypot(r.rows().get(12)[3], r.rows().get(12)[4]) < 1.4);
    }

    @Test void headOnWithoutLayerTouchesAndEscapesWithoutCrossingTheHardCore() {
        Simulation.Result r = run(AvoidanceLayer.NONE, 120, headOn(0.05));
        assertTrue(r.contactSteps()[0] > 0 && r.contactSteps()[1] > 0);
        for (double[] row : r.rows()) {
            if (Double.isNaN(row[1]) || Double.isNaN(row[5])) continue;
            assertTrue(Math.hypot(row[1] - row[5], row[2] - row[6]) > P.rMin());
        }
    }

    @Test void layerWithoutLateralShiftIsTheBareModel() {
        LayerConstants c = LayerConstants.defaults();
        Simulation.Result base = run(AvoidanceLayer.NONE, 120, headOn(0.05));
        Simulation.Result zero = run(LateralTargetLayer.a(3, 0, c), 120, headOn(0.05));
        assertEquals(base.rows().size(), zero.rows().size());
        for (int k = 0; k < base.rows().size(); k++) assertArrayEquals(base.rows().get(k), zero.rows().get(k));
    }

    @Test void layersAvoidTheContactOfTheBareModel() {
        LayerConstants c = LayerConstants.defaults();
        for (AvoidanceLayer layer : new AvoidanceLayer[] { LateralTargetLayer.a(3, 0.5, c), LateralTargetLayer.b(3.5, 1, c), new EggLayer(3, 0.35) }) {
            Simulation.Result r = run(layer, 120, headOn(0.05));
            assertEquals(0, r.contactSteps()[0] + r.contactSteps()[1], layer.label());
        }
    }
}
