package ar.edu.itba.sds.tp1;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ParticleGeneratorTest {

    @Test
    void generatedParticlesDoNotOverlap() {
        List<Particle> particles = new ParticleGenerator(7).generate(150, 20);

        for (int i = 0; i < particles.size(); i++) {
            for (int j = i + 1; j < particles.size(); j++) {
                Particle a = particles.get(i);
                Particle b = particles.get(j);
                double centerDistance = Math.hypot(a.x() - b.x(), a.y() - b.y());
                assertTrue(centerDistance >= a.radius() + b.radius(),
                        "Partículas %d y %d se superponen".formatted(a.id(), b.id()));
            }
        }
    }

    @Test
    void generatedRadiiFallWithinRequestedRange() {
        double minRadius = 0.5;
        double maxRadius = 1.0;
        List<Particle> particles = new ParticleGenerator(7, minRadius, maxRadius).generate(50, 30);

        for (Particle p : particles) {
            assertTrue(p.radius() >= minRadius && p.radius() <= maxRadius,
                    "Radio fuera de rango: " + p.radius());
        }
    }

    @Test
    void generateThrowsWhenSpaceIsTooSmallForRequestedN() {
        ParticleGenerator generator = new ParticleGenerator(7);

        assertThrows(IllegalStateException.class, () -> generator.generate(1000, 2.0));
    }
}
