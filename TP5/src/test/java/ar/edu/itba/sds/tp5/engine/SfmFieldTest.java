package ar.edu.itba.sds.tp5.engine;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class SfmFieldTest {
    private static final SfmParameters P = SfmParameters.defaults();
    private static final double M = P.mass();

    /** Sin rapidez deseada, para aislar el contacto. */
    private static final Agent STILL = new Agent(0, 0, 0, 0, 100, 0, 0);

    private static double[] accelerations(Agent[] agents, boolean[] active, double[] r, double[] v) {
        double[] a = new double[r.length];
        new SfmField(agents, P, active).acceleration(r, v, a);
        return a;
    }

    private static double[] contact(double[] r, double[] v) {
        // Se le resta la relajación (−v/τ), que acá no se quiere medir
        double[] a = accelerations(new Agent[] { STILL, STILL }, new boolean[] { true, true }, r, v);
        for (int k = 0; k < a.length; k++) a[k] += v[k] / P.tau();
        return a;
    }

    @Test
    void drivingForcePointsToTheTargetWithDesiredSpeed() {
        Agent agent = new Agent(0, 0, 0, 0, 3, 4, 1.5);
        double[] a = accelerations(new Agent[] { agent }, new boolean[] { true }, new double[] { 0, 0 }, new double[] { 0.5, 0 });
        assertEquals((1.5 * 0.6 - 0.5) / P.tau(), a[0], 1e-12);
        assertEquals(1.5 * 0.8 / P.tau(), a[1], 1e-12);
    }

    @Test
    void noContactForceWithoutOverlap() {
        double[] a = contact(new double[] { 0, 0, 0.5, 0 }, new double[] { 1, 2, -1, 3 });
        for (double c : a) assertEquals(0, c, 1e-12);
    }

    @Test
    void normalForceRepelsWithTheExpectedMagnitude() {
        double overlap = 0.01;
        double[] a = contact(new double[] { 0, 0, 0.5 - overlap, 0 }, new double[4]);
        assertEquals(-P.kn() * overlap / M, a[0], 1e-9);    // i está a la izquierda: lo empuja hacia −x
        assertEquals(P.kn() * overlap / M, a[2], 1e-9);
        assertEquals(0, a[1], 1e-12);
        assertEquals(0, a[3], 1e-12);
    }

    @Test
    void tangentialForceOpposesTheRelativeSlidingVelocity() {
        double overlap = 0.01, slip = 0.5;
        double[] a = contact(new double[] { 0, 0, 0.5 - overlap, 0 }, new double[] { 0, slip, 0, 0 });
        assertEquals(-P.kt() * overlap * slip / M, a[1], 1e-9);
        assertEquals(P.kt() * overlap * slip / M, a[3], 1e-9);
    }

    @Test
    void contactForceFollowsActionAndReaction() {
        double[] a = contact(new double[] { 0.1, 0.2, 0.4, 0.45 }, new double[] { 1, -0.5, -0.3, 0.7 });
        assertTrue(Math.abs(a[0]) > 0);
        assertEquals(-a[0], a[2], 1e-9);
        assertEquals(-a[1], a[3], 1e-9);
    }

    @Test
    void retiredAgentNeitherFeelsNorExertsForce() {
        Agent walker = new Agent(0, 0, 0, 0, 100, 0, 1);
        double[] r = { 0, 0, 0.4, 0 };
        double[] a = accelerations(new Agent[] { walker, walker }, new boolean[] { true, false }, r, new double[4]);
        assertEquals(1 / P.tau(), a[0], 1e-12);             // solo la driving force
        assertEquals(0, a[2]);
        assertEquals(0, a[3]);
    }
}
