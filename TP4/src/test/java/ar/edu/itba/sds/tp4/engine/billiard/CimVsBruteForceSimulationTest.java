package ar.edu.itba.sds.tp4.engine.billiard;

import ar.edu.itba.sds.tp4.engine.cim.BruteForceNeighborFinder;
import ar.edu.itba.sds.tp4.engine.cim.CellIndexMethod;
import ar.edu.itba.sds.tp4.engine.cim.NeighborFinder;
import ar.edu.itba.sds.tp4.engine.cim.Particle;
import ar.edu.itba.sds.tp4.models.BilliardConfig;
import org.junit.jupiter.api.Test;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.function.Function;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Prueba de simulación completa del paso 04: la misma simulación (misma semilla, mismo estado inicial) con CIM y con
 * fuerza bruta. Se compara (1) el conjunto de pares en contacto en cada paso, (2) posiciones y velocidades en los
 * primeros 1000 pasos y (3) la energía y Nu en toda la corrida. Casos (a) N=300 sin obstáculos, (b) N máx = 714 con
 * x0=r, (c) anillo contra la pared + racimo superpuesto en x<0, y<0; cada uno con M = 29 (máximo) y M = 7 (grueso).
 */
class CimVsBruteForceSimulationTest {
    private static final double R = 0.51, r = 0.0175;
    private static final int[] MS = {29, 7};
    /** dt2 = 10·dt: un cuadro cada 10 pasos; 100 cuadros = primeros 1000 pasos. */
    private static final double DT = 1e-4, DT2 = 1e-3;
    private static final int CLOSE_FRAMES = 100;

    /** Registra los pares de cada llamada (clave i·N + j con i < j, ordenadas) y el tiempo de la búsqueda. */
    private static final class Recording implements NeighborFinder {
        final NeighborFinder inner;
        final List<long[]> pairs = new ArrayList<>();
        long nanos;
        Recording(NeighborFinder inner) { this.inner = inner; }

        @Override public Map<Integer, Set<Integer>> findNeighbors(List<Particle> particles, double l, double rc, boolean periodic) {
            long start = System.nanoTime();
            Map<Integer, Set<Integer>> result = inner.findNeighbors(particles, l, rc, periodic);
            nanos += System.nanoTime() - start;
            int n = particles.size();
            List<Long> keys = new ArrayList<>();
            for (var e : result.entrySet())
                for (int j : e.getValue()) {
                    assertTrue(result.get(j).contains(e.getKey()), "vecindad no simétrica");
                    if (e.getKey() < j) keys.add((long) e.getKey() * n + j);
                }
            long[] sorted = keys.stream().mapToLong(Long::longValue).sorted().toArray();
            pairs.add(sorted);
            return result;
        }
    }

    private record Frame(double t, double[] x, double[] y, double[] vx, double[] vy, int nu, double e) { }
    private record Run(List<Frame> frames, Recording finder, long wallNanos) { }

    private static Run run(Function<NeighborFinder, BilliardSimulator> build, NeighborFinder finder) throws IOException {
        Recording rec = new Recording(finder);
        BilliardSimulator sim = build.apply(rec);
        List<Frame> frames = new ArrayList<>();
        long start = System.nanoTime();
        BilliardSimulator.Summary s = sim.run(f -> frames.add(new Frame(f.time(), f.x().clone(), f.y().clone(),
                f.vx().clone(), f.vy().clone(), f.usedCount(), f.totalEnergy())));
        long wall = System.nanoTime() - start;
        assertEquals(BilliardSimulator.Status.COMPLETED, s.status());
        return new Run(frames, rec, wall);
    }

