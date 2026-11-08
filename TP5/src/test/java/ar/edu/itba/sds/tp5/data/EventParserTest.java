package ar.edu.itba.sds.tp5.data;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

class EventParserTest {
    private static List<PedestrianEvent> events;

    @BeforeAll
    static void load() throws IOException {
        events = EventParser.parse(Path.of("data"));
    }

    @Test
    void readsTheNineteenEventsAndTheFramerate() {
        assertEquals(19, events.size());
        for (int m = 0; m < 19; m++) {
            assertEquals(m + 1, events.get(m).number());
            assertEquals(1 / 15.0192, events.get(m).dtExp(), 1e-15);
        }
    }

    @Test
    void unknownLeftIdOfEventTwoIsThousand() {
        assertEquals(1000, events.get(1).left().id());
        assertEquals(25, events.get(1).right().id());
    }

    @Test
    void minimumDistanceMatchesTheReadme() {
        for (PedestrianEvent e : events)
            assertEquals(e.leemeMinDistance(), e.minDistance().distance(), 0.005 + 1e-9, "evento " + e.number());
    }

    @Test
    void offsetsMatchTheVerifiedCounts() {
        int startOffset = 0, endOffset = 0, maxStart = 0, maxEnd = 0;
        for (PedestrianEvent e : events) {
            int s = Math.abs(e.left().firstFrame() - e.right().firstFrame());
            int f = Math.abs(e.left().lastFrame() - e.right().lastFrame());
            if (s > 0) startOffset++;
            if (f > 0) endOffset++;
            maxStart = Math.max(maxStart, s);
            maxEnd = Math.max(maxEnd, f);
        }
        assertEquals(12, startOffset);
        assertEquals(62, maxStart);
        assertEquals(15, endOffset);
        assertEquals(92, maxEnd);
    }

    @Test
    void commonFramesGoFrom92To196() {
        int min = Integer.MAX_VALUE, max = 0;
        for (PedestrianEvent e : events) {
            min = Math.min(min, e.commonFramesAvailable());
            max = Math.max(max, e.commonFramesAvailable());
        }
        assertEquals(92, min);
        assertEquals(196, max);
    }

    @Test
    void gapsAreOnlyInEventOneAndFour() {
        for (PedestrianEvent e : events) {
            int expectedLeft = e.number() == 4 ? 16 : 0, expectedRight = e.number() == 1 ? 32 : 0;
            assertEquals(expectedLeft, e.left().missingFrames(), "izquierdo del evento " + e.number());
            assertEquals(expectedRight, e.right().missingFrames(), "derecho del evento " + e.number());
        }
    }

    @Test
    void trajectoryIsClippedToTheReadmeWindow() {
        PedestrianEvent third = events.get(2);
        assertEquals(1, third.right().id());
        assertEquals(20370, third.right().firstFrame());    // el ID 1 tiene filas desde el frame 19250
        assertEquals(20381, third.firstFrame());
        assertEquals(20516, third.lastFrame());
    }

    @Test
    void targetIsTheLastPositionOfTheCompleteTrajectory() {
        PedestrianEvent first = events.get(0);
        assertEquals(20254, first.left().lastFrame());      // la ventana común termina antes, en 20191
        assertEquals(11.2923, first.left().targetX(), 1e-12);
        assertEquals(2.99167, first.left().targetY(), 1e-12);
        assertEquals(20191, first.lastFrame());
    }

    private static final List<String> README = List.of(
            "Pruebas/pasadas: 1",
            "  prueba   1: sale izquierda   7, sale derecha   8, cuadros 10-14, distancia minima 1.00 m");

    @Test
    void commonWindowSkipsFramesMissingInEitherPedestrian() {
        List<PedestrianEvent> parsed = EventParser.parse(List.of("# framerate: 10 fps", "# id frame x/m y/m markerID",
                "7 9 -1 0 1", "7 10 0 0 1", "7 11 1 0 1", "7 12 2 0 1", "7 13 3 0 1",
                "8 11 0 5 1", "8 12 0 6 1", "8 14 0 8 1", "8 15 0 9 1"), README);
        PedestrianEvent e = parsed.get(0);
        assertEquals(10, e.left().firstFrame());            // el frame 9 queda fuera de los cuadros
        assertEquals(14, e.right().lastFrame());            // el 15 también
        assertEquals(11, e.firstFrame());
        assertEquals(12, e.lastFrame());                    // 13 falta en el 8 y 14 falta en el 7
        assertEquals(0.1, e.dtExp(), 1e-15);
    }

    @Test
    void repeatedFrameIsRejected() {
        assertThrows(IllegalArgumentException.class, () -> EventParser.parse(List.of("# framerate: 10 fps",
                "7 10 0 0 1", "7 10 1 0 1", "8 10 0 0 1", "8 11 0 0 1"), README));
    }

    @Test
    void meanSpeedCountsAGapAsItsChord() {
        Trajectory t = new Trajectory(1, new int[] { 0, 1, 4 }, new double[] { 0, 1, 4 }, new double[] { 0, 0, 4 });
        assertEquals((1 + 5) / (4 * 0.5), t.meanSpeed(0.5), 1e-12);
    }

    @Test
    void fittedVelocityRecoversAStraightLine() {
        double[] x = new double[8], y = new double[8];
        int[] frames = new int[8];
        for (int k = 0; k < 8; k++) { frames[k] = 100 + k; x[k] = 2 + 1.5 * k * 0.1; y[k] = -1 - 0.5 * k * 0.1; }
        Trajectory t = new Trajectory(1, frames, x, y);
        for (int count : new int[] { 2, 3, 5, 7 })
            assertArrayEquals(new double[] { 1.5, -0.5 }, t.fittedVelocity(100, count, 0.1), 1e-12);
    }

    @Test
    void fittedVelocityUsesTheRealTimesAcrossAGap() {
        int[] frames = { 0, 1, 5, 6, 7 };
        double[] x = new double[5], y = new double[5];
        for (int k = 0; k < 5; k++) x[k] = 3.0 * frames[k] * 0.1;
        assertArrayEquals(new double[] { 3, 0 }, new Trajectory(1, frames, x, y).fittedVelocity(0, 5, 0.1), 1e-12);
    }

    @Test
    void fittedVelocityMatchesAHandComputedFit() {
        // t = 0, 1, 2; y = 0, 1, 1: pendiente = Σ(t−1)(y−ȳ) / Σ(t−1)² = 1/2
        Trajectory t = new Trajectory(1, new int[] { 0, 1, 2 }, new double[3], new double[] { 0, 1, 1 });
        assertEquals(0.5, t.fittedVelocity(0, 3, 1)[1], 1e-12);
        assertTrue(t.fittedVelocity(0, 2, 1)[1] > 0.5);
    }
}
