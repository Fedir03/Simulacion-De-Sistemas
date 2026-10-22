package ar.edu.itba.sds.tp4.engine.cim;

import ar.edu.itba.sds.tp4.engine.GridPlacement;
import ar.edu.itba.sds.tp4.engine.GridPlacement.*;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class CellIndexMethodTest {
    private static final double R = 0.51, r = 0.0175, DT = 1e-3;
    private static final int M_MAX = CellIndexMethod.maxValidM(2 * R, 0, r);
    private static final int[] MS = {M_MAX, 10, 7, 1};
    private static final NeighborFinder BRUTE = new BruteForceNeighborFinder();

    /**
     * Pares de forEachContact como mapa id → vecinos, igual que findNeighbors. Falla si un par llega dos veces o
     * con i ≥ j. Todas las partículas de ps tienen el mismo radio r.
     */
    static Map<Integer, Set<Integer>> pairsViaForEach(NeighborFinder finder, List<Particle> ps) {
        int n = ps.size();
        double[] x = new double[n], y = new double[n];
        Map<Integer, Set<Integer>> neighbors = new HashMap<>();
        for (int i = 0; i < n; i++) {
            x[i] = ps.get(i).x(); y[i] = ps.get(i).y();
            neighbors.put(ps.get(i).id(), new HashSet<>());
        }
        Set<Long> seen = new HashSet<>();
        finder.forEachContact(x, y, r, 2 * R, (i, j) -> {
            assertTrue(i < j, "par con i ≥ j: " + i + ", " + j);
            assertTrue(seen.add((long) i * n + j), "par repetido: " + i + ", " + j);
            neighbors.get(ps.get(i).id()).add(ps.get(j).id());
            neighbors.get(ps.get(j).id()).add(ps.get(i).id());
        });
        return neighbors;
    }

    /** Fuerza bruta = findContacts = forEachContact para cada M. */
    private static void assertAllAgree(List<Particle> ps, int... ms) {
        Map<Integer, Set<Integer>> expected = BRUTE.findNeighbors(ps, 2 * R, 0, false);
        for (int m : ms) {
            CellIndexMethod cim = CellIndexMethod.forCircle(m, R);
            assertEquals(expected, cim.findContacts(ps), "findContacts M=" + m);
            assertEquals(expected, pairsViaForEach(cim, ps), "forEachContact M=" + m);
        }
    }

    private static List<Placed> grid(int n, long seed, List<Particle> obstacles) {
        List<Site> sites = GridPlacement.sites(Lattice.HEX, Anchor.SITE_AT_ORIGIN, 2 * r + 1e-4, R, r, obstacles);
        return GridPlacement.place(sites, n < 0 ? sites.size() : n, seed, 1);
    }

    /**
     * Vuelo libre: x += v·dt sin fuerzas, con rebote especular en la pared, así que las partículas se traslapan
     * libremente. La trayectoria no depende del buscador, por eso alcanza con consultar a los dos en cada paso.
     * Devuelve la cantidad de pares en contacto sumada sobre todos los pasos.
     */
    private static long assertSameContactsInFreeFlight(List<Placed> start, int steps, int m) {
        CellIndexMethod cim = CellIndexMethod.forCircle(m, R);
        int n = start.size();
        double[] x = new double[n], y = new double[n], vx = new double[n], vy = new double[n];
        for (int i = 0; i < n; i++) {
            Placed p = start.get(i);
            x[i] = p.x(); y[i] = p.y(); vx[i] = p.vx(); vy[i] = p.vy();
        }
        long contacts = 0;
        for (int step = 0; step <= steps; step++) {
            List<Particle> ps = new ArrayList<>(n);
            for (int i = 0; i < n; i++) ps.add(new Particle(start.get(i).id(), x[i], y[i], r));
            Map<Integer, Set<Integer>> expected = BRUTE.findNeighbors(ps, 2 * R, 0, false);
            Map<Integer, Set<Integer>> actual = cim.findContacts(ps);
            if (!expected.equals(actual)) fail("M=" + m + ", paso " + step + ": " + firstDifference(expected, actual));
            Map<Integer, Set<Integer>> viaForEach = pairsViaForEach(cim, ps);
            if (!expected.equals(viaForEach))
                fail("forEachContact M=" + m + ", paso " + step + ": " + firstDifference(expected, viaForEach));
            for (Set<Integer> s : expected.values()) contacts += s.size();
            for (int i = 0; i < n; i++) {
                x[i] += vx[i] * DT; y[i] += vy[i] * DT;
                double d = Math.hypot(x[i], y[i]), nx = x[i] / d, ny = y[i] / d, vn = vx[i] * nx + vy[i] * ny;
                if (d > R - r && vn > 0) { vx[i] -= 2 * vn * nx; vy[i] -= 2 * vn * ny; }
            }
        }
        return contacts / 2;
    }

    private static String firstDifference(Map<Integer, Set<Integer>> expected, Map<Integer, Set<Integer>> actual) {
        for (int id : expected.keySet())
            if (!expected.get(id).equals(actual.get(id)))
                return "partícula " + id + ": fuerza bruta " + expected.get(id) + ", CIM " + actual.get(id);
        return "claves distintas: " + expected.keySet() + " vs " + actual.keySet();
    }

    @Test void mMaxIs29ForTheBilliard() {
        assertEquals(29, M_MAX);
    }

    @Test void freeFlightN300WithoutObstaclesMatchesBruteForceEveryStep() {
        List<Placed> start = grid(300, 42, List.of());
        for (int m : MS) assertTrue(assertSameContactsInFreeFlight(start, 1000, m) > 0, "sin contactos con M=" + m);
    }

    @Test void freeFlightMaxNWithTouchingObstaclesMatchesBruteForceEveryStep() {
        // Las posiciones vienen de la grilla con obstáculos en x0=r; los obstáculos no van en la grilla del CIM (D25).
        // 200 pasos (20 cm a 1 m/s, ~6 celdas): con 2000 el test tardaba ~30 s por la fuerza bruta con N≈714
        List<Placed> start = grid(-1, 7, GridPlacement.obstacles(r, r));
        for (int m : MS) assertTrue(assertSameContactsInFreeFlight(start, 200, m) > 0, "sin contactos con M=" + m);
    }

    @Test void freeFlightNearWallAndNegativeQuadrantMatchesBruteForceEveryStep() {
        Random random = new Random(3);
        List<Placed> start = new ArrayList<>();
        int id = 1;
        // Anillo pegado a la pared (|r| = R − r), con velocidad hacia afuera para que rebote enseguida
        for (int k = 0; k < 60; k++, id++) {
            double a = 2 * Math.PI * k / 60, b = a + (random.nextDouble() - 0.5);
            start.add(new Placed(id, (R - r) * Math.cos(a), (R - r) * Math.sin(a), Math.cos(b), Math.sin(b)));
        }
        // Racimo superpuesto en x<0, y<0
        for (int k = 0; k < 40; k++, id++) {
            double b = random.nextDouble() * 2 * Math.PI;
            start.add(new Placed(id, -0.25 + 0.06 * random.nextDouble(), -0.25 + 0.06 * random.nextDouble(), Math.cos(b), Math.sin(b)));
        }
        for (int m : MS) assertTrue(assertSameContactsInFreeFlight(start, 2000, m) > 0, "sin contactos con M=" + m);
    }

    @Test void pairsAcrossCellBordersAndHalfNeighborhoodDiagonalAreFound() {
        double c = 2 * R / M_MAX;
        List<Particle> ps = new ArrayList<>();
        Set<List<Integer>> pairs = new HashSet<>();
        int id = 1;
        // Esquinas de celda en los cuatro cuadrantes (coordenada corrida = k·c)
        for (int kx : new int[]{5, 13, 15, 24})
            for (int ky : new int[]{5, 14, 16, 24}) {
                double bx = kx * c - R, by = ky * c - R, e = 0.006;
                ps.add(new Particle(id, bx - e, by, r)); ps.add(new Particle(id + 1, bx + e, by, r));         // borde en x
                ps.add(new Particle(id + 2, bx, by + 3 * c - e, r)); ps.add(new Particle(id + 3, bx, by + 3 * c + e, r)); // borde en y
                ps.add(new Particle(id + 4, bx + 6 * c + e, by - 6 * c - e, r));                                  // diagonal (−1, +1)
                ps.add(new Particle(id + 5, bx + 6 * c - e, by - 6 * c + e, r));
                ps.add(new Particle(id + 6, kx * c - R, ky * c - R + 9 * c, r));                                    // justo sobre el borde
                pairs.add(List.of(id, id + 1)); pairs.add(List.of(id + 2, id + 3)); pairs.add(List.of(id + 4, id + 5));
                id += 7;
            }
        ps.removeIf(p -> Math.hypot(p.x(), p.y()) > R);
        // |r| = R exacto está permitido, y su vecina hacia adentro tiene que aparecer
        ps.add(new Particle(id, R, 0, r)); ps.add(new Particle(id + 1, R - 0.02, 0, r));
        pairs.add(List.of(id, id + 1));
        Set<Integer> present = new HashSet<>();
        for (Particle p : ps) present.add(p.id());

        Map<Integer, Set<Integer>> expected = BRUTE.findNeighbors(ps, 2 * R, 0, false);
        for (List<Integer> pair : pairs)
            if (present.containsAll(pair)) assertTrue(expected.get(pair.get(0)).contains(pair.get(1)), "par armado " + pair);
        for (int m : MS) assertEquals(expected, CellIndexMethod.forCircle(m, R).findContacts(ps), "M=" + m);
        assertAllAgree(ps, MS);
    }

    @Test void negativeCoordinatesAndBothClampedBordersMatch() {
        // x + R = 0 cae en la celda 0 sin recorte; x = R da índice M y se recorta a M − 1
        double d = 2 * r - 0.004, q = (R - r) / Math.sqrt(2);
        List<Particle> ps = List.of(
                new Particle(1, -R, 0, r), new Particle(2, -R + d, 0, r),
                new Particle(3, 0, -R, r), new Particle(4, 0.003, -R + d, r),
                new Particle(5, -q, -q, r), new Particle(6, -q + d, -q, r), new Particle(7, -q, -q + d, r),
                new Particle(8, R, 0, r), new Particle(9, R - d, 0.002, r),
                new Particle(10, 0, R, r), new Particle(11, -0.002, R - d, r));
        Map<Integer, Set<Integer>> expected = BRUTE.findNeighbors(ps, 2 * R, 0, false);
        assertEquals(Set.of(2), expected.get(1));
        assertEquals(Set.of(6, 7), expected.get(5));
        assertEquals(Set.of(9), expected.get(8));
        assertAllAgree(ps, MS);
    }

    @Test void overlappingClusterInsideOneCellGivesEveryPairOnce() {
        // 4 partículas superpuestas dentro de una misma celda (de 0,035 m con M = 29): 6 pares
        double c = 2 * R / M_MAX, bx = 3 * c - R + 0.004, by = 20 * c - R + 0.004;
        List<Particle> ps = List.of(new Particle(1, bx, by, r), new Particle(2, bx + 0.01, by, r),
                new Particle(3, bx, by + 0.01, r), new Particle(4, bx + 0.01, by + 0.01, r));
        Map<Integer, Set<Integer>> expected = BRUTE.findNeighbors(ps, 2 * R, 0, false);
        for (Set<Integer> s : expected.values()) assertEquals(3, s.size());
        assertAllAgree(ps, M_MAX, 7);
    }

    @Test void forEachContactValidatesLikeFindContacts() {
        CellIndexMethod cim = CellIndexMethod.forCircle(M_MAX, R);
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class,
                () -> cim.forEachContact(new double[]{0, -(R + 1e-9)}, new double[]{0, 0}, r, 2 * R, (i, j) -> { }));
        assertTrue(e.getMessage().contains("Particula 1"), e.getMessage());
        assertThrows(IllegalArgumentException.class,
                () -> CellIndexMethod.forCircle(M_MAX + 1, R).forEachContact(new double[]{0}, new double[]{0}, r, 2 * R, (i, j) -> { }));
        assertThrows(IllegalArgumentException.class,
                () -> cim.forEachContact(new double[]{0}, new double[]{0}, r, 2 * R + 1e-6, (i, j) -> { }));
        // N = 0 y N = 1: ningún par
        assertTrue(pairsViaForEach(cim, List.of()).isEmpty());
        assertEquals(Map.of(1, Set.of()), pairsViaForEach(cim, List.of(new Particle(1, 0.1, 0.1, r))));
    }

    @Test void forEachContactReusesItsBuffersAcrossSizes() {
        CellIndexMethod cim = CellIndexMethod.forCircle(M_MAX, R);
        List<Particle> big = new ArrayList<>();
        for (Placed p : grid(-1, 7, GridPlacement.obstacles(r, r))) big.add(new Particle(p.id(), p.x() * 0.98, p.y() * 0.98, r));
        Map<Integer, Set<Integer>> expectedBig = BRUTE.findNeighbors(big, 2 * R, 0, false);
        List<Particle> small = big.subList(0, 10);
        assertEquals(expectedBig, pairsViaForEach(cim, big));
        assertEquals(BRUTE.findNeighbors(small, 2 * R, 0, false), pairsViaForEach(cim, small));
        assertEquals(expectedBig, pairsViaForEach(cim, big));
    }

    @Test void squareModeForEachContactUsesTheGenericPath() {
        List<Particle> ps = List.of(new Particle(0, 0.2, 0.2, r), new Particle(1, 0.22, 0.2, r), new Particle(2, 0.6, 0.6, r));
        Map<Integer, Set<Integer>> expected = BRUTE.findNeighbors(ps, 2 * R, 0, false);
        assertEquals(Set.of(1), expected.get(0));
        assertEquals(expected, pairsViaForEach(new CellIndexMethod(5), ps));
        assertEquals(expected, pairsViaForEach(BRUTE, ps));
    }

    @Test void particleOutsideCircleIsRejected() {
        List<Particle> ps = List.of(new Particle(1, 0, 0, r), new Particle(2, -(R + 1e-9), 0, r));
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class, () -> CellIndexMethod.forCircle(M_MAX, R).findContacts(ps));
        assertTrue(e.getMessage().contains("Particula 2"), e.getMessage());
    }

    @Test void lMustBeTwiceRWithTolerance() {
        CellIndexMethod cim = CellIndexMethod.forCircle(M_MAX, R);
        List<Particle> ps = List.of(new Particle(1, -0.3, -0.3, r), new Particle(2, -0.29, -0.3, r));
        assertThrows(IllegalArgumentException.class, () -> cim.findNeighbors(ps, 2 * R + 1e-6, 0, false));
        assertEquals(cim.findContacts(ps), cim.findNeighbors(ps, 2 * R + 1e-14, 0, false));
        assertEquals(cim.findContacts(ps), cim.findNeighbors(ps, 2 * R - 1e-14, 0, false));
        assertThrows(IllegalArgumentException.class, () -> cim.findNeighbors(ps, 2 * R, 0, true));
    }

    @Test void squareModeFromTp1IsUnchanged() {
        assertThrows(IllegalStateException.class, () -> new CellIndexMethod(5).findContacts(List.of()));
        List<Particle> ps = List.of(new Particle(1, 1, 1, 0.1), new Particle(2, 1.25, 1, 0.1), new Particle(3, 5, 5, 0.1));
        assertEquals(BRUTE.findNeighbors(ps, 10, 0.1, false), new CellIndexMethod(5).findNeighbors(ps, 10, 0.1, false));
    }
}
