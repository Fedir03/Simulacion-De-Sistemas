package ar.edu.itba.sds.tp5.io;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.data.Trajectory;
import ar.edu.itba.sds.tp5.engine.Simulation;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Salida del motor (trayectorias). El informe ecm.txt se prueba en analysis.EcmReportTest. */
class OutputFilesTest {
    private static final OutputFiles.RunInfo INFO = new OutputFiles.RunInfo("BEEMAN", 64, 5, 0.1, "capa=none");

    private static PedestrianEvent event(int number) {
        Trajectory a = new Trajectory(1, new int[] { 0, 1 }, new double[] { 0, 1 }, new double[2]);
        Trajectory b = new Trajectory(2, new int[] { 0, 1 }, new double[] { 5, 4 }, new double[2]);
        return PedestrianEvent.of(number, a, b, 0.1, 1);
    }

    private static Simulation.Result sim(double arrival) {
        double[][] rows = { { 0, 0.5, 0, 1, 0, 5, 0, -1, 0 }, { 0.025, Double.NaN, Double.NaN, Double.NaN, Double.NaN, 4.9, 0, -1, 0 } };
        return new Simulation.Result(List.of(rows), 0.025, new double[] { arrival, Double.NaN });
    }

    @Test
    void trajectoryHasTheAgreedColumnsAndNaNForRetiredPedestrians(@TempDir Path dir) throws IOException {
        Path file = dir.resolve("evento.txt");
        OutputFiles.writeTrajectory(file, event(7), sim(0.025), INFO);
        List<String> lines = Files.readAllLines(file, StandardCharsets.UTF_8);
        assertTrue(lines.get(0).contains("evento=7"));
        assertEquals("# t x1 y1 vx1 vy1 x2 y2 vx2 vy2", lines.get(1));
        assertEquals(9, lines.get(2).split(" ").length);
        assertEquals("0.025000 NaN NaN NaN NaN 4.900000 0.000000 -1.000000 0.000000", lines.get(3));
        assertFalse(Files.readString(file).contains("\r"));
    }
}
