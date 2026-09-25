package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.*;

/** Red triangular de discos equidistantes, como los clavos de un tablero de Galton.
 * Columnas perpendiculares al eje longitudinal, separadas s·√3/2, con discos cada s y
 * cada columna desplazada s/2 respecto de la anterior: todo disco está a distancia s de
 * sus vecinos. La red se centra en (L/2, W/2), así es simétrica respecto de ambos ejes.
 * Se omiten los discos que dejarían un paso de 2r o menos contra una pared o contra un
 * obstáculo existente, para no formar pasillos por donde una partícula no pase.
 */
public final class LatticeObstacleGenerator implements ObstacleGenerator {
    private final double spacing, radius;

    /** @param radius radio de cada disco; NaN usa el radio de las partículas, el mínimo permitido. */
    public LatticeObstacleGenerator(double spacing, double radius) {
        if (!(spacing > 0) || !Double.isFinite(spacing)) throw new IllegalArgumentException("Separación de la red debe ser positiva");
        if (!Double.isNaN(radius) && !(radius > 0 && Double.isFinite(radius))) throw new IllegalArgumentException("Radio de obstáculo debe ser positivo");
        this.spacing = spacing;
        this.radius = radius;
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed) {
        return generate(c, seed, List.of());
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed, List<Obstacle> existing) {
        // Un paso de exactamente 2r solo admite una trayectoria tangente: se exige algo más.
        double rho = Double.isNaN(radius) ? c.radius() : radius, pass = 2 * c.radius() * (1 + 1e-6);
        if (spacing - 2 * rho < pass) throw new IllegalArgumentException("Separación demasiado chica: una partícula no pasa entre discos vecinos");
        double column = spacing * Math.sqrt(3) / 2;
        int kMax = (int) Math.ceil(c.length() / 2 / column), jMax = (int) Math.ceil(c.width() / 2 / spacing) + 1;
        List<Obstacle> result = new ArrayList<>();
        for (int k = -kMax; k <= kMax; k++)
            for (int j = -jMax; j <= jMax; j++) {
                double x = c.length() / 2 + k * column, y = c.width() / 2 + (j + (Math.abs(k) % 2) * 0.5) * spacing;
                double wall = Math.min(Math.min(x, c.length() - x), Math.min(y, c.width() - y));
                if (wall - rho < pass) continue;
                if (existing.stream().anyMatch(o -> Math.hypot(x - o.x(), y - o.y()) - o.radius() - rho < pass)) continue;
                result.add(new Obstacle(x, y, rho));
            }
        if (result.isEmpty()) throw new IllegalArgumentException("La red no deja ningún obstáculo dentro de la mesa");
        return List.copyOf(result);
    }
}
