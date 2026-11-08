package ar.edu.itba.sds.tp5.engine.layer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** Fórmulas de la especificación en casos calculados a mano. i va por +x: su derecha es −y. */
class AvoidanceLayerTest {
    private static final LayerConstants C = LayerConstants.defaults();
    private static final double RHO = C.rho();

    private static double[] direction(AvoidanceLayer layer, double xj, double yj, double vxj, double vyj) {
        double[] out = new double[2];
        layer.direction(0, 0, xj, yj, vxj, vyj, 1, 1, 0, out);
        return out;
    }

    private static boolean active(AvoidanceLayer layer, double xj, double yj, double vxj, double vyj) {
        return layer.direction(0, 0, xj, yj, vxj, vyj, 1, 1, 0, new double[2]);
    }

    @Test
    void predictionMatchesAHandComputedCase() {
        // j en (4, 0,5) a −1 en x; i hipotético a +1: w = (−2, 0), t* = 2, se cruzan a 0,5 en y
        CollisionPrediction p = CollisionPrediction.of(0, 0, 4, 0.5, -1, 0, 1, 1, 0);
        assertEquals(2, p.tStar(), 1e-12);
        assertEquals(0.5, p.dMin(), 1e-12);
        assertEquals(0, p.closestX(), 1e-12);
        assertEquals(0.5, p.closestY(), 1e-12);
    }

    @Test
    void noPredictionWhenBothMoveTheSame() {
        assertNull(CollisionPrediction.of(0, 0, 4, 0, 1, 0, 1, 1, 0));
    }

    @Test
    void collisionNeedsAFutureClosestApproachInsideTheHorizonAndTheSpace() {
        CollisionPrediction p = CollisionPrediction.of(0, 0, 4, 0.5, -1, 0, 1, 1, 0);
        assertTrue(p.isCollision(2, RHO));              // t* = t_a entra
        assertFalse(p.isCollision(1.99, RHO));
        assertFalse(p.isCollision(5, 0.5));             // d_min = ρ no entra
        assertFalse(CollisionPrediction.of(0, 0, -4, 0.5, -1, 0, 1, 1, 0).isCollision(5, RHO));  // ya pasó: t* < 0
    }

    @Test
    void layerADodgesToTheSideOppositeTheOther() {
        AvoidanceLayer a = LateralTargetLayer.a(2, 1, C);
        double norm = Math.hypot(2, 1);
        double[] left = direction(a, 4, 0.5, -1, 0);    // j a la izquierda de i: esquiva a la derecha (−y)
        assertEquals(2 / norm, left[0], 1e-12);
        assertEquals(-1 / norm, left[1], 1e-12);
        double[] right = direction(a, 4, -0.5, -1, 0);  // j a la derecha: esquiva a la izquierda
        assertEquals(2 / norm, right[0], 1e-12);
        assertEquals(1 / norm, right[1], 1e-12);
    }

    @Test
    void lateralLayersBreakTiesToTheRight() {
        double[] tie = direction(LateralTargetLayer.a(2, 1, C), 4, 0.05, -1, 0);    // |s_c| ≤ ε: desempate
        assertTrue(tie[1] < 0);
        double[] beyond = direction(LateralTargetLayer.a(2, 1, C), 4, -0.051, -1, 0);
        assertTrue(beyond[1] > 0);
    }

    @Test
    void layerBScalesTheOffsetWithTheSeverity() {
        // d_min = 0,5: ℓ = 2 (0,9 − 0,5) = 0,8; x_T − x_i = (2, −0,8)
        double[] d = direction(LateralTargetLayer.b(2, 2, C), 4, 0.5, -1, 0);
        double norm = Math.hypot(2, 0.8);
        assertEquals(2 / norm, d[0], 1e-12);
        assertEquals(-0.8 / norm, d[1], 1e-12);
    }

    @Test
    void lateralLayersDoNothingOutsideTheHorizon() {
        double[] d = direction(LateralTargetLayer.a(1, 1, C), 4, 0.5, -1, 0);       // t* = 2 > t_a
        assertEquals(1, d[0]);
        assertEquals(0, d[1]);
        assertFalse(active(LateralTargetLayer.a(1, 1, C), 4, 0.5, -1, 0));
    }

