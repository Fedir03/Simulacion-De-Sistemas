package ar.edu.itba.sds.tp4.engine.billiard;

import ar.edu.itba.sds.tp4.engine.cim.NeighborFinder;
import ar.edu.itba.sds.tp4.engine.cim.Particle;
import ar.edu.itba.sds.tp4.models.BilliardConfig;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Fuerza normal de contacto F = −k·ξ·e_n (Teórica 4, diapos 42–46; contacto si ξ > 0, enunciado) entre partículas,
 * con los obstáculos fijos y con la pared por partícula imagen. Los pares salen del {@link NeighborFinder}; obstáculos
 * y pared se recorren aparte, fuera de la grilla (D25).
 */
public final class ContactForces {
    /** Energía elástica Σ½kξ² de todos los contactos y cantidad de partículas que pasaron a usadas en esta llamada. */
    public record Result(double elasticEnergy, int newlyUsed) { }

    private final BilliardConfig c;
    private final NeighborFinder finder;
    private final double[] obstacleX;

    public ContactForces(BilliardConfig c, NeighborFinder finder) {
        this.c = c;
        this.finder = finder;
        this.obstacleX = c.hasObstacles() ? new double[]{-c.x0(), c.x0()} : new double[0];
    }

    /** Centros de los obstáculos, en (obstacleX[i], 0). */
    public double[] obstacleX() { return obstacleX.clone(); }

    /**
     * Escribe en fx, fy la fuerza total sobre cada partícula en las posiciones x, y. Una partícula fresca que toca un
     * obstáculo (ξ > 0) pasa a usada; nunca vuelve a fresca. Requiere |r| ≤ R (lo valida el CIM).
     */
    public Result compute(double[] x, double[] y, double[] fx, double[] fy, boolean[] used) {
        int n = x.length;
        double r = c.radius(), k = c.k(), big = c.domainRadius();
        double elastic = 0;
        int newlyUsed = 0;
        Arrays.fill(fx, 0);
        Arrays.fill(fy, 0);

        // Pares partícula-partícula: el id de la Particle es el índice en los arreglos
        List<Particle> particles = new ArrayList<>(n);
        for (int i = 0; i < n; i++) particles.add(new Particle(i, x[i], y[i], r));
        Map<Integer, Set<Integer>> contacts = finder.findNeighbors(particles, 2 * big, 0, false);
        for (int i = 0; i < n; i++)
            for (int j : contacts.get(i)) {
                if (j <= i) continue; // cada par una sola vez
                double dx = x[j] - x[i], dy = y[j] - y[i], d = Math.sqrt(dx * dx + dy * dy);
                double xi = 2 * r - d;
                if (xi <= 0) continue;
                // e_n = (r_j − r_i)/|r_j − r_i|; F_i = −k·ξ·e_n, F_j = −F_i
                double ex = dx / d, ey = dy / d;
                fx[i] -= k * xi * ex; fy[i] -= k * xi * ey;
                fx[j] += k * xi * ex; fy[j] += k * xi * ey;
                elastic += 0.5 * k * xi * xi;
            }

        for (int i = 0; i < n; i++) {
            // Obstáculos fijos de radio r (masa infinita: solo actúa la fuerza sobre i)
            for (double ox : obstacleX) {
                double dx = ox - x[i], dy = -y[i], d = Math.sqrt(dx * dx + dy * dy);
                double xi = 2 * r - d;
                if (xi <= 0) continue;
                fx[i] -= k * xi * dx / d; fy[i] -= k * xi * dy / d;
                elastic += 0.5 * k * xi * xi;
                if (!used[i]) { used[i] = true; newlyUsed++; }
            }
            // Pared: imagen fija de radio r en (R + r)·n̂, recalculada en cada llamada; ξ = 2r − |r_img − r_i| = |r_i| + r − R.
            // La imagen es fantasma: su energía no se suma, solo la elástica del contacto, una vez (D21)
            double d = Math.sqrt(x[i] * x[i] + y[i] * y[i]);
            if (d > big - r) {
                double xi = d + r - big;
                fx[i] -= k * xi * x[i] / d; fy[i] -= k * xi * y[i] / d;
                elastic += 0.5 * k * xi * xi;
            }
        }
        return new Result(elastic, newlyUsed);
    }
}
