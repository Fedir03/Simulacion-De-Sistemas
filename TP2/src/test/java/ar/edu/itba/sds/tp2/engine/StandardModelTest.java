package ar.edu.itba.sds.tp2.engine;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class StandardModelTest {

    private static final double DELTA = 1e-9;
    private static final double TWO_PI = 2 * Math.PI;

    @Test
    void includeSelfTrueNoNeighborsZeroEtaReturnsOwnTheta() {
        VicsekParticle self = new VicsekParticle(1, 0.0, 0.0, 1.2345);

        double result = new StandardModel(true).nextAngle(self, List.of(), 0.0, new Random(1));

        assertEquals(self.theta(), result, DELTA);
    }

    @Test
    void includeSelfFalseNoNeighborsZeroEtaFallsBackToNoiseOnly() {
        VicsekParticle self = new VicsekParticle(1, 0.0, 0.0, 1.2345);

        // Con includeSelf=false y sin vecinos, la lista de thetas queda vacía: no debe llamar a
        // vectorialAverage (que tira IllegalArgumentException con lista vacía), sino caer al
        // mismo fallback de "solo ruido" que VoterModel sin vecinos.
        double result = new StandardModel(false).nextAngle(self, List.of(), 0.0, new Random(1));

        assertEquals(self.theta(), result, DELTA);
    }

    @Test
    void includeSelfChangesResultWithOneNeighbor() {
        VicsekParticle self = new VicsekParticle(1, 0.0, 0.0, 0.0);
        VicsekParticle neighbor = new VicsekParticle(2, 0.0, 0.0, Math.PI / 2);
        List<VicsekParticle> neighbors = List.of(neighbor);

        double withSelf = new StandardModel(true).nextAngle(self, neighbors, 0.0, new Random(1));
        double withoutSelf = new StandardModel(false).nextAngle(self, neighbors, 0.0, new Random(1));

        // includeSelf=true: promedio de [0, π/2] -> vector (1,1) -> atan2 = π/4.
        assertEquals(Math.PI / 4, withSelf, DELTA);
        // includeSelf=false: promedio de [π/2] solo -> π/2 exacto.
        assertEquals(Math.PI / 2, withoutSelf, DELTA);
        assertNotEquals(withSelf, withoutSelf, DELTA);
    }

    @Test
    void delegatesToVectorialAverageForWrapAround() {
        VicsekParticle self = new VicsekParticle(1, 0.0, 0.0, 0.0);
        List<VicsekParticle> neighbors = List.of(
                new VicsekParticle(2, 0.0, 0.0, 0.1),
                new VicsekParticle(3, 0.0, 0.0, TWO_PI - 0.1)
        );

        // includeSelf=false para que el promedio sea exactamente sobre [0.1, 2π-0.1], el mismo
        // caso que AngleMathTest.vectorialAverageWrapAround: tiene que dar cerca de 0, no cerca
        // de π como daría un promedio aritmético ingenuo — confirma que StandardModel delega en
        // AngleMath en vez de reimplementar el promedio.
        double result = new StandardModel(false).nextAngle(self, neighbors, 0.0, new Random(1));

        boolean nearZero = result < DELTA || result > TWO_PI - DELTA;
        assertTrue(nearZero, "esperado cerca de 0, dio " + result);
    }

    @Test
    void sameSeedGivesSameResultWithNoise() {
        VicsekParticle self = new VicsekParticle(1, 0.0, 0.0, 0.0);
        List<VicsekParticle> neighbors = List.of(
                new VicsekParticle(2, 0.0, 0.0, 0.5),
                new VicsekParticle(3, 0.0, 0.0, 2.5)
        );

        double resultA = new StandardModel(true).nextAngle(self, neighbors, 0.3, new Random(42));
        double resultB = new StandardModel(true).nextAngle(self, neighbors, 0.3, new Random(42));

        assertEquals(resultA, resultB, DELTA);
    }
}