    @Test
    void layerFMatchesAHandComputedCase() {
        // j en (3, 0,6), t* = 1,5 y d_min = 0,6. e_ij = −(3; 0,6)/d, cos θ = 3/d
        double dist = Math.hypot(3, 0.6), ap = 0.5, bp = 2;
        double m = ap * Math.exp(-dist / bp) * (3 / dist);
        double ax = 1 - m * 3 / dist, ay = -m * 0.6 / dist, norm = Math.hypot(ax, ay);
        double[] d = direction(new RepulsiveDirectionLayer(ap, bp, C), 3, 0.6, -1, 0);
        assertEquals(ax / norm, d[0], 1e-12);
        assertEquals(ay / norm, d[1], 1e-12);
    }

    @Test
    void layerFIgnoresWhoIsBehindAndHasNoHorizon() {
        // t* > 0 pero j está detrás de i: fuera del semiplano de visión. j corre más rápido hacia i desde atrás
        assertFalse(active(new RepulsiveDirectionLayer(0.5, 2, C), -3, 0.2, 3, 0));
        // Muy lejos sigue activa: no hay t_a
        assertTrue(active(new RepulsiveDirectionLayer(0.5, 2, C), 500, 0.2, -1, 0));
    }

    @Test
    void layerFBreaksFrontalTiesToTheWalkersRight() {
        double[] exact = direction(new RepulsiveDirectionLayer(0.5, 2, C), 3, 0, -1, 0);
        assertTrue(exact[1] < 0, "desvío " + exact[1]);
        // Apenas a la izquierda, dentro de la banda: también a la derecha
        assertTrue(direction(new RepulsiveDirectionLayer(0.5, 2, C), 3, 0.05, -1, 0)[1] < 0);
        // Fuera de la banda, a la derecha de i: se aleja hacia la izquierda
        assertTrue(direction(new RepulsiveDirectionLayer(0.5, 2, C), 3, -0.6, -1, 0)[1] > 0);
    }

    @Test
    void layerFMetricTieUsesTheLateralOffsetAtClosestApproach() {
        AvoidanceLayer f = new RepulsiveDirectionLayer(0.5, 2, C);
        // Con w = (−2, 0), s_c es el desvío en y: |s_c| = 0,05 todavía es desempate y va a la derecha (−y)
        assertTrue(direction(f, 3, 0.05, -1, 0)[1] < 0);
        // Apenas afuera, j a la derecha de i: i se aleja hacia la izquierda, no hay desempate
        assertTrue(direction(f, 3, -0.051, -1, 0)[1] > 0);
        // j está a la derecha pero se viene a la recta de i: s_c = 0 es desempate, así que igual va a la derecha.
        // Sin desempate se alejaría hacia la izquierda, como en el caso anterior
        double vy = 0.1 / 1.5;      // de y = −0,1 a y = 0 en t* = 1,5
        assertEquals(0, CollisionPrediction.of(0, 0, 3, -0.1, -1, vy, 1, 1, 0).closestY(), 1e-12);
        assertTrue(direction(f, 3, -0.1, -1, vy)[1] < 0);
    }

    /** Con s_c = 0 y el otro bien afuera del eje, rotar e_ij 5° no alcanza: el desvío igual tiene que ir a la derecha. */
    @Test
    void layerFMetricTieGoesRightEvenWithTheOtherFarFromTheAxis() {
        AvoidanceLayer f = new RepulsiveDirectionLayer(0.5, 2, C);
        // j en (3; −0,6), viene a la recta de i: t* = 1,5 y s_c = 0. Rotar e_ij lo mandaría a la izquierda (+y)
        double vy = 0.6 / 1.5;
        assertEquals(0, CollisionPrediction.of(0, 0, 3, -0.6, -1, vy, 1, 1, 0).closestY(), 1e-12);
        double[] d = direction(f, 3, -0.6, -1, vy);
        assertTrue(d[1] < 0, "desvío " + d[1]);
        // Se comporta como el frontal exacto, con la intensidad de esta distancia
        double dist = Math.hypot(3, 0.6), m = 0.5 * Math.exp(-dist / 2) * (3 / dist);
        double a = Math.toRadians(5), ax = 1 - m * Math.cos(a), ay = -m * Math.sin(a), norm = Math.hypot(ax, ay);
        assertEquals(ax / norm, d[0], 1e-12);
        assertEquals(ay / norm, d[1], 1e-12);
        // Del otro lado e_ij ya apunta a la derecha y la rotación lo aumenta: sigue siendo la rotación de e_ij
        double[] other = direction(f, 3, 0.6, -1, -vy);
        assertTrue(other[1] < d[1]);
    }

