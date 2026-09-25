package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.*;

/** Embudos hacia ambos arcos: bloquea las cuatro esquinas detrás de rectas que van
 * desde cada palo del arco hasta la pared larga, a distancia funnelLength de la pared corta.
 * Con edgeRadius finito, cada recta es una cadena de discos de ese radio, con huecos menores
 * que el diámetro de una partícula y extremos apoyados en las paredes; el interior de las
 * esquinas se rellena después con {@link RegionFill}, detrás de la cadena.
 * Con edgeRadius NaN, todo se rellena con {@link RegionFill}.
 */
public final class FunnelObstacleGenerator implements ObstacleGenerator {
    private final double funnelLength, edgeRadius, maxRadius, grid;

    public FunnelObstacleGenerator(double funnelLength, double maxRadius, double grid) {
        this(funnelLength, Double.NaN, maxRadius, grid);
    }

    public FunnelObstacleGenerator(double funnelLength, double edgeRadius, double maxRadius, double grid) {
        if (!Double.isFinite(funnelLength) || funnelLength <= 0)
            throw new IllegalArgumentException("Largo de embudo debe ser positivo");
        if (!Double.isNaN(edgeRadius) && !(edgeRadius > 0 && Double.isFinite(edgeRadius)))
            throw new IllegalArgumentException("Radio de la frontera del embudo debe ser positivo");
        this.funnelLength = funnelLength;
        this.edgeRadius = edgeRadius;
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
        List<Obstacle> edge = Double.isNaN(edgeRadius) ? List.of() : edge(c, a, post, ux, uy, norm);
        List<Obstacle> base = new ArrayList<>(existing);
        base.addAll(edge);
        List<Obstacle> result = new ArrayList<>(edge);
        result.addAll(RegionFill.fill(c, (x, y) -> {
            double fx = Math.min(x, c.length() - x), fy = Math.max(y, c.width() - y);
            double px = fx, py = fy - post;
            // Del lado de la esquina respecto de la recta PQ; la distancia a la zona libre es la del segmento PQ.
            if (ux * py - uy * px <= 0) return 0;
            double s = Math.max(0, Math.min(1, (px * ux + py * uy) / (norm * norm)));
            return Math.hypot(px - s * ux, py - s * uy);
        }, maxRadius, grid, base));
        return List.copyOf(result);
    }

    /** Cadena de discos centrados sobre cada recta PQ, desde donde tocan la pared corta
     * (x = ρ) hasta donde tocan la larga (y = W - ρ), equiespaciados y sin solaparse. */
    private List<Obstacle> edge(SimulationConfig c, double a, double post, double ux, double uy, double norm) {
        // Los extremos quedan a 1e-9 m de las paredes para que el redondeo no los saque del dominio.
        double rho = edgeRadius, t0 = (rho + 1e-9) / ux, t1 = 1 - (rho + 1e-9) / uy;
        int gaps = (int) Math.floor((t1 - t0) * norm / (2 * rho));
        if (t0 >= t1 || gaps < 1) throw new IllegalArgumentException("El embudo es demasiado corto para su frontera de discos");
        if ((t1 - t0) * norm / gaps - 2 * rho >= 2 * c.radius())
            throw new IllegalArgumentException("La frontera del embudo dejaría huecos por donde pasa una partícula");
        List<Obstacle> chain = new ArrayList<>();
        for (int k = 0; k <= gaps; k++) {
            double t = t0 + (t1 - t0) * k / gaps, x = t * ux, y = post + t * uy;
            chain.add(new Obstacle(x, y, rho));
            chain.add(new Obstacle(x, c.width() - y, rho));
            chain.add(new Obstacle(c.length() - x, y, rho));
            chain.add(new Obstacle(c.length() - x, c.width() - y, rho));
        }
        return chain;
    }
}
