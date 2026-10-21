package ar.edu.itba.sds.tp4.engine.billiard;

import ar.edu.itba.sds.tp4.engine.cim.BruteForceNeighborFinder;
import ar.edu.itba.sds.tp4.engine.cim.NeighborFinder;
import ar.edu.itba.sds.tp4.models.BilliardConfig;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class ContactForcesTest {
    private static final double R = 0.51, r = 0.0175, K = 1e4, DELTA = 1e-3;

    private static BilliardConfig config(int n, double x0) { return BilliardConfig.of(n, 1, x0, 1e-4, 0.04, 1); }

    /** Fuerzas con CIM y con fuerza bruta; deben coincidir. Devuelve {fx, fy} del CIM. */
    private static double[][] forces(BilliardConfig c, double[] x, double[] y, boolean[] used, double expectedElastic) {
        double[][] out = null;
        for (NeighborFinder finder : new NeighborFinder[]{BilliardSimulator.defaultFinder(c), new BruteForceNeighborFinder()}) {
            double[] fx = new double[x.length], fy = new double[x.length];
            ContactForces.Result res = new ContactForces(c, finder).compute(x, y, fx, fy, used.clone());
            assertEquals(expectedElastic, res.elasticEnergy(), 1e-15);
            if (out == null) out = new double[][]{fx, fy};
            else { assertArrayEquals(out[0], fx, 1e-12); assertArrayEquals(out[1], fy, 1e-12); }
        }
        return out;
    }

    @Test void wallContactOnlyBeyondRMinusRAndPointsInward() {
        BilliardConfig c = config(1, BilliardConfig.NO_OBSTACLES);
        // Dirección del tercer cuadrante (x<0, y<0)
        double nx = -0.6, ny = -0.8;
        double[][] f = forces(c, new double[]{nx * (R - r - 1e-9)}, new double[]{ny * (R - r - 1e-9)}, new boolean[1], 0);
        assertEquals(0, f[0][0]); assertEquals(0, f[1][0]);

        double d = R - r + DELTA;
        f = forces(c, new double[]{nx * d}, new double[]{ny * d}, new boolean[1], 0.5 * K * DELTA * DELTA);
        // F = −k·ξ·n̂ con ξ = |r| + r − R = DELTA: radial hacia el centro
        assertEquals(-K * DELTA * nx, f[0][0], 1e-9);
        assertEquals(-K * DELTA * ny, f[1][0], 1e-9);
    }

    @Test void pairForceIsRepulsiveEqualAndOppositeInNegativeQuadrant() {
        BilliardConfig c = config(2, BilliardConfig.NO_OBSTACLES);
        double ex = Math.sqrt(0.5), ey = Math.sqrt(0.5), d = 2 * r - DELTA;
        double[] x = {-0.2, -0.2 + d * ex}, y = {-0.3, -0.3 + d * ey};
        double[][] f = forces(c, x, y, new boolean[2], 0.5 * K * DELTA * DELTA);
        assertEquals(-K * DELTA * ex, f[0][0], 1e-9); assertEquals(-K * DELTA * ey, f[1][0], 1e-9);
        assertEquals(-f[0][0], f[0][1], 1e-12); assertEquals(-f[1][0], f[1][1], 1e-12);

        // Separadas: sin fuerza ni energía
        x[1] = -0.2 + (2 * r + DELTA) * ex; y[1] = -0.3 + (2 * r + DELTA) * ey;
        f = forces(c, x, y, new boolean[2], 0);
        for (double[] comp : f) assertArrayEquals(new double[2], comp);
    }

    @Test void obstacleContactPushesAwayAndMarksUsedOnce() {
        BilliardConfig c = config(3, 0.2);
        // 0: solapa el obstáculo izquierdo desde la izquierda; 1: a 1e-9 m del derecho (ξ < 0); 2: lejos
        double[] x = {-0.2 - (2 * r - DELTA), 0.2 + 2 * r + 1e-9, 0}, y = {0, 0, 0.3};
        boolean[] used = new boolean[3];
        double[] fx = new double[3], fy = new double[3];
        ContactForces cf = new ContactForces(c, BilliardSimulator.defaultFinder(c));
        ContactForces.Result res = cf.compute(x, y, fx, fy, used);
        assertEquals(1, res.newlyUsed());
        assertArrayEquals(new boolean[]{true, false, false}, used);
        assertEquals(-K * DELTA, fx[0], 1e-9);
        assertEquals(0.5 * K * DELTA * DELTA, res.elasticEnergy(), 1e-15);
        assertEquals(0, fx[1]);

        // Se aleja: sigue usada y no se vuelve a contar
        x[0] = -0.4;
        res = cf.compute(x, y, fx, fy, used);
        assertEquals(0, res.newlyUsed());
        assertTrue(used[0]);
        x[0] = -0.2 - (2 * r - DELTA);
        assertEquals(0, cf.compute(x, y, fx, fy, used).newlyUsed());
    }

    @Test void configRequiresIntegerOutputAndStepCounts() {
        double[] dts = {1e-2, 1e-3, 1e-4, 1e-5, 1e-6};
        int[] expected = {4, 40, 400, 4000, 40000};
        for (int i = 0; i < dts.length; i++)
            assertEquals(expected[i], BilliardConfig.of(300, 1, BilliardConfig.NO_OBSTACLES, dts[i], 0.04, 30).outputEvery());
        assertEquals(300_000, BilliardConfig.of(300, 1, BilliardConfig.NO_OBSTACLES, 1e-4, 0.04, 30).totalSteps());
        assertThrows(IllegalArgumentException.class, () -> BilliardConfig.of(300, 1, BilliardConfig.NO_OBSTACLES, 3e-3, 0.04, 30));
        assertThrows(IllegalArgumentException.class, () -> BilliardConfig.of(300, 1, BilliardConfig.NO_OBSTACLES, 1e-4, 0.04, 30.01));
        assertThrows(IllegalArgumentException.class, () -> BilliardConfig.of(300, 1, 0.01, 1e-4, 0.04, 30));
        assertThrows(IllegalArgumentException.class, () -> BilliardConfig.of(300, 1, 0.5, 1e-4, 0.04, 30));
        assertThrows(IllegalArgumentException.class, () -> BilliardConfig.of(0, 1, BilliardConfig.NO_OBSTACLES, 1e-4, 0.04, 30));
        // Los extremos del enunciado son válidos
        BilliardConfig.of(1, 1, r, 1e-4, 0.04, 30);
        BilliardConfig.of(1, 1, R - r, 1e-4, 0.04, 30);
    }
}