    /** Sentido de la rotación: la desviación tiene que ir a la derecha del peatón, en su propio sistema de referencia. */
    @Test
    void frontalTieDodgesToTheWalkersOwnRightForAnyHeading() {
        AvoidanceLayer[] layers = { new RepulsiveDirectionLayer(0.5, 2, C), LateralTargetLayer.a(5, 1, C), LateralTargetLayer.b(5, 2, C) };
        for (double degrees : new double[] { 0, 180, 90, -90, 37, 211 }) {
            double ex = Math.cos(Math.toRadians(degrees)), ey = Math.sin(Math.toRadians(degrees));
            double rightX = ey, rightY = -ex;
            for (AvoidanceLayer layer : layers) {
                double[] out = new double[2];
                // j de frente exacto, a 3 m sobre el rumbo de i, viniendo hacia i
                assertTrue(layer.direction(1, 2, 1 + 3 * ex, 2 + 3 * ey, -ex, -ey, 1, ex, ey, out), layer.label());
                double right = out[0] * rightX + out[1] * rightY;
                assertTrue(right > 1e-3, layer.label() + " con rumbo " + degrees + "°: componente a la derecha = " + right);
            }
        }
    }

    /** Otro adelante con d_ij dado y 0,3 m de desvío lateral, de frente. Devuelve el giro en grados, con signo. */
    private static double turnDegrees(AvoidanceLayer layer, double dij) {
        double[] d = direction(layer, Math.sqrt(dij * dij - 0.09), 0.3, -1.2, 0);
        return Math.toDegrees(Math.atan2(d[1], d[0]));
    }

    /** Auditoría, ítem 2: valores calculados a mano. El otro está a la izquierda (+y), así que i gira hacia −y. */
    @Test
    void layerFTurnMatchesTheHandComputedAngles() {
        AvoidanceLayer f = new RepulsiveDirectionLayer(0.9, 2.5, C);
        assertEquals(-0.476, turnDegrees(f, 5), 0.002);
        assertEquals(-5.664, turnDegrees(f, 2), 0.002);
    }

    @Test
    void layerFHasNoEffectWhenTheOtherIsBehindEvenWithAPredictedCollision() {
        // Viene de atrás, más rápido: t* > 0 y d_min < ρ, pero cos θ_j < 0
        double[] d = direction(new RepulsiveDirectionLayer(0.9, 2.5, C), -2, 0.3, 3, 0);
        assertEquals(1, d[0]);
        assertEquals(0, d[1]);
        // Justo a un costado: cos θ_j = 0 tampoco entra
        assertFalse(active(new RepulsiveDirectionLayer(0.9, 2.5, C), 0, 0.5, 1, 0));
    }

    @Test
    void layerFWithNullIntensityReturnsTheFinalDirectionExactly() {
        double[] d = direction(new RepulsiveDirectionLayer(0, 2.5, C), 3, 0.3, -1.2, 0);
        assertEquals(1, d[0]);
        assertEquals(0, d[1]);
    }

    @Test
    void layerFWithHugeRangeHasAnExponentialOfOne() {
        double dist = 2, cos = Math.sqrt(dist * dist - 0.09) / dist, sin = 0.3 / dist, ap = 0.5;
        double ax = 1 - ap * cos * cos, ay = -ap * cos * sin, norm = Math.hypot(ax, ay);
        double[] d = direction(new RepulsiveDirectionLayer(ap, 1e9, C), Math.sqrt(dist * dist - 0.09), 0.3, -1.2, 0);
        assertEquals(ax / norm, d[0], 1e-8);
        assertEquals(ay / norm, d[1], 1e-8);
    }

    /** Auditoría, ítem 1: con A_p < 1 la suma nunca se anula, ni frontal y casi tocándose con el mayor A_p usado. */
    @Test
    void layerFStaysUnitWithoutAGuardWhenTheSumIsSmallest() {
        for (double dist : new double[] { 1e-6, 0.01, 0.5 }) {
            double[] d = direction(new RepulsiveDirectionLayer(0.99, 1000, C), dist, 0, -1.2, 0);
            assertEquals(1, Math.hypot(d[0], d[1]), 1e-12);
        }
    }

