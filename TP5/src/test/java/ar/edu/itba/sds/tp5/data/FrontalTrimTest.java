package ar.edu.itba.sds.tp5.data;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.analysis.Ecm;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;

class FrontalTrimTest {
    private static final double DT = 0.1;
    /** D(45°) sin la compuerta de tramo compartido (el recorte del piloto del 11/11). */
    private static final FrontalTrim.Options D45 = new FrontalTrim.Options(true, 45, 5, 2, FrontalTrim.Target.COMMON);
    /** Vigente: D(45°) con la compuerta, X = 1,5 m. */
    private static final FrontalTrim.Options SHARED = FrontalTrim.Options.DEFAULT;

    /**
     * Evento sintético: cada peatón sube en vertical (20 frames) y después cruza en horizontal, el izquierdo sobre y = 2
     * de x = 0 a x = 8 y el derecho sobre y = 2,6 de x = 8 a x = 0, a 1 m/s. Al final los dos salen en vertical.
     */
    private static PedestrianEvent verticalStart() {
        return PedestrianEvent.of(1, walker(1, 0, 1, 2), walker(2, 8, -1, 2.6), DT, 0.6);
    }

    private static Trajectory walker(int id, double x0, int sense, double lane) {
        int up = 20, across = 80, out = 15, n = up + across + out + 1;
        int[] f = new int[n];
        double[] x = new double[n], y = new double[n];
        for (int k = 0; k < n; k++) {
            f[k] = 1000 + k;
            if (k <= up) { x[k] = x0; y[k] = lane * k / up; }
            else if (k <= up + across) { x[k] = x0 + sense * 0.1 * (k - up); y[k] = lane; }
            else { x[k] = x0 + sense * 8; y[k] = lane + 0.1 * (k - up - across); }
        }
        return new Trajectory(id, f, x, y);
    }

    @Test
    void verticalStartIsCutAndTheTargetLiesOnTheXAxis() {
        PedestrianEvent full = verticalStart(), cut = FrontalTrim.apply(full, D45);
        assertTrue(cut.firstFrame() > 1000 + 20, "el tramo vertical inicial queda afuera");
        assertTrue(cut.lastFrame() <= 1000 + 100, "la salida vertical queda afuera");
        for (int i = 0; i < 2; i++) {
            Agent a = Agent.from(cut, i, 5);
            double ex = a.targetX() - a.x0(), ey = a.targetY() - a.y0();
            assertTrue(Math.abs(ey) < 0.01 * Math.abs(ex), "e_target sobre el eje x, peatón " + i + ": " + ex + ", " + ey);
            assertTrue(Math.abs(a.vy0()) < 0.05 * Math.abs(a.vx0()), "v_0 sin componente vertical, peatón " + i);
            assertEquals(1.0, a.desiredSpeed(), 0.01, "v_d del tramo horizontal");
            Agent before = Agent.from(full, i, 5);
            assertTrue(Math.abs(before.vy0()) > Math.abs(before.vx0()), "sin recorte arranca subiendo");
        }
    }

    @Test
    void trimmingIsIdempotent() throws IOException {
        List<PedestrianEvent> events = new ArrayList<>(EventParser.parse(Path.of("data")));
        events.add(verticalStart());
        for (FrontalTrim.Options options : List.of(D45, SHARED))
            for (PedestrianEvent e : events) {
                PedestrianEvent once = FrontalTrim.apply(e, options), twice = FrontalTrim.apply(once, options);
                assertEquals(once.firstFrame(), twice.firstFrame(), "evento " + e.number());
                assertEquals(once.lastFrame(), twice.lastFrame(), "evento " + e.number());
                assertArrayEquals(once.targetFrame(), twice.targetFrame(), "evento " + e.number());
                for (int i = 0; i < 2; i++) assertArrayEquals(once.pedestrian(i).frames(), twice.pedestrian(i).frames());
            }
    }

