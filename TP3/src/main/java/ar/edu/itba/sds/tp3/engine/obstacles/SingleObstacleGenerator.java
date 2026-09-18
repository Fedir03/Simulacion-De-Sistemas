package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.List;

/** Un único obstáculo en (x, y); NaN en una coordenada la ubica en el centro de la mesa.
 * Permite barrer, por ejemplo, un obstáculo grande sobre el eje longitudinal.
 */
public final class SingleObstacleGenerator implements ObstacleGenerator {
    private final double x, y, radius;

    public SingleObstacleGenerator(double x, double y, double radius) {
        if (!Double.isFinite(radius) || radius <= 0) throw new IllegalArgumentException("Radio de obstáculo debe ser positivo");
        this.x = x;
        this.y = y;
        this.radius = radius;
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed) {
        return List.of(new Obstacle(Double.isNaN(x) ? c.length() / 2 : x, Double.isNaN(y) ? c.width() / 2 : y, radius));
    }
}