    @Test
    void layerFHorizonIsInfiniteByDefaultAndCanBeLimited() {
        assertTrue(active(new RepulsiveDirectionLayer(0.5, 2, C), 4, 0.5, -1, 0));          // t* = 2
        assertTrue(active(new RepulsiveDirectionLayer(0.5, 2, C.withFHorizon(2)), 4, 0.5, -1, 0));
        assertFalse(active(new RepulsiveDirectionLayer(0.5, 2, C.withFHorizon(1.99)), 4, 0.5, -1, 0));
    }

    /** Variante F1: sin compuerta actúa con solo estar en el semiplano; el desempate pide acercamiento futuro. */
    @Test
    void layerFWithoutTheGateActsOnWhoeverIsInTheHalfPlane() {
        LayerConstants open = C.withFVariant(false, 0);
        // Se cruzan a 3 m: d_min = 3 > ρ, no hay choque predicho
        assertFalse(active(new RepulsiveDirectionLayer(0.5, 2, C), 5, 3, -1, 0));
        double dist = Math.hypot(5, 3), m = 0.5 * Math.exp(-dist / 2) * (5 / dist);
        double ax = 1 - m * 5 / dist, ay = -m * 3 / dist, norm = Math.hypot(ax, ay);
        double[] d = direction(new RepulsiveDirectionLayer(0.5, 2, open), 5, 3, -1, 0);
        assertEquals(ax / norm, d[0], 1e-12);
        assertEquals(ay / norm, d[1], 1e-12);
        // Detrás sigue sin efecto
        assertFalse(active(new RepulsiveDirectionLayer(0.5, 2, open), -5, 3, -1, 0));
        // Exactamente adelante y alejándose (t* < 0): sin desempate, no hay desvío lateral
        assertEquals(0, direction(new RepulsiveDirectionLayer(0.5, 2, open), 5, 0, 3, 0)[1], 1e-15);
        // |w| ≈ 0: no hay predicción y no falla
        assertEquals(0, direction(new RepulsiveDirectionLayer(0.5, 2, open), 5, 0, 1, 0)[1], 1e-15);
    }

    /** Variante F2: d_ij − 2R solo en la exponencial, sin bajar de 0. */
    @Test
    void layerFBetweenEdgesOnlyChangesTheExponential() {
        LayerConstants edges = C.withFVariant(true, 0.5);
        double x = 3, y = 0.6, dist = Math.hypot(x, y), m = 0.5 * Math.exp(-(dist - 0.5) / 2) * (x / dist);
        double ax = 1 - m * x / dist, ay = -m * y / dist, norm = Math.hypot(ax, ay);
        double[] d = direction(new RepulsiveDirectionLayer(0.5, 2, edges), x, y, -1, 0);
        assertEquals(ax / norm, d[0], 1e-12);
        assertEquals(ay / norm, d[1], 1e-12);
        // Con solape la exponencial vale 1 como máximo: con A_p < 1 la suma no se anula
        double[] close = direction(new RepulsiveDirectionLayer(0.99, 0.25, edges), 0.3, 0.1, -1, 0);
        assertEquals(1, Math.hypot(close[0], close[1]), 1e-12);
        double[] atContact = direction(new RepulsiveDirectionLayer(0.99, 0.25, edges), 0.5 * 0.9, 0.1, -1, 0);
        assertEquals(1, Math.hypot(atContact[0], atContact[1]), 1e-12);
        assertTrue(close[0] > 0, "no se invierte: " + close[0]);
    }

    @Test
    void directionsAreUnitVectors() {
        for (AvoidanceLayer layer : new AvoidanceLayer[] { LateralTargetLayer.a(2, 2.5, C), LateralTargetLayer.b(3, 4, C), new RepulsiveDirectionLayer(0.9, 3, C) }) {
            for (double y : new double[] { -0.7, -0.2, 0, 0.1, 0.8 }) {
                double[] d = direction(layer, 2, y, -1, 0);
                assertEquals(1, Math.hypot(d[0], d[1]), 1e-12, layer.label());
            }
        }
    }

    @Test
    void parametersOutsideTheirRangeAreRejected() {
        assertThrows(IllegalArgumentException.class, () -> new RepulsiveDirectionLayer(1, 1, C));
        assertThrows(IllegalArgumentException.class, () -> new RepulsiveDirectionLayer(0.5, 0, C));
        assertThrows(IllegalArgumentException.class, () -> LateralTargetLayer.a(0, 1, C));
        assertThrows(IllegalArgumentException.class, () -> LateralTargetLayer.b(1, -1, C));
        assertThrows(IllegalArgumentException.class, () -> Layers.of("z", 1, 1, C));
    }
}
