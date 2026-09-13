package ar.edu.itba.sds.tp3.engine;

import ar.edu.itba.sds.tp3.models.*;
import java.util.*;

/** Generación uniforme por rechazo; nunca deja discos solapados. */
public final class StageGeneration {
    private StageGeneration() { }
    public record Stage(SimulationConfig config, long seed, List<Particle> particles, List<Obstacle> obstacles) {
        public Stage {
            particles = List.copyOf(particles); obstacles = List.copyOf(obstacles);
            validate(config, particles, obstacles);
        }
    }

    public static Stage generate(SimulationConfig c, int n, long seed, List<Obstacle> obstacles) {
        if (n <= 0) throw new IllegalArgumentException("N debe ser positivo");
        validate(c, List.of(), obstacles);
        Random random = new Random(seed);
        List<Particle> particles = new ArrayList<>();
        for (int id = 1; id <= n; id++) {
            boolean placed = false;
            for (int attempt = 0; attempt < 100_000; attempt++) {
                double x = c.radius() + random.nextDouble() * (c.length() - 2 * c.radius());
                double y = c.radius() + random.nextDouble() * (c.width() - 2 * c.radius());
                if (particles.stream().anyMatch(p -> overlaps(x, y, c.radius(), p.x(), p.y(), p.radius()))
                        || obstacles.stream().anyMatch(o -> overlaps(x, y, c.radius(), o.x(), o.y(), o.radius()))) continue;
                double angle = random.nextDouble() * 2 * Math.PI;
                particles.add(new Particle(id, x, y, c.speed() * Math.cos(angle), c.speed() * Math.sin(angle), c.radius(), c.mass()));
                placed = true;
                break;
            }
            if (!placed) throw new IllegalArgumentException("No se pudieron ubicar " + n + " partículas: límite de intentos en partícula " + id);
        }
        return new Stage(c, seed, particles, obstacles);
    }

    public static void validate(SimulationConfig c, List<Particle> particles, List<Obstacle> obstacles) {
        Set<Integer> ids = new HashSet<>();
        for (int i = 0; i < obstacles.size(); i++) {
            Obstacle o = obstacles.get(i);
            inside(c, o.x(), o.y(), o.radius());
            if (o.radius() < c.radius()) throw new IllegalArgumentException("Radio de obstáculo menor que r");
            for (int j = 0; j < i; j++) {
                Obstacle b = obstacles.get(j);
                if (overlaps(o.x(), o.y(), o.radius(), b.x(), b.y(), b.radius()))
                    throw new IllegalArgumentException("Obstáculos solapados");
            }
        }
        for (int i = 0; i < particles.size(); i++) {
            Particle p = particles.get(i);
            inside(c, p.x(), p.y(), p.radius());
            if (!ids.add(p.id())) throw new IllegalArgumentException("ID repetido");
            for (Obstacle o : obstacles)
                if (overlaps(p.x(), p.y(), p.radius(), o.x(), o.y(), o.radius()))
                    throw new IllegalArgumentException("Partícula solapada con obstáculo");
            for (int j = 0; j < i; j++) {
                Particle b = particles.get(j);
                if (overlaps(p.x(), p.y(), p.radius(), b.x(), b.y(), b.radius()))
                    throw new IllegalArgumentException("Partículas solapadas");
            }
        }
    }
    private static void inside(SimulationConfig c, double x, double y, double r) {
        if (x < r || y < r || x > c.length() - r || y > c.width() - r)
            throw new IllegalArgumentException("Disco fuera del dominio");
    }
    private static boolean overlaps(double x, double y, double r, double bx, double by, double br) {
        return Math.hypot(x - bx, y - by) < r + br;
    }
}
