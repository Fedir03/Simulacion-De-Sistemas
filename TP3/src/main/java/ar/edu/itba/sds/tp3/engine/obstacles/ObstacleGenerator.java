package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.List;

/** Estrategia independiente de la generación de partículas y del simulador.
 * Implementaciones nuevas pueden recibir sus parámetros en el constructor.
 * StageGeneration valida la geometría resultante antes de ubicar partículas.
 */
@FunctionalInterface
public interface ObstacleGenerator {
    List<Obstacle> generate(SimulationConfig config, long seed);
}
