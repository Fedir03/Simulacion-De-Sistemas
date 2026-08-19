package ar.edu.itba.sds.tp2.engine;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AngleMathTest {

    private static final double DELTA = 1e-9;
    private static final double TWO_PI = 2 * Math.PI;

    // --- normalize ---

    @Test
    void normalizeValueAlreadyInRange() {
        assertEquals(Math.PI / 2, AngleMath.normalize(Math.PI / 2), DELTA);
    }

    @Test
    void normalizeNegativeValue() {
        assertEquals(3 * Math.PI / 2, AngleMath.normalize(-Math.PI / 2), DELTA);
    }

    @Test
    void normalizeValueGreaterThanTwoPi() {
        assertEquals(Math.PI / 2, AngleMath.normalize(TWO_PI + Math.PI / 2), DELTA);
    }

    // --- vectorialAverage ---

    @Test
    void vectorialAverageAllSameAngle() {
        double theta = Math.PI / 3;
        assertEquals(theta, AngleMath.vectorialAverage(List.of(theta, theta, theta)), DELTA);
    }

    @Test
    void vectorialAverageWrapAround() {
        // Promedio ingenuo (aritmético) de 0.1 y (2π - 0.1) daría π, que es
        // el resultado opuesto al esperado. El promedio vectorial correcto
        // da cerca de 0 (ángulos casi opuestos alrededor del corte 0/2π).
        double result = AngleMath.vectorialAverage(List.of(0.1, TWO_PI - 0.1));
        boolean nearZero = result < DELTA || result > TWO_PI - DELTA;
        assertTrue(nearZero, "esperado cerca de 0, dio " + result);
    }

    @Test
    void vectorialAverageOppositeAnglesNearCancellation() {
        // [0, π] son direcciones opuestas, pero en double no cancelan
        // exacto: Math.cos(Math.PI) da -1.0 exacto, mientras que
        // Math.sin(Math.PI) da 1.2246e-16 (no 0.0 exacto, residuo de
        // redondeo documentado de Math.sin). Por eso el vector resultante
        // no es (0, 0) sino un vector casi-nulo apuntando levemente hacia
        // +y, y atan2 da π/2 en vez de 0.0. No es un bug de AngleMath: es
        // el resultado real de sumar estos dos ángulos en punto flotante.
        assertEquals(Math.PI / 2, AngleMath.vectorialAverage(List.of(0.0, Math.PI)), DELTA);
    }

    @Test
    void atan2OfZeroZeroIsZeroInJava() {
        // Confirmación directa (independiente de vectorialAverage): cuando
        // el vector resultante SÍ es exactamente (0, 0), Math.atan2 en
        // Java da 0.0 por definición (no lanza ni da NaN).
        assertEquals(0.0, Math.atan2(0.0, 0.0), DELTA);
    }

    @Test
    void vectorialAverageEmptyListThrows() {
        assertThrows(IllegalArgumentException.class, () -> AngleMath.vectorialAverage(List.of()));
    }

    // --- addNoise ---

    @Test
    void addNoiseZeroEtaReturnsOriginalTheta() {
        double theta = 1.2345;
        assertEquals(theta, AngleMath.addNoise(theta, 0.0, new Random(42)), DELTA);
    }

    @Test
    void addNoisePositiveEtaStaysInRange() {
        Random random = new Random(7);
        double result = AngleMath.addNoise(-5.0, 1.0, random);
        assertTrue(result >= 0.0 && result < TWO_PI, "resultado fuera de [0, 2π): " + result);
    }
}