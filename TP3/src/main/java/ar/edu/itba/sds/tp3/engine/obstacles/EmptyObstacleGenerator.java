package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.List;

/** Mesa vacía para comparar con configuraciones con obstáculos. */
public final class EmptyObstacleGenerator implements ObstacleGenerator {
    @Override public List<Obstacle> generate(SimulationConfig config, long seed) {
        return List.of();
    }
}
