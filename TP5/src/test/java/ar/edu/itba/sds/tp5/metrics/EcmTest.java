package ar.edu.itba.sds.tp5.metrics;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.data.Trajectory;
import ar.edu.itba.sds.tp5.engine.Simulation;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class EcmTest {
    private static final double DT_EXP = 0.25;

    /** Peatón 0 en y = 0, de x = 0 a x = 4; el peatón 1 lejos, para tener un evento válido. */
    private static Trajectory walker(int id, double y, int... frames) {
        double[] x = new double[frames.length], yy = new double[frames.length];
        for (int k = 0; k < frames.length; k++) { x[k] = frames[k]; yy[k] = y; }
        return new Trajectory(id, frames, x, yy);
    }

    private static PedestrianEvent event(Trajectory left) {
        return PedestrianEvent.of(1, left, walker(2, 50, 0, 1, 2, 3, 4), DT_EXP, 1);
    }

    /** Filas cada dt2 = Δt_exp/4, con la posición del agente 0 dada por x(fila), y = y0; NaN después de {@code leaveRow}. */
    private static Simulation.Result sim(int rows, java.util.function.IntToDoubleFunction x, double y0, int leaveRow) {
        List<double[]> list = new ArrayList<>();
        for (int r = 0; r < rows; r++) {
            boolean in = r < leaveRow;
            list.add(new double[] { r * DT_EXP / 4, in ? x.applyAsDouble(r) : Double.NaN, in ? y0 : Double.NaN, 0, 0, 0, 50, 0, 0 });
        }
        return new Simulation.Result(list, DT_EXP / 4, new double[2], new double[2], 1, 0, false, new int[2]);
    }

    @Test
    void trajectoryAgainstItselfIsZero() {
        Ecm.Pedestrian p = Ecm.of(event(walker(1, 0, 0, 1, 2, 3, 4)), sim(17, r -> r / 4.0, 0, 17), 0);
        assertEquals(0, p.ecm1Excluding(), 1e-12);
        assertEquals(0, p.ecm1Filled(), 1e-12);
        assertEquals(0, p.ecm2(), 1e-12);
        assertEquals(5, p.n1());
        assertEquals(5, p.n2());
    }

    @Test
    void constantOffsetGivesItsSquare() {
        Ecm.Pedestrian p = Ecm.of(event(walker(1, 0, 0, 1, 2, 3, 4)), sim(17, r -> r / 4.0, 0.3, 17), 0);
        assertEquals(0.09, p.ecm1Excluding(), 1e-12);
        assertEquals(0.09, p.ecm2(), 1e-12);
    }

    @Test
    void secondMetricIgnoresATimeShiftOfTheSamePath() {
        // Misma recta, recorrida 8 filas (2 frames) después; con cola para cubrir todos los puntos experimentales
        Ecm.Pedestrian p = Ecm.of(event(walker(1, 0, 0, 1, 2, 3, 4)), sim(25, r -> Math.max(0, (r - 8) / 4.0), 0, 25), 0);
        assertEquals((0 + 1 + 4 + 4 + 4) / 5.0, p.ecm1Excluding(), 1e-12);  // errores de 0, 1, 2, 2 y 2 m: arranca quieto
        assertEquals(0, p.ecm2(), 1e-12);
        assertTrue(p.ecm2() <= p.ecm1Excluding());
    }

    @Test
    void framesMissingInTheExperimentAreOmitted() {
        // Falta el frame 2. Error (0,3)² en todos los instantes salvo en ese, donde el simulado está lejos
        Ecm.Pedestrian p = Ecm.of(event(walker(1, 0, 0, 1, 3, 4)), sim(17, r -> r == 8 ? 99 : r / 4.0, 0.3, 17), 0);
        assertEquals(4, p.n1());
        assertEquals(4, p.n2());
        assertEquals(0.09, p.ecm1Excluding(), 1e-12);
    }

    @Test
    void afterLeavingTheFirstMetricExcludesThoseInstants() {
        // Se va en la fila 9: quedan los t_k de las filas 0, 4 y 8
        Ecm.Pedestrian p = Ecm.of(event(walker(1, 0, 0, 1, 2, 3, 4)), sim(17, r -> r / 4.0, 0.3, 9), 0);
        assertEquals(3, p.n1());
        assertEquals(5, p.n2());
        assertEquals(0.09, p.ecm1Excluding(), 1e-12);
    }

    @Test
    void filledVariantComparesAgainstTheTargetByHand() {
        // Target del experimento: (4, 0). Filas 0, 4 y 8: (0,3)² cada una; frames 3 y 4: (3−4)² = 1 y 0.
        Ecm.Pedestrian p = Ecm.of(event(walker(1, 0, 0, 1, 2, 3, 4)), sim(17, r -> r / 4.0, 0.3, 9), 0);
        assertEquals((3 * 0.09 + 1 + 0) / 5, p.ecm1Filled(), 1e-12);
    }

    @Test
    void filledVariantAlsoCoversARunEndedBeforeTheWindow() {
        // Se cortó la corrida: no hay filas desde la 9. Es el caso de que todos se hayan retirado.
        Ecm.Pedestrian p = Ecm.of(event(walker(1, 0, 0, 1, 2, 3, 4)), sim(9, r -> r / 4.0, 0.3, 9), 0);
        assertEquals(3, p.n1());
        assertEquals((3 * 0.09 + 1 + 0) / 5, p.ecm1Filled(), 1e-12);
    }

    @Test
    void bothVariantsMatchWhenNobodyLeaves() {
        Ecm.Pedestrian p = Ecm.of(event(walker(1, 0, 0, 1, 2, 3, 4)), sim(17, r -> r / 4.0 + 0.2, 0.1, 17), 0);
        assertEquals(p.ecm1Excluding(), p.ecm1Filled(), 1e-15);
    }

    @Test
    void secondMetricUsesOnlyTheSimulatedPathBeforeLeaving() {
        // El simulado llega hasta x = 2 en la fila 8; los puntos experimentales 3 y 4 quedan a 1 y 2 m del último.
        Ecm.Pedestrian p = Ecm.of(event(walker(1, 0, 0, 1, 2, 3, 4)), sim(17, r -> r / 4.0, 0, 9), 0);
        assertEquals((0 + 0 + 0 + 1 + 4) / 5.0, p.ecm2(), 1e-12);
    }

    @Test
    void eventValueIsTheMeanOfItsTwoPedestrians() {
        Ecm.Event e = new Ecm.Event(new Ecm.Pedestrian[] { new Ecm.Pedestrian(1, 2, 3, 5, 5), new Ecm.Pedestrian(3, 4, 7, 5, 5) });
        assertEquals(2, e.ecm1Excluding());
        assertEquals(3, e.ecm1Filled());
        assertEquals(5, e.ecm2());
    }

    @Test
    void onlyTheCommonWindowCounts() {
        // El peatón 0 sigue hasta el frame 6, pero la ventana termina en el 4 (el otro peatón ya no está)
        Ecm.Pedestrian p = Ecm.of(event(walker(1, 0, 0, 1, 2, 3, 4, 5, 6)), sim(17, r -> r / 4.0, 0, 17), 0);
        assertEquals(5, p.n2());
    }
}
