package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.List;

/** Deja libre solamente el semicírculo de radio freeRadius centrado en el arco derecho
 * (L, W/2), o en cada arco con bothGoals, y rellena con {@link RegionFill} el resto de la mesa.
 * Con freeRadius = 0.3 L y un solo arco se bloquea el 70 % izquierdo del largo de la mesa.
 * Con ambos arcos forma un cuenco: un embudo de pared curva alrededor de cada arco.
 */
public final class SemicircleObstacleGenerator implements ObstacleGenerator {
    private final double freeRadius, maxRadius, grid;
    private final boolean bothGoals;

    public SemicircleObstacleGenerator(double freeRadius, boolean bothGoals, double maxRadius, double grid) {
        if (!Double.isFinite(freeRadius) || freeRadius <= 0)
            throw new IllegalArgumentException("Radio libre debe ser positivo");
        this.freeRadius = freeRadius;
        this.bothGoals = bothGoals;
        this.maxRadius = maxRadius;
        this.grid = grid;
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed) {
        return generate(c, seed, List.of());
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed, List<Obstacle> existing) {
        if (freeRadius >= c.length()) throw new IllegalArgumentException("El radio libre debe ser menor que L");
        return RegionFill.fill(c, (x, y) -> {
            double right = Math.hypot(x - c.length(), y - c.width() / 2);
            return (bothGoals ? Math.min(right, Math.hypot(x, y - c.width() / 2)) : right) - freeRadius;
        }, maxRadius, grid, existing);
    }
}