    private static void compare(String name, Function<NeighborFinder, BilliardSimulator> build) throws IOException {
        Run brute = run(build, new BruteForceNeighborFinder());
        for (int m : MS) {
            Run cim = run(build, CellIndexMethod.forCircle(m, R));
            String c = name + " M=" + m;
            // (1) mismos pares en contacto en cada paso
            assertEquals(brute.finder.pairs.size(), cim.finder.pairs.size(), c + ": cantidad de pasos");
            long totalPairs = 0;
            for (int step = 0; step < brute.finder.pairs.size(); step++) {
                assertArrayEquals(brute.finder.pairs.get(step), cim.finder.pairs.get(step), c + ": pares en el paso " + step);
                totalPairs += brute.finder.pairs.get(step).length;
            }
            assertTrue(totalPairs > 0, c + ": sin contactos entre partículas, el caso no prueba nada");
            // (2) r y v en los primeros 1000 pasos; (3) energía y Nu en toda la corrida
            double e0 = brute.frames.getFirst().e(), maxDr = 0, maxDv = 0, maxDe = 0;
            for (int f = 0; f < brute.frames.size(); f++) {
                Frame b = brute.frames.get(f), q = cim.frames.get(f);
                assertEquals(b.nu(), q.nu(), c + ": Nu en t=" + b.t());
                maxDe = Math.max(maxDe, Math.abs(b.e() - q.e()) / e0);
                if (f > CLOSE_FRAMES) continue;
                for (int i = 0; i < b.x().length; i++) {
                    maxDr = Math.max(maxDr, Math.max(Math.abs(b.x()[i] - q.x()[i]), Math.abs(b.y()[i] - q.y()[i])));
                    maxDv = Math.max(maxDv, Math.max(Math.abs(b.vx()[i] - q.vx()[i]), Math.abs(b.vy()[i] - q.vy()[i])));
                }
            }
            assertTrue(maxDr < 1e-9, c + ": |Δr| máx " + maxDr);
            assertTrue(maxDv < 1e-6, c + ": |Δv| máx " + maxDv);
            assertTrue(maxDe < 1e-6, c + ": |ΔE|/E0 máx " + maxDe);
            int steps = brute.finder.pairs.size();
            System.out.printf(Locale.ROOT, "%-28s pasos=%d pares/paso=%.0f |Δr|=%.1e |Δv|=%.1e |ΔE|/E0=%.1e "
                            + "búsqueda: fuerza bruta %.1f µs/paso, CIM %.1f µs/paso (×%.1f) | corrida: %.2f s vs %.2f s%n",
                    c, steps, (double) totalPairs / steps, maxDr, maxDv, maxDe,
                    brute.finder.nanos / 1e3 / steps, cim.finder.nanos / 1e3 / steps,
                    (double) brute.finder.nanos / cim.finder.nanos, brute.wallNanos / 1e9, cim.wallNanos / 1e9);
        }
    }

    @Test void caseA_n300WithoutObstacles() throws IOException {
        BilliardConfig c = BilliardConfig.of(300, 11, BilliardConfig.NO_OBSTACLES, DT, DT2, 0.3);
        compare("(a) N=300 sin obstáculos", f -> BilliardSimulator.fromGrid(c, f));
    }

    @Test void caseB_nMaxWithTouchingObstacles() throws IOException {
        BilliardConfig c = BilliardConfig.of(714, 12, r, DT, DT2, 0.2);
        compare("(b) N=714 x0=r", f -> BilliardSimulator.fromGrid(c, f));
    }

    @Test void caseC_wallRingAndNegativeQuadrantCluster() throws IOException {
        // Anillo de 40 partículas contra la pared (|r| = R − r − 0,1 mm) yendo hacia afuera, y un racimo hexagonal de
        // 5×6 en el tercer cuadrante con separación 2r − 0,5 mm (arranca superpuesto); obstáculos en ±0,3
        Random random = new Random(13);
        List<double[]> state = new ArrayList<>();
        for (int k = 0; k < 40; k++) {
            double a = 2 * Math.PI * k / 40, d = R - r - 1e-4, dir = a + (random.nextDouble() - 0.5);
            state.add(new double[]{d * Math.cos(a), d * Math.sin(a), Math.cos(dir), Math.sin(dir)});
        }
        double s = 2 * r - 5e-4;
        for (int row = 0; row < 5; row++)
            for (int col = 0; col < 6; col++) {
                double dir = 2 * Math.PI * random.nextDouble();
                state.add(new double[]{-0.35 + (col + (row % 2) * 0.5) * s, -0.3 + row * s * Math.sqrt(3) / 2,
                        Math.cos(dir), Math.sin(dir)});
            }
        int n = state.size();
        double[] x = new double[n], y = new double[n], vx = new double[n], vy = new double[n];
        for (int i = 0; i < n; i++) { x[i] = state.get(i)[0]; y[i] = state.get(i)[1]; vx[i] = state.get(i)[2]; vy[i] = state.get(i)[3]; }
        assertTrue(Arrays.stream(x).anyMatch(v -> v < -R + 0.05) && Arrays.stream(y).anyMatch(v -> v < -R + 0.05));
        BilliardConfig c = BilliardConfig.of(n, 1, 0.3, DT, DT2, 0.5);
        compare("(c) pared + racimo x<0,y<0", f -> new BilliardSimulator(c, x, y, vx, vy, f));
    }
}