    @Test
    void trimmedTrajectoryAgainstItselfGivesZeroError() throws IOException {
        for (FrontalTrim.Options options : List.of(D45, SHARED))
            for (PedestrianEvent full : EventParser.parse(Path.of("data"))) {
                PedestrianEvent e = FrontalTrim.apply(full, options);
                Ecm.Event ecm = Ecm.of(e, replay(e));
                assertEquals(0, ecm.ecm1Excluding(), 1e-20, "evento " + e.number());
                assertEquals(0, ecm.ecm2(), 1e-20, "evento " + e.number());
            }
    }

    /** Eventos cuya ventana, target o tramo de v_d cambian con la compuerta respecto de D(45°) sin ella. */
    private static java.util.Set<Integer> changedByGate(double x) throws IOException {
        FrontalTrim.Options gate = new FrontalTrim.Options(true, 45, 5, 2, FrontalTrim.Target.COMMON, true, x);
        java.util.Set<Integer> changed = new java.util.TreeSet<>();
        for (PedestrianEvent full : EventParser.parse(Path.of("data"))) {
            PedestrianEvent a = FrontalTrim.apply(full, D45), b = FrontalTrim.apply(full, gate);
            if (a.firstFrame() != b.firstFrame() || a.lastFrame() != b.lastFrame()
                    || !java.util.Arrays.equals(a.targetFrame(), b.targetFrame()) || !java.util.Arrays.equals(a.speedFrom(), b.speedFrom()))
                changed.add(full.number());
        }
        return changed;
    }

    @Test
    void gateChangesOnlyEventsThreeAndSixForXBetweenOneAndTwo() throws IOException {
        for (double x : new double[] { 1.0, 1.5, 2.0 }) assertEquals(java.util.Set.of(3, 6), changedByGate(x), "X = " + x);
    }

    @Test
    void theOtherSeventeenEventsSimulateIdenticallyWithTheGate() throws IOException {
        Simulation sim = new Simulation(ar.edu.itba.sds.tp5.engine.SfmParameters.defaults(), ar.edu.itba.sds.tp5.engine.Integrator.DEFAULT,
                Simulation.DEFAULT_DT_DIV);
        for (PedestrianEvent full : EventParser.parse(Path.of("data"))) {
            if (full.number() == 3 || full.number() == 6) continue;
            PedestrianEvent a = FrontalTrim.apply(full, D45), b = FrontalTrim.apply(full, SHARED);
            List<double[]> ra = sim.run(ar.edu.itba.sds.tp5.Main.agents(a, 5), a.dtExp(), a.windowIntervals()).rows(), rb = sim.run(ar.edu.itba.sds.tp5.Main.agents(b, 5), b.dtExp(), b.windowIntervals()).rows();
            assertEquals(ra.size(), rb.size(), "evento " + full.number());
            for (int r = 0; r < ra.size(); r++) assertArrayEquals(ra.get(r), rb.get(r), 0.0, "evento " + full.number() + ", fila " + r);
        }
    }

    @Test
    void gateReproducesTheManualCutOfEventsThreeAndSix() throws IOException {
        List<PedestrianEvent> raw = EventParser.parse(Path.of("data"));
        int[][] expected = { { 3, 20381, 20470, 90 }, { 6, 20827, 20909, 83 } };
        for (int[] x : expected) {
            PedestrianEvent e = FrontalTrim.apply(raw.get(x[0] - 1), SHARED);
            assertEquals(x[1], e.firstFrame(), "evento " + x[0]);
            assertEquals(x[2], e.lastFrame(), "evento " + x[0]);
            assertEquals(x[3], e.commonFramesAvailable(), "evento " + x[0]);
            assertArrayEquals(new int[] { x[2], x[2] }, e.targetFrame());
            assertArrayEquals(new int[] { x[1], x[1] }, e.speedFrom());
        }
    }

