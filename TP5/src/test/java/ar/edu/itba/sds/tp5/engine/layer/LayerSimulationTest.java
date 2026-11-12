package ar.edu.itba.sds.tp5.engine.layer;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.Main;
import ar.edu.itba.sds.tp5.analysis.ContactMonitor;
import ar.edu.itba.sds.tp5.analysis.MotionMonitor;
import ar.edu.itba.sds.tp5.data.EventParser;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Integrator;
import ar.edu.itba.sds.tp5.engine.SfmField;
import ar.edu.itba.sds.tp5.engine.SfmParameters;
import ar.edu.itba.sds.tp5.engine.Simulation;
import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;

/** Pruebas de la especificación antes del piloto. */
class LayerSimulationTest {
    private static final double DT_EXP = 1 / 15.0192;
    private static final LayerConstants C = LayerConstants.defaults();
    private static final SfmParameters P = SfmParameters.defaults();
    private static final Simulation BASE = new Simulation(P, Integrator.DEFAULT, Simulation.DEFAULT_DT_DIV);

    private static Simulation with(AvoidanceLayer layer) {
        return new Simulation(P, Integrator.DEFAULT, Simulation.DEFAULT_DT_DIV, layer);
    }

    private static void assertSameRun(Simulation.Result expected, Simulation.Result actual, String label) {
        assertEquals(expected.rows().size(), actual.rows().size(), label);
        for (int k = 0; k < expected.rows().size(); k++)
            assertArrayEquals(expected.rows().get(k), actual.rows().get(k), 0.0, label + ", fila " + k);    // delta 0: exacto
        assertArrayEquals(expected.arrival(), actual.arrival(), 0.0, label);
    }

    private static Agent[] agents(PedestrianEvent e) {
        return new Agent[] { Agent.from(e, 0, Main.DEFAULT_V0_FRAMES), Agent.from(e, 1, Main.DEFAULT_V0_FRAMES) };
    }

    @Test
    void nullParameterGivesExactlyTheBaselineInTheNineteenEvents() throws IOException {
        List<PedestrianEvent> events = EventParser.parse(Path.of("data"));
        assertEquals(19, events.size());
        AvoidanceLayer[] nulls = { LateralTargetLayer.a(0.5, 0, C), LateralTargetLayer.a(5, 0, C), LateralTargetLayer.b(0.5, 0, C),
                LateralTargetLayer.b(5, 0, C), new RepulsiveDirectionLayer(0, 0.25, C), new RepulsiveDirectionLayer(0, 3, C) };
        for (PedestrianEvent e : events) {
            Simulation.Result base = BASE.run(agents(e), e.dtExp(), e.windowIntervals());
            for (AvoidanceLayer layer : nulls)
                assertSameRun(base, with(layer).run(agents(e), e.dtExp(), e.windowIntervals()), layer.label() + ", evento " + e.number());
        }
    }

    @Test
    void withoutPredictedCollisionTheRunIsIdentical() {
        // Se cruzan a 3 m: d_min = 3 > ρ. Parámetros bien distintos de cero
        Agent[] crossing = { new Agent(0, 0, 1, 0, 8, 0, 1.3), new Agent(8, 3, -1, 0, 0, 3, 1.3) };
        Simulation.Result base = BASE.run(crossing, DT_EXP, 120);
        for (AvoidanceLayer layer : new AvoidanceLayer[] { LateralTargetLayer.a(5, 2.5, C), LateralTargetLayer.b(5, 4, C), new RepulsiveDirectionLayer(0.9, 3, C) }) {
            MotionMonitor motion = new MotionMonitor();
            Simulation.Result run = with(layer).run(crossing, DT_EXP, 120, motion);
            assertSameRun(base, run, layer.label());
            assertEquals(0, motion.layerSwitches()[0] + motion.layerSwitches()[1], layer.label());
        }
    }

