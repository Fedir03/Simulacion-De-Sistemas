package ar.edu.itba.sds.tp5.analysis;

import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.data.Trajectory;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.io.OutputFiles;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

/** Informe ecm.txt (antes en io.OutputFilesTest, cuando lo escribía el motor). */
class EcmReportTest {
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

    private static EcmReport.EventReport report(int number, double excluding, double filled) {
        Ecm.Pedestrian p = new Ecm.Pedestrian(excluding, filled, 0.5, 2, 2);
        return new EcmReport.EventReport(event(number), sim(0.025), new Ecm.Event(new Ecm.Pedestrian[] { p, p }),
                new ContactMonitor.Stats(1, 0, false), new double[] { 0.025, 3 });
    }

    @Test
    void reportsThatTheOrderDoesNotChange() {
        String text = EcmReport.orderComparison(List.of(report(1, 1, 1), report(2, 2, 3)));
        assertTrue(text.startsWith("sin_cambios"), text);
    }

    @Test
    void reportsWhichEventsChangePosition() {
        String text = EcmReport.orderComparison(List.of(report(1, 1, 3), report(2, 2, 2), report(3, 5, 5)));
        assertTrue(text.startsWith("cambia"), text);
        assertTrue(text.contains("eventos_movidos=[1, 2]"), text);
    }

    @Test
    void ecmReportHasBothVariantsAndTheArrivals(@TempDir Path dir) throws IOException {
        Path file = dir.resolve("ecm.txt");
        EcmReport.write(file, List.of(report(1, 1, 1.5)), INFO);
        String text = Files.readString(file);
        assertTrue(text.contains("ecm1_excl=1.000000 ecm1_relleno=1.500000 ecm2=0.500000"), text);
        assertTrue(text.contains("llegan_en_ventana=1 de 2"), text);
        assertTrue(text.contains("orden_ecm1 sin_cambios"), text);
    }
}
