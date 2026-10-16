package ar.edu.itba.sds.tp4.engine.oscillator;

import ar.edu.itba.sds.tp4.Main;
import ar.edu.itba.sds.tp4.engine.oscillator.IntegrationOptions.*;
import ar.edu.itba.sds.tp4.models.Oscillator;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.*;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class OscillatorTest {
    @TempDir Path temp;
    private static final Oscillator O = Oscillator.defaults();
    private static final IntegrationOptions D = IntegrationOptions.defaults();

    /** Pendiente de log(ECM) vs log(dt) entre dos pasos. */
    private static double slope(Scheme s, IntegrationOptions opt, double dtLarge, double dtSmall) {
        double e1 = OscillatorStudy.run(O, s, dtLarge, opt).ecm(), e2 = OscillatorStudy.run(O, s, dtSmall, opt).ecm();
        return Math.log(e1 / e2) / Math.log(dtLarge / dtSmall);
    }

    @Test void analyticSolutionMatchesInitialConditionAndDecays() {
        assertEquals(1, O.analytic(0), 1e-15);
        assertEquals(-100.0 / 140, O.v0(), 1e-15);
        double h = 1e-7; // derivada numérica en t = 0 coincide con v(0)
        assertEquals(O.v0(), (O.analytic(h) - O.analytic(-h)) / (2 * h), 1e-6);
        assertTrue(Math.abs(O.analytic(5)) < Math.exp(-100 * 5 / 140.0) + 1e-12);
    }

    @Test void everySchemeReproducesAnalyticSolutionAtSmallDt() {
        double dt = 1e-5;
        int steps = OscillatorStudy.steps(O, dt);
        for (Scheme s : Scheme.values()) {
            double[] x = s.integrate(O, dt, steps, D);
            double max = 0;
            for (int n = 0; n <= steps; n++) max = Math.max(max, Math.abs(x[n] - O.analytic(n * dt)));
            assertTrue(max < 1e-3, s + ": error máximo " + max);
        }
    }

    @Test void ecmSlopesMatchExpectedOrderWithDefaultOptions() {
        // ECM ∝ dt^(2p) con p el orden global en posición.
        assertEquals(4, slope(Scheme.BEEMAN, D, 1e-3, 1e-4), 0.1);
        assertEquals(4, slope(Scheme.VELOCITY_VERLET, D, 1e-3, 1e-4), 0.1);
        // v(t) hacia atrás es O(dt): degrada a Verlet a primer orden con esta fuerza.
        assertEquals(2, slope(Scheme.VERLET, D, 1e-3, 1e-4), 0.1);
        assertEquals(2, slope(Scheme.EULER_PC, D, 1e-3, 1e-4), 0.1);
    }

    @Test void velocityEstimateChangesVerletOrder() {
        var euler = new IntegrationOptions(VerletVelocity.EULER, PredictedVelocity.EULER, AccelerationUpdate.PREDICTED);
        assertEquals(4, slope(Scheme.VERLET, euler, 1e-3, 1e-4), 0.1);
        var halfStep = new IntegrationOptions(VerletVelocity.BACKWARD, PredictedVelocity.HALF_STEP, AccelerationUpdate.PREDICTED);
        assertEquals(2, slope(Scheme.VELOCITY_VERLET, halfStep, 1e-3, 1e-4), 0.1);
    }

    @Test void verletAndVelocityVerletCoincideWithoutDamping() {
        Oscillator undamped = new Oscillator(70, 1e4, 0, 1, 5);
        double dt = 1e-3;
        int steps = OscillatorStudy.steps(undamped, dt);
        double[] a = Scheme.VERLET.integrate(undamped, dt, steps, D), b = Scheme.VELOCITY_VERLET.integrate(undamped, dt, steps, D);
        // Con r(−dt) por Euler, x(dt) de Verlet es el de Velocity Verlet; sin γ, las trayectorias son la misma.
        for (int n = 0; n <= steps; n++) assertEquals(a[n], b[n], 1e-9);
    }

    @Test void defaultOptionsAreTheAgreedOnes() {
        assertEquals(VerletVelocity.BACKWARD, D.verletVelocity());
        assertEquals(PredictedVelocity.EULER, D.velocityVerletPrediction());
        assertEquals(AccelerationUpdate.PREDICTED, D.accelerationUpdate());
        assertEquals(PredictedVelocity.HALF_STEP, IntegrationOptions.parse(PredictedVelocity.class, "half-step"));
        assertThrows(IllegalArgumentException.class, () -> IntegrationOptions.parse(VerletVelocity.class, "central"));
    }

    @Test void rejectsInvalidInput() {
        assertThrows(IllegalArgumentException.class, () -> Scheme.BEEMAN.integrate(O, 0, 10, D));
        assertThrows(IllegalArgumentException.class, () -> Scheme.BEEMAN.integrate(O, -1e-3, 10, D));
        assertThrows(IllegalArgumentException.class, () -> new Oscillator(70, 1e4, 1e5, 1, 5));
        assertThrows(IllegalArgumentException.class, () -> OscillatorStudy.logSpaced(1e-3, 1e-4, 5));
        assertThrows(IllegalArgumentException.class, () -> Main.execute(new String[]{"oscillator-ecm", "--dt", "1e-3"}));
    }

    @Test void logSpacedSweepHitsBothEnds() {
        double[] dts = OscillatorStudy.logSpaced(1e-6, 5e-3, 13);
        assertEquals(5e-3, dts[0], 1e-15);
        assertEquals(1e-6, dts[12], 1e-18);
        for (int i = 1; i < dts.length; i++) assertTrue(dts[i] < dts[i - 1]);
    }

    @Test void cliWritesOneRowPerSchemeAndDt() throws Exception {
        Path out = temp.resolve("ecm.txt");
        Main.execute(new String[]{"oscillator-ecm", "--dts", "1e-3,1e-4", "--out", out.toString()});
        List<String> rows = Files.readAllLines(out).stream().filter(l -> !l.startsWith("#")).toList();
        assertEquals("scheme dt steps ecm runtime_s", rows.get(0));
        assertEquals(1 + 2 * Scheme.values().length, rows.size());
    }
}