    @Test
    void mirroringTheEventSwapsTheDodgeSide() {
        // Fuera de los desempates: |s_c| > ε y, en F, |sin θ_j| = 0,116 > sen 5° desde el inicio
        Agent[] up = { new Agent(0, 0, 1.2, 0, 6, 0, 1.3), new Agent(6, 0.7, -1.2, 0, 0, 0.7, 1.3) };
        Agent[] down = { new Agent(0, 0, 1.2, 0, 6, 0, 1.3), new Agent(6, -0.7, -1.2, 0, 0, -0.7, 1.3) };
        for (AvoidanceLayer layer : new AvoidanceLayer[] { LateralTargetLayer.a(3, 1, C), LateralTargetLayer.b(3, 2, C), new RepulsiveDirectionLayer(0.6, 2, C) }) {
            Simulation.Result a = with(layer).run(up, DT_EXP, 120), b = with(layer).run(down, DT_EXP, 120);
            assertEquals(a.rows().size(), b.rows().size(), layer.label());
            double maxLateral = 0;
            for (int k = 0; k < a.rows().size(); k++) {
                double[] ra = a.rows().get(k), rb = b.rows().get(k);
                for (int c : new int[] { 1, 3, 5, 7 }) assertEquals(ra[c], rb[c], 1e-9, layer.label() + " x/vx, fila " + k);
                for (int c : new int[] { 2, 4, 6, 8 }) assertEquals(ra[c], -rb[c], 1e-9, layer.label() + " y/vy, fila " + k);
                if (!Double.isNaN(ra[2])) maxLateral = Math.max(maxLateral, Math.abs(ra[2]));
            }
            assertTrue(maxLateral > 0.05, layer.label() + " no esquivó: " + maxLateral);
        }
    }

    /** La banda angular original de F abarca desvíos laterales grandes de lejos, y ahí rompe la simetría. La métrica no. */
    @Test
    void angularBandBreaksTheMirrorFarAwayAndTheMetricTieDoesNot() {
        double[] up = new double[2], down = new double[2];
        AvoidanceLayer band = new RepulsiveDirectionLayer(0.6, 2, LayerConstants.of(C.rho(), 5, LayerConstants.FrontalTie.ANGULAR));
        band.direction(0, 0, 10, 0.5, -1.2, 0, 1.3, 1, 0, up);
        band.direction(0, 0, 10, -0.5, -1.2, 0, 1.3, 1, 0, down);
        assertTrue(up[1] < 0 && down[1] < 0, "los dos a la derecha: " + up[1] + ", " + down[1]);
        // Con el criterio métrico ya no es desempate: cada uno se aleja del otro
        AvoidanceLayer metric = new RepulsiveDirectionLayer(0.6, 2, C);
        metric.direction(0, 0, 10, 0.5, -1.2, 0, 1.3, 1, 0, up);
        metric.direction(0, 0, 10, -0.5, -1.2, 0, 1.3, 1, 0, down);
        assertEquals(up[1], -down[1], 1e-12);
        assertTrue(up[1] < 0 && down[1] > 0);
    }

    /** Sentido de la rotación: en la corrida completa, de frente exacto, cada peatón se corre a SU derecha. */
    @Test
    void headOnPedestriansDodgeToTheirOwnRight() {
        // i va por +x (su derecha es −y); j va por −x (su derecha es +y)
        Agent[] pair = { new Agent(0, 0, 1.2, 0, 10, 0, 1.3), new Agent(10, 0, -1.2, 0, 0, 0, 1.3) };
        for (AvoidanceLayer layer : new AvoidanceLayer[] { LateralTargetLayer.a(3, 1, C), LateralTargetLayer.b(3, 2, C), new RepulsiveDirectionLayer(0.6, 2, C) }) {
            Simulation.Result r = with(layer).run(pair, DT_EXP, 60);
            double[] last = r.rows().get(r.rows().size() - 1);
            assertTrue(last[2] < -0.01, layer.label() + ": el que va por +x tiene que correrse a −y: " + last[2]);
            assertTrue(last[6] > 0.01, layer.label() + ": el que va por −x tiene que correrse a +y: " + last[6]);
        }
    }

    @Test
    void observerDoesNotChangeTheRunAndSeesEveryStep() {
        Agent[] pair = { new Agent(0, 0, 1.2, 0, 10, 0, 1.3), new Agent(10, 0.3, -1.2, 0, 0, 0.3, 1.3) };
        Simulation sim = with(LateralTargetLayer.a(3, 1, C));
        long[] steps = { 0 };
        Simulation.Result observed = sim.run(pair, DT_EXP, 60, (step, t, r, v, active, on) -> steps[0]++);
        assertSameRun(sim.run(pair, DT_EXP, 60), observed, "con observador");
        assertEquals(60L * Simulation.DEFAULT_DT_DIV + 1, steps[0]);
    }

