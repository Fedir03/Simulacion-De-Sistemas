package ar.edu.itba.sds.tp1;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** Generates non-overlapping circular particles inside a square domain. */
public final class ParticleGenerator {
    public static final double DEFAULT_MIN_RADIUS = 0.23;
    public static final double DEFAULT_MAX_RADIUS = 0.26;
    private static final int MAX_ATTEMPTS_PER_PARTICLE = 100000;

    private final Random random;
    private final double minRadius;
    private final double maxRadius;

    public ParticleGenerator(long seed) {
        this(seed, DEFAULT_MIN_RADIUS, DEFAULT_MAX_RADIUS);
    }

    public ParticleGenerator(long seed, double minRadius, double maxRadius) {
        if (minRadius <= 0 || maxRadius < minRadius) {
            throw new IllegalArgumentException("minRadius debe ser positivo y maxRadius >= minRadius");
        }
        this.random = new Random(seed);
        this.minRadius = minRadius;
        this.maxRadius = maxRadius;
    }

    public List<Particle> generate(int n, double l) {
        if (n <= 0 || l <= 2 * maxRadius) {
            throw new IllegalArgumentException("N debe ser positivo y L debe ser mayor a " + (2 * maxRadius));
        }

        List<Particle> particles = new ArrayList<>(n);
        for (int id = 1; id <= n; id++) {
            particles.add(generateValidParticle(id, l, particles));
        }
        return particles;
    }

    private Particle generateValidParticle(int id, double l, List<Particle> existingParticles) {
        for (int attempt = 1; attempt <= MAX_ATTEMPTS_PER_PARTICLE; attempt++) {
            double radius = randomRadius();
            double x = radius + random.nextDouble() * (l - 2 * radius);
            double y = radius + random.nextDouble() * (l - 2 * radius);
            Particle candidate = new Particle(id, x, y, radius);

            if (!overlapsAny(candidate, existingParticles)) {
                return candidate;
            }
        }

        throw new IllegalStateException(
                "No se pudo ubicar la partícula %d tras %d intentos; reducir N o aumentar L."
                        .formatted(id, MAX_ATTEMPTS_PER_PARTICLE)
        );
    }

    private double randomRadius() {
        return minRadius + random.nextDouble() * (maxRadius - minRadius);
    }

    private boolean overlapsAny(Particle candidate, List<Particle> particles) {
        return particles.stream().anyMatch(other -> overlaps(candidate, other));
    }

    private boolean overlaps(Particle a, Particle b) {
        return Math.hypot(a.x() - b.x(), a.y() - b.y()) < a.radius() + b.radius();
    }
}