    /** "Simulación" que repite las posiciones experimentales, interpolando entre frames (y en los huecos). */
    private static Simulation.Result replay(PedestrianEvent e) {
        List<double[]> rows = new ArrayList<>();
        int perInterval = Simulation.ROWS_PER_INTERVAL;
        for (int r = 0; r <= e.windowIntervals() * perInterval; r++) {
            double frame = e.firstFrame() + (double) r / perInterval;
            double[] row = new double[9];
            row[0] = r * e.dtExp() / perInterval;
            for (int i = 0; i < 2; i++) {
                double[] p = at(e.pedestrian(i), frame);
                row[1 + 4 * i] = p[0];
                row[2 + 4 * i] = p[1];
            }
            rows.add(row);
        }
        return new Simulation.Result(rows, e.dtExp() / perInterval, new double[] { Double.NaN, Double.NaN });
    }

    private static double[] at(Trajectory t, double frame) {
        int k = 0;
        while (k < t.size() - 1 && t.frames()[k + 1] <= frame) k++;
        if (k == t.size() - 1 || t.frames()[k] == frame) return new double[] { t.x()[k], t.y()[k] };
        double w = (frame - t.frames()[k]) / (t.frames()[k + 1] - t.frames()[k]);
        return new double[] { t.x()[k] + w * (t.x()[k + 1] - t.x()[k]), t.y()[k] + w * (t.y()[k + 1] - t.y()[k]) };
    }

    @Test
    void commonTargetIsTheLastPositionInTheWindowAndOwnTargetGoesFurther() throws IOException {
        FrontalTrim.Options own = new FrontalTrim.Options(true, 45, 5, 2, FrontalTrim.Target.OWN);
        for (PedestrianEvent full : EventParser.parse(Path.of("data"))) {
            PedestrianEvent common = FrontalTrim.apply(full, D45), mine = FrontalTrim.apply(full, own);
            assertEquals(common.firstFrame(), mine.firstFrame());
            assertEquals(common.lastFrame(), mine.lastFrame());
            for (int i = 0; i < 2; i++) {
                assertEquals(common.lastFrame(), common.targetFrame()[i]);
                assertEquals(common.firstFrame(), common.speedFrom()[i]);
                assertEquals(common.firstFrame(), mine.speedFrom()[i]);
                assertTrue(mine.targetFrame()[i] >= common.lastFrame());
                Trajectory t = full.pedestrian(i);
                int k = t.indexOf(common.lastFrame());
                assertEquals(t.x()[k], common.targetX(i));
                assertEquals(t.y()[k], common.targetY(i));
            }
        }
    }

    @Test
    void offReturnsTheSameEventsAndCliOptionsAreValidated() throws IOException {
        List<PedestrianEvent> raw = EventParser.parse(Path.of("data"));
        assertSame(raw, FrontalTrim.apply(raw, FrontalTrim.Options.OFF));
        assertEquals(SHARED, FrontalTrim.Options.parse(Map.of()));
        assertEquals(D45, FrontalTrim.Options.parse(Map.of("trim-shared", "off")));
        assertEquals("recorte=D45.0_p5_h2_common", D45.label());           // sin compuerta, el encabezado de antes
        assertEquals("recorte=D45.0_p5_h2_common_sx1.5", SHARED.label());
        assertEquals(new FrontalTrim.Options(true, 30, 3, 2, FrontalTrim.Target.OWN, true, 1.0),
                FrontalTrim.Options.parse(Map.of("trim-deg", "30", "trim-persist", "3", "trim-target", "own", "trim-shared-x", "1.0")));
        assertThrows(IllegalArgumentException.class, () -> FrontalTrim.Options.parse(Map.of("trim-shared", "off", "trim-shared-x", "2")));
        assertThrows(IllegalArgumentException.class, () -> FrontalTrim.Options.parse(Map.of("trim", "off", "trim-deg", "30")));
        assertThrows(IllegalArgumentException.class, () -> FrontalTrim.Options.parse(Map.of("trim-target", "x")));
    }

    @Test
    void persistenceClosesShortInterruptionsOnly() {
        boolean[] ok = { true, false, false, true, false, false, false, false, false, true };
        assertArrayEquals(new boolean[] { true, true, true, true, false, false, false, false, false, true }, FrontalTrim.closeGaps(ok, 5));
        assertArrayEquals(ok, FrontalTrim.closeGaps(ok, 2));
    }
}
