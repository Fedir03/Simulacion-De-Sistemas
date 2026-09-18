package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.List;

/** Un disco de radio R en cada palo de ambos arcos: tangente a la pared corta, con su punto
 * más cercano al arco a la altura del palo, (R, W/2 ± (d/2 + R)) y sus simétricos en x = L - R.
 * Estrecha la entrada del arco y desvía hacia él a las partículas que corren junto a la pared.
 */
public final class PostsObstacleGenerator implements ObstacleGenerator {
    private final double radius;

    public PostsObstacleGenerator(double radius) {
        if (!Double.isFinite(radius) || radius <= 0) throw new IllegalArgumentException("Radio de obstáculo debe ser positivo");
        this.radius = radius;
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed) {
        double low = c.width() / 2 - c.goalWidth() / 2 - radius, high = c.width() / 2 + c.goalWidth() / 2 + radius;
        return List.of(new Obstacle(radius, low, radius), new Obstacle(radius, high, radius),
                new Obstacle(c.length() - radius, low, radius), new Obstacle(c.length() - radius, high, radius));
    }
}
