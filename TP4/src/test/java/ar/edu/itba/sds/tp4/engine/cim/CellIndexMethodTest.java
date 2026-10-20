package ar.edu.itba.sds.tp4.engine.cim;

import ar.edu.itba.sds.tp4.engine.GridPlacement;
import ar.edu.itba.sds.tp4.engine.GridPlacement.*;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class CellIndexMethodTest {
    private static final double R = 0.51, r = 0.0175, DT = 1e-3;
    private static final int M_MAX = CellIndexMethod.maxValidM(2 * R, 0, r);
    private static final int[] MS = {M_MAX, 10, 1};
    private static final NeighborFinder BRUTE = new BruteForceNeighborFinder();

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
