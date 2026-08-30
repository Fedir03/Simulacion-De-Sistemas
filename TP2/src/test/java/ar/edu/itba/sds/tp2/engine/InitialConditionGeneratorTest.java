package ar.edu.itba.sds.tp2.engine;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class InitialConditionGeneratorTest {

    private static final double TWO_PI = 2 * Math.PI;

    @Test
    void generatesExpectedCountAndSequentialIds() {
        List<VicsekParticle> particles = InitialConditionGenerator.generate(50, 10.0, new Random(1));

        assertEquals(50, particles.size());
        for (int i = 0; i < particles.size(); i++) {
            assertEquals(i + 1, particles.get(i).id());
        }
    }

    @Test
    void positionsAndAnglesAreWithinExpectedRanges() {
        double l = 10.0;
        List<VicsekParticle> particles = InitialConditionGenerator.generate(200, l, new Random(2));

        for (VicsekParticle p : particles) {
            assertTrue(p.x() >= 0.0 && p.x() < l, "x fuera de rango: " + p.x());
            assertTrue(p.y() >= 0.0 && p.y() < l, "y fuera de rango: " + p.y());
            assertTrue(p.theta() >= 0.0 && p.theta() < TWO_PI, "theta fuera de rango: " + p.theta());
        }
    }

    @Test
    void fixedTheta0AppliesToEveryParticle() {
        List<VicsekParticle> particles = InitialConditionGenerator.generate(20, 10.0, new Random(7), 0.0);

        for (VicsekParticle p : particles) {
            assertEquals(0.0, p.theta());
        }
    }

    @Test
    void sameSeedGivesSamePositionsWithRandomAndFixedAngles() {
        List<VicsekParticle> random = InitialConditionGenerator.generate(30, 10.0, new Random(5), null);
        List<VicsekParticle> aligned = InitialConditionGenerator.generate(30, 10.0, new Random(5), 1.5);

        for (int i = 0; i < random.size(); i++) {
            assertEquals(random.get(i).x(), aligned.get(i).x(), "las posiciones x tienen que coincidir");
            assertEquals(random.get(i).y(), aligned.get(i).y(), "las posiciones y tienen que coincidir");
            assertEquals(1.5, aligned.get(i).theta());
        }
        assertTrue(random.stream().anyMatch(p -> p.theta() != 1.5),
                "los angulos random no deberian coincidir con el angulo fijo");
    }

    @Test
    void sameSeedProducesIdenticalResults() {
        List<VicsekParticle> a = InitialConditionGenerator.generate(30, 10.0, new Random(42));
        List<VicsekParticle> b = InitialConditionGenerator.generate(30, 10.0, new Random(42));

        assertEquals(a, b);
    }
}