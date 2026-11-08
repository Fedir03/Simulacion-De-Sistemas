package ar.edu.itba.sds.tp5.io;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.data.Trajectory;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.metrics.Ecm;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class OutputFilesTest {
    private static final OutputFiles.RunInfo INFO = new OutputFiles.RunInfo("BEEMAN", 64, 5, 0.1, "capa=none");

    private static PedestrianEvent event(int number) {
        Trajectory a = new Trajectory(1, new int[] { 0, 1 }, new double[] { 0, 1 }, new double[2]);
        Trajectory b = new Trajectory(2, new int[] { 0, 1 }, new double[] { 5, 4 }, new double[2]);
        return PedestrianEvent.of(number, a, b, 0.1, 1);
    }

    private static Simulation.Result sim(double arrival) {
        double[][] rows = { { 0, 0.5, 0, 1, 0, 5, 0, -1, 0 }, { 0.025, Double.NaN, Double.NaN, Double.NaN, Double.NaN, 4.9, 0, -1, 0 } };
        return new Simulation.Result(List.of(rows), 0.025, new double[] { arrival, Double.NaN }, new double[2], 1, 0, false, new int[2]);
    }

    private static OutputFiles.EventReport report(int number, double excluding, double filled) {
        Ecm.Pedestrian p = new Ecm.Pedestrian(excluding, filled, 0.5, 2, 2);
        return new OutputFiles.EventReport(event(number), sim(0.025), new Ecm.Event(new Ecm.Pedestrian[] { p, p }), new double[] { 0.025, 3 });
    }

    @Test
    void reportsThatTheOrderDoesNotChange() {
        String text = OutputFiles.orderComparison(List.of(report(1, 1, 1), report(2, 2, 3)));
        assertTrue(text.startsWith("sin_cambios"), text);
    }

    @Test
    void reportsWhichEventsChangePosition() {
        String text = OutputFiles.orderComparison(List.of(report(1, 1, 3), report(2, 2, 2), report(3, 5, 5)));
        assertTrue(text.startsWith("cambia"), text);
        assertTrue(text.contains("eventos_movidos=[1, 2]"), text);
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

    @Test
    void ecmReportHasBothVariantsAndTheArrivals(@TempDir Path dir) throws IOException {
        Path file = dir.resolve("ecm.txt");
        OutputFiles.writeEcmReport(file, List.of(report(1, 1, 1.5)), INFO);
        String text = Files.readString(file);
        assertTrue(text.contains("ecm1_excl=1.000000 ecm1_relleno=1.500000 ecm2=0.500000"), text);
        assertTrue(text.contains("llegan_en_ventana=1 de 2"), text);
        assertTrue(text.contains("orden_ecm1 sin_cambios"), text);
    }
}
