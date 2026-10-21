package ar.edu.itba.sds.tp4.engine.billiard;

import ar.edu.itba.sds.tp4.engine.billiard.BilliardSimulator.Frame;
import ar.edu.itba.sds.tp4.engine.billiard.BilliardSimulator.Summary;
import ar.edu.itba.sds.tp4.models.BilliardConfig;
import org.junit.jupiter.api.Test;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class BilliardSimulatorTest {
    private static final double M = 0.025;

    /** Copia de un cuadro (el simulador reutiliza sus arreglos). */
    private record Snap(double t, double[] x, double[] y, double[] vx, double[] vy, boolean[] used, int nu, double eKin, double eEl) {
        static Snap of(Frame f) {
            return new Snap(f.time(), f.x().clone(), f.y().clone(), f.vx().clone(), f.vy().clone(), f.used().clone(),
                    f.usedCount(), f.kineticEnergy(), f.elasticEnergy());
        }
        double eTot() { return eKin + eEl; }
    }

    private static List<Snap> run(BilliardSimulator sim) throws IOException {
        List<Snap> frames = new ArrayList<>();
        Summary s = sim.run(f -> frames.add(Snap.of(f)));
        assertEquals(BilliardSimulator.Status.COMPLETED, s.status());
        return frames;
    }

    private static BilliardSimulator explicit(BilliardConfig c, double[] x, double[] y, double[] vx, double[] vy) {
        return new BilliardSimulator(c, x, y, vx, vy, BilliardSimulator.defaultFinder(c));
    }

    @Test void singleParticleKeepsSpeedAngularMomentumAndEnergyThroughWallBounces() throws IOException {
        // dt2 = 1 ms para que caigan cuadros dentro de los choques con la pared (~5 ms)
        BilliardConfig c = BilliardConfig.of(1, 1, BilliardConfig.NO_OBSTACLES, 1e-5, 1e-3, 2);
        double vx = Math.cos(0.3), vy = Math.sin(0.3);
        List<Snap> frames = run(explicit(c, new double[]{0}, new double[]{0.1}, new double[]{vx}, new double[]{vy}));
        double e0 = 0.5 * M, l0 = M * (0 * vy - 0.1 * vx);
        int inContact = 0, bounces = 0;
        for (int i = 0; i < frames.size(); i++) {
            Snap f = frames.get(i);
            // La pared es radial: no hace torque
            assertEquals(l0, M * (f.x[0] * f.vy[0] - f.y[0] * f.vx[0]), 1e-6 * Math.abs(l0), "L en t=" + f.t);
            // Energía total (cinética + elástica de la pared, contada una vez) igual antes, durante y después del choque
            assertEquals(e0, f.eTot(), 1e-3 * e0, "E en t=" + f.t);
            if (f.eEl > 0) {
                inContact++;
                if (frames.get(i - 1).eEl == 0) bounces++;
            } else assertEquals(1, Math.hypot(f.vx[0], f.vy[0]), 1e-4, "|v| en t=" + f.t);
        }
        assertTrue(bounces >= 2, "rebotes: " + bounces);
        assertTrue(inContact > bounces, "cuadros en contacto: " + inContact);
        assertEquals(e0, frames.getLast().eTot(), 1e-4 * e0);
    }

    @Test void headOnCollisionConservesMomentumAndEnergyAndSwapsVelocities() throws IOException {
        BilliardConfig c = BilliardConfig.of(2, 1, BilliardConfig.NO_OBSTACLES, 1e-5, 0.01, 0.15);
        List<Snap> frames = run(explicit(c, new double[]{-0.1, 0.1}, new double[]{0.05, 0.05},
                new double[]{1, -1}, new double[]{0, 0}));
        double e0 = M; // 2 · ½·m·1²
        for (Snap f : frames) {
            assertEquals(0, f.vx[0] + f.vx[1], 1e-9, "p_x en t=" + f.t);
            assertEquals(0, f.vy[0] + f.vy[1], 1e-9, "p_y en t=" + f.t);
            assertEquals(e0, f.eTot(), 1e-3 * e0, "E en t=" + f.t);
        }
        Snap last = frames.getLast();
        assertEquals(-1, last.vx[0], 1e-4); assertEquals(1, last.vx[1], 1e-4);
        assertEquals(0, last.vy[0], 1e-12); assertEquals(0, last.vy[1], 1e-12);
        assertEquals(e0, last.eTot(), 1e-4 * e0);
    }

    @Test void freshToUsedIsIrreversibleAndNuNeverDecreases() throws IOException {
        BilliardConfig c = BilliardConfig.of(2, 1, 0.2, 1e-5, 0.01, 2);
        // 0 va y vuelve entre los dos obstáculos sobre y = 0; 1 quieta lejos de todo
        List<Snap> frames = run(explicit(c, new double[]{0, 0}, new double[]{0, 0.3}, new double[]{1, 0}, new double[]{0, 0}));
        assertEquals(0, frames.getFirst().nu);
        boolean seenUsed = false;
        for (int i = 0; i < frames.size(); i++) {
            Snap f = frames.get(i);
            if (i > 0) assertTrue(f.nu >= frames.get(i - 1).nu);
            if (seenUsed) assertTrue(f.used[0], "volvió a fresca en t=" + f.t);
            seenUsed |= f.used[0];
            assertFalse(f.used[1]);
            int count = 0;
            for (boolean u : f.used) if (u) count++;
            assertEquals(count, f.nu);
        }
        assertTrue(seenUsed);
        assertEquals(1, frames.getLast().nu);
        // Primer contacto con el obstáculo derecho cerca de t = (0,2 − 2r)/v0 = 0,165 s
        double tUsed = frames.stream().filter(f -> f.used[0]).findFirst().orElseThrow().t;
        assertEquals(0.17, tUsed, 1e-9);
    }

    @Test void untilAllUsedStopsAtFirstFrameWithNuEqualN() throws IOException {
        BilliardConfig c = BilliardConfig.of(2, 1, 0.2, 1e-5, 0.01, 2);
        // Cada una va hacia su obstáculo sobre y = 0: contacto cuando 0,2 − 0,05 − t < 2r, es decir t > 0,115 s
        List<Double> times = new ArrayList<>();
        Summary s = explicit(c, new double[]{0.05, -0.05}, new double[]{0, 0}, new double[]{1, -1}, new double[]{0, 0})
                .run(f -> times.add(f.time()), true);
        assertEquals(BilliardSimulator.Status.ALL_USED, s.status());
        assertEquals(2, s.usedCount());
        assertEquals(0.12, s.time(), 1e-9);
        assertEquals(0.12, times.getLast(), 1e-9);
    }

    @Test void gridInitialConditionHasNoContactsAndExactInitialSpeed() throws IOException {
        for (double x0 : new double[]{0.0175, BilliardConfig.NO_OBSTACLES}) {
            int n = Double.isNaN(x0) ? 721 : 714; // N máx de D6
            BilliardConfig c = BilliardConfig.of(n, 3, x0, 1e-4, 1e-4, 1e-4);
            Snap f0 = run(BilliardSimulator.fromGrid(c, BilliardSimulator.defaultFinder(c))).getFirst();
            // F(0) = 0: el primer paso por Euler en −Δt es exacto (Q6)
            assertEquals(0, f0.eEl);
            assertEquals(0, f0.nu);
            for (int i = 0; i < n; i++) assertEquals(1, Math.hypot(f0.vx[i], f0.vy[i]), 1e-12);
            assertEquals(n * 0.5 * M, f0.eKin, 1e-12);
        }
    }

    @Test void unstableRunStopsWithDivergenceInsteadOfThrowing() throws IOException {
        BilliardConfig c = BilliardConfig.of(1, 1, BilliardConfig.NO_OBSTACLES, 1e-2, 0.01, 1);
        List<Double> times = new ArrayList<>();
        Summary s = explicit(c, new double[]{0}, new double[]{0}, new double[]{100}, new double[]{0}).run(f -> times.add(f.time()));
        assertEquals(BilliardSimulator.Status.DIVERGED, s.status());
        assertEquals(0.01, s.time(), 1e-15);
        assertEquals(List.of(0.0), times);
    }

    @Test void outputsOnlyAtMultiplesOfDt2IncludingZeroAndTf() throws IOException {
        BilliardConfig c = BilliardConfig.of(50, 1, 0.24, 1e-4, 0.04, 1);
        List<Snap> frames = run(BilliardSimulator.fromGrid(c, BilliardSimulator.defaultFinder(c)));
        assertEquals(26, frames.size());
        for (int i = 0; i < frames.size(); i++) assertEquals(i * 400 * 1e-4, frames.get(i).t, 1e-12);
    }

    @Test void sameSeedSameTrajectoryOtherSeedOther() throws IOException {
        BilliardConfig a = BilliardConfig.of(100, 7, 0.24, 1e-4, 0.04, 0.4);
        BilliardConfig b = BilliardConfig.of(100, 8, 0.24, 1e-4, 0.04, 0.4);
        List<Snap> r1 = run(BilliardSimulator.fromGrid(a, BilliardSimulator.defaultFinder(a)));
        List<Snap> r2 = run(BilliardSimulator.fromGrid(a, BilliardSimulator.defaultFinder(a)));
        List<Snap> r3 = run(BilliardSimulator.fromGrid(b, BilliardSimulator.defaultFinder(b)));
        for (int i = 0; i < r1.size(); i++) {
            assertArrayEquals(r1.get(i).x, r2.get(i).x);
            assertArrayEquals(r1.get(i).vy, r2.get(i).vy);
            assertEquals(r1.get(i).eTot(), r2.get(i).eTot());
        }
        assertFalse(java.util.Arrays.equals(r1.getLast().x, r3.getLast().x));
    }
}