    /** Auditoría, ítem 3: e_t sale de la posición y no de la velocidad propia. */
    @Test
    void theOwnVelocityDoesNotChangeTheDirectionChosenByTheLayer() {
        Agent i = new Agent(0, 0, 0, 0, 10, 0, 1.3), j = new Agent(3, 0.4, 0, 0, 0, 0.4, 1.1);
        boolean[] active = { true, true };
        double[] r = { 0, 0, 3, 0.4 };
        for (AvoidanceLayer layer : new AvoidanceLayer[] { LateralTargetLayer.a(3, 1.5, C), LateralTargetLayer.b(3, 2, C), new RepulsiveDirectionLayer(0.8, 2, C) }) {
            double[] a1 = new double[4], a2 = new double[4];
            double[] v1 = { 1.3, 0, -1.1, 0 }, v2 = { 0.2, 0.9, -1.1, 0 };
            SfmField field = new SfmField(new Agent[] { i, j }, P, active, layer);
            field.acceleration(r, v1, a1);
            field.acceleration(r, v2, a2);
            assertEquals(a1[0] * P.tau() + v1[0], a2[0] * P.tau() + v2[0], 1e-12, layer.label());
            assertEquals(a1[1] * P.tau() + v1[1], a2[1] * P.tau() + v2[1], 1e-12, layer.label());
        }
    }

    @Test
    void afterCrossingEveryoneGoesBackToTheFinalTarget() {
        Agent[] pair = { new Agent(0, 0, 1.2, 0, 10, 0, 1.3), new Agent(10, 0.3, -1.2, 0, 0, 0.3, 1.3) };
        for (AvoidanceLayer layer : new AvoidanceLayer[] { LateralTargetLayer.a(3, 1, C), LateralTargetLayer.b(3, 2, C), new RepulsiveDirectionLayer(0.6, 2, C) }) {
            ContactMonitor withLayer = new ContactMonitor(SfmParameters.defaults().radius());
            ContactMonitor without = new ContactMonitor(SfmParameters.defaults().radius());
            MotionMonitor motion = new MotionMonitor();
            Simulation.Result r = with(layer).run(pair, DT_EXP, 400, MotionMonitor.all(withLayer, motion));
            BASE.run(pair, DT_EXP, 400, without);
            assertTrue(r.arrival()[0] > 0 && r.arrival()[1] > 0, layer.label() + " no llega al target");
            assertTrue(motion.layerSwitches()[0] >= 2, layer.label() + " tiene que prenderse y apagarse");
            assertTrue(withLayer.stats().minDistance() > without.stats().minDistance(), layer.label() + " no aumenta la distancia");
        }
    }

    @Test
    void theLayerOnlyChangesTheDirectionOfTheDesiredVelocity() {
        // Sin contacto, |a τ + v| = v_d en cualquier estado: el módulo sigue siendo la rapidez media
        Agent i = new Agent(0, 0, 0, 0, 10, 0, 1.3), j = new Agent(3, 0.4, 0, 0, 0, 0.4, 1.1);
        boolean[] active = { true, true };
        double[] r = { 0, 0, 3, 0.4 }, v = { 0.7, 0.2, -1.1, 0 }, a = new double[4];
        for (AvoidanceLayer layer : new AvoidanceLayer[] { LateralTargetLayer.a(3, 1.5, C), LateralTargetLayer.b(3, 2, C), new RepulsiveDirectionLayer(0.8, 2, C) }) {
            new SfmField(new Agent[] { i, j }, P, active, layer).acceleration(r, v, a);
            double dvx = a[0] * P.tau() + v[0], dvy = a[1] * P.tau() + v[1];
            assertEquals(1.3, Math.hypot(dvx, dvy), 1e-12, layer.label());
            assertTrue(Math.abs(dvy) > 1e-3, layer.label() + " no cambió la dirección");
        }
    }

    @Test
    void retiredOtherAgentTurnsTheLayerOff() {
        Agent i = new Agent(0, 0, 0, 0, 10, 0, 1.3), j = new Agent(3, 0.4, 0, 0, 0, 0.4, 1.1);
        double[] r = { 0, 0, 3, 0.4 }, v = { 0.7, 0, -1.1, 0 }, a = new double[4];
        new SfmField(new Agent[] { i, j }, P, new boolean[] { true, false }, LateralTargetLayer.a(3, 1.5, C)).acceleration(r, v, a);
        assertEquals(0, a[1] * P.tau() + v[1], 1e-12);
    }

    @Test
    void layerNoneReportsNoSwitches() {
        MotionMonitor motion = new MotionMonitor();
        BASE.run(new Agent[] { new Agent(0, 0, 1, 0, 5, 0, 1.3), new Agent(5, 0.2, -1, 0, 0, 0.2, 1.3) }, DT_EXP, 80, motion);
        assertEquals(0, motion.layerSwitches()[0] + motion.layerSwitches()[1]);
        assertFalse(AvoidanceLayer.NONE.direction(0, 0, 1, 0, -1, 0, 1, 1, 0, new double[2]));
    }
}
