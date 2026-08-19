package ar.edu.itba.sds.tp2.engine;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class VoterModelTest {

    private static final double DELTA = 1e-9;

    @Test
    void noNeighborsZeroEtaReturnsOwnTheta() {
        VicsekParticle self = new VicsekParticle(1, 0.0, 0.0, 1.2345);

        double result = new VoterModel().nextAngle(self, List.of(), 0.0, new Random(1));

        assertEquals(self.theta(), result, DELTA);
    }

    @Test
    void singleNeighborZeroEtaReturnsNeighborTheta() {
        VicsekParticle self = new VicsekParticle(1, 0.0, 0.0, 0.1);
        VicsekParticle neighbor = new VicsekParticle(2, 1.0, 0.0, 2.5);

        // Determinista: con un solo vecino, la elección al azar no tiene otra opción.
        double result = new VoterModel().nextAngle(self, List.of(neighbor), 0.0, new Random(999));

        assertEquals(neighbor.theta(), result, DELTA);
    }

    @Test
    void multipleNeighborsZeroEtaReturnsExactlyOneOfTheirThetas() {
        VicsekParticle self = new VicsekParticle(1, 0.0, 0.0, 0.0);
        List<VicsekParticle> neighbors = List.of(
                new VicsekParticle(2, 0.0, 0.0, 0.5),
                new VicsekParticle(3, 0.0, 0.0, 2.5),
                new VicsekParticle(4, 0.0, 0.0, 4.5)
        );

        double result = new VoterModel().nextAngle(self, neighbors, 0.0, new Random(7));

        assertTrue(result == 0.5 || result == 2.5 || result == 4.5,
                "esperado uno de {0.5, 2.5, 4.5} exacto (no promedio), dio " + result);
    }

    @Test
    void sameSeedGivesSameResult() {
        VicsekParticle self = new VicsekParticle(1, 0.0, 0.0, 0.0);
        List<VicsekParticle> neighbors = List.of(
                new VicsekParticle(2, 0.0, 0.0, 0.5),
                new VicsekParticle(3, 0.0, 0.0, 2.5),
                new VicsekParticle(4, 0.0, 0.0, 4.5)
        );

        double resultA = new VoterModel().nextAngle(self, neighbors, 0.3, new Random(42));
        double resultB = new VoterModel().nextAngle(self, neighbors, 0.3, new Random(42));

        assertEquals(resultA, resultB, DELTA);
    }

    @Test
    void distributionOverManyRunsIsRoughlyUniform() {
        VicsekParticle self = new VicsekParticle(1, 0.0, 0.0, 0.0);
        double thetaA = 0.5;
        double thetaB = 2.5;
        double thetaC = 4.5;
        List<VicsekParticle> neighbors = List.of(
                new VicsekParticle(2, 0.0, 0.0, thetaA),
                new VicsekParticle(3, 0.0, 0.0, thetaB),
                new VicsekParticle(4, 0.0, 0.0, thetaC)
        );

        int runs = 1000;
        int countA = 0;
        int countB = 0;
        int countC = 0;
        Random random = new Random(2024); // un único Random avanzando, no uno nuevo por vuelta
        VoterModel voterModel = new VoterModel();
        for (int i = 0; i < runs; i++) {
            double result = voterModel.nextAngle(self, neighbors, 0.0, random);
            if (result == thetaA) {
                countA++;
            } else if (result == thetaB) {
                countB++;
            } else if (result == thetaC) {
                countC++;
            } else {
                throw new AssertionError("resultado inesperado: " + result);
            }
        }

        // Tolerancia amplia a propósito: chequeo de "no hay sesgo grosero", no de precisión estadística.
        int min = (int) (runs * 0.20);
        int max = (int) (runs * 0.45);
        assertTrue(countA >= min && countA <= max, "countA fuera de rango: " + countA);
        assertTrue(countB >= min && countB <= max, "countB fuera de rango: " + countB);
        assertTrue(countC >= min && countC <= max, "countC fuera de rango: " + countC);
    }
}