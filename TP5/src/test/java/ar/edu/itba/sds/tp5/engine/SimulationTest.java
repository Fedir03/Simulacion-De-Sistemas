package ar.edu.itba.sds.tp5.engine;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.analysis.ContactMonitor;
import ar.edu.itba.sds.tp5.analysis.MotionMonitor;
import org.junit.jupiter.api.Test;

class SimulationTest {
    private static final double DT_EXP = 1 / 15.0192;
    private static final Simulation SIM = new Simulation(SfmParameters.defaults(), Integrator.DEFAULT, Simulation.DEFAULT_DT_DIV);

    /** Dos peatones en carriles lejanos: cada uno llega a su target sin interactuar. */
    private static Agent[] parallelLanes() {
        return new Agent[] { new Agent(0, 0, 1, 0, 5, 0, 1.3), new Agent(5, 10, -1, 0, 0, 10, 1.3) };
    }

    @Test
    void outputRowsFallOnEverySecondTimeStepOfTheExperiment() {
        Simulation.Result r = SIM.run(new Agent[] { new Agent(0, 0, 1, 0, 1000, 0, 1), new Agent(0, 5, 1, 0, 1000, 5, 1) }, DT_EXP, 10);
        assertEquals(10 * 4 + 1, r.rows().size());
        for (int k = 0; k <= 10; k++) assertEquals(k * DT_EXP, r.rows().get(4 * k)[0], 1e-12);
        assertEquals(9, r.rows().get(0).length);
    }

    @Test
    void outputStrideScalesWithTheTimeStep() {
        assertEquals(4, new Simulation(SfmParameters.defaults(), Integrator.DEFAULT, 16).outputEvery());
        assertEquals(16, SIM.outputEvery());
        assertEquals(16, new Simulation(SfmParameters.defaults(), Integrator.DEFAULT, 64).outputEvery());
        assertThrows(IllegalArgumentException.class, () -> new Simulation(SfmParameters.defaults(), Integrator.DEFAULT, 30));
    }

    @Test
    void pedestriansWithoutCrossingReachTheTargetAndLeave() {
        ContactMonitor contacts = new ContactMonitor(SfmParameters.defaults().radius());
        MotionMonitor motion = new MotionMonitor();
        Simulation.Result r = SIM.run(parallelLanes(), DT_EXP, 200, MotionMonitor.all(contacts, motion));
        assertFalse(contacts.stats().anyContact());
        for (int i = 0; i < 2; i++) {
            assertTrue(r.arrival()[i] > 0);
            // Va casi recto: no da vueltas alrededor del target
            assertTrue(motion.pathLength()[i] < 5, "agente " + i + " recorrió " + motion.pathLength()[i]);
        }
    }

    @Test
    void retiredPedestrianIsNaNAndTheRunEndsWhenEveryoneLeaves() {
        Simulation.Result r = SIM.run(parallelLanes(), DT_EXP, 200);
        double last = Math.max(r.arrival()[0], r.arrival()[1]);
        assertTrue(r.rows().size() < 200 * 4 + 1);
        assertTrue(r.rows().get(r.rows().size() - 1)[0] <= last + 1e-9);
        boolean sawFinite = false;
        for (double[] row : r.rows()) {
            if (row[0] >= r.arrival()[0]) assertTrue(Double.isNaN(row[1]) && Double.isNaN(row[3]));
            else { assertFalse(Double.isNaN(row[1])); sawFinite = true; }
        }
        assertTrue(sawFinite);
    }

    @Test
    void obliqueStartStillReachesTheTargetWithoutOrbiting() {
        Agent[] agents = { new Agent(0, 0, 0, 2, 3, 0, 1), new Agent(50, 50, 0, 0, 50, 49, 1) };
        MotionMonitor motion = new MotionMonitor();
        Simulation.Result r = SIM.run(agents, DT_EXP, 300, motion);
        assertTrue(r.arrival()[0] > 0);
        assertTrue(motion.pathLength()[0] < 5, "recorrió " + motion.pathLength()[0]);
    }

    @Test
    void deltaAIsConfigurable() {
        Simulation near = new Simulation(SfmParameters.withDeltaA(0.05), Integrator.DEFAULT, Simulation.DEFAULT_DT_DIV);
        Simulation far = new Simulation(SfmParameters.withDeltaA(0.5), Integrator.DEFAULT, Simulation.DEFAULT_DT_DIV);
        assertTrue(far.run(parallelLanes(), DT_EXP, 200).arrival()[0] < near.run(parallelLanes(), DT_EXP, 200).arrival()[0]);
    }

    @Test
    void headOnPairTouchesAndRepels() {
        Agent[] agents = { new Agent(0, 0, 1.3, 0, 8, 0.05, 1.3), new Agent(8, 0.05, -1.3, 0, 0, 0, 1.3) };
        ContactMonitor contacts = new ContactMonitor(SfmParameters.defaults().radius());
        SIM.run(agents, DT_EXP, 120, contacts);
        ContactMonitor.Stats s = contacts.stats();
        assertTrue(s.anyContact());
        assertTrue(s.minDistance() > 0.4 && s.minDistance() < 0.5, "d_min = " + s.minDistance());
    }

    @Test
    void sameInputGivesTheSameRun() {
        Simulation.Result a = SIM.run(parallelLanes(), DT_EXP, 40), b = SIM.run(parallelLanes(), DT_EXP, 40);
        for (int k = 0; k < a.rows().size(); k++) org.junit.jupiter.api.Assertions.assertArrayEquals(a.rows().get(k), b.rows().get(k));
    }
}
