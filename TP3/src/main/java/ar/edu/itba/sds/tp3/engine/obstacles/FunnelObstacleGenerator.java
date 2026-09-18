package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.List;

/** Embudos hacia ambos arcos: bloquea las cuatro esquinas detrás de rectas que van
 * desde cada palo del arco hasta la pared larga, a distancia funnelLength de la pared corta.
 * Las esquinas se rellenan con {@link RegionFill}.
 */
public final class FunnelObstacleGenerator implements ObstacleGenerator {
    private final double funnelLength, maxRadius, grid;

    public FunnelObstacleGenerator(double funnelLength, double maxRadius, double grid) {
        if (!Double.isFinite(funnelLength) || funnelLength <= 0)
            throw new IllegalArgumentException("Largo de embudo debe ser positivo");
        this.funnelLength = funnelLength;
        this.maxRadius = maxRadius;
        this.grid = grid;
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed) {
        return generate(c, seed, List.of());
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed, List<Obstacle> existing) {
        double a = funnelLength, post = (c.width() + c.goalWidth()) / 2;
        if (a > c.length() / 2 || post >= c.width())
            throw new IllegalArgumentException("El embudo debe ocupar a lo sumo media mesa y el arco ser más angosto que W");
        // Por simetría se trabaja en la esquina superior izquierda: palo P=(0, post), Q=(a, W).
        double ux = a, uy = c.width() - post, norm = Math.hypot(ux, uy);
        return RegionFill.fill(c, (x, y) -> {
            double fx = Math.min(x, c.length() - x), fy = Math.max(y, c.width() - y);
            double px = fx, py = fy - post;
            // Del lado de la esquina respecto de la recta PQ; la distancia a la zona libre es la del segmento PQ.
            if (ux * py - uy * px <= 0) return 0;
            double s = Math.max(0, Math.min(1, (px * ux + py * uy) / (norm * norm)));
            return Math.hypot(px - s * ux, py - s * uy);
        }, maxRadius, grid, existing);
    }
}
