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
    void sameSeedProducesIdenticalResults() {
        List<VicsekParticle> a = InitialConditionGenerator.generate(30, 10.0, new Random(42));
        List<VicsekParticle> b = InitialConditionGenerator.generate(30, 10.0, new Random(42));

        assertEquals(a, b);
    }
}