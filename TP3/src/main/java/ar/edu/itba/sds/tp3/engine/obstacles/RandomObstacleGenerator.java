package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.*;

/** Centros uniformes por rechazo, discos de igual radio, sin solapamientos. */
public final class RandomObstacleGenerator implements ObstacleGenerator {
    private static final int MAX_ATTEMPTS_PER_OBSTACLE = 100_000;
    private final int count;
    private final double radius;

    public RandomObstacleGenerator(int count, double radius) {
        if (count <= 0 || !Double.isFinite(radius) || radius <= 0)
            throw new IllegalArgumentException("Cantidad y radio de obstáculos deben ser positivos");
        this.count = count;
        this.radius = radius;
    }

    @Override public List<Obstacle> generate(SimulationConfig config, long seed) {
        if (radius < config.radius() || 2 * radius > Math.min(config.length(), config.width()))
            throw new IllegalArgumentException("Radio de obstáculo incompatible con el dominio o menor que r");
        Random random = new Random(seed);
        List<Obstacle> obstacles = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            boolean placed = false;
            for (int attempt = 0; attempt < MAX_ATTEMPTS_PER_OBSTACLE; attempt++) {
                double x = radius + random.nextDouble() * (config.length() - 2 * radius);
                double y = radius + random.nextDouble() * (config.width() - 2 * radius);
                if (obstacles.stream().anyMatch(o -> Math.hypot(x - o.x(), y - o.y()) < radius + o.radius())) continue;
                obstacles.add(new Obstacle(x, y, radius));
                placed = true;
                break;
            }
            if (!placed) throw new IllegalArgumentException("No se pudieron ubicar " + count
                    + " obstáculos: límite de intentos en obstáculo " + (i + 1));
        }
        return List.copyOf(obstacles);
    }
}
