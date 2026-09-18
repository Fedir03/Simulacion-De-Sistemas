package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.*;

/** Rellena una región bloqueada con discos fijos, del más grande al más chico.
 * En cada paso ubica el mayor disco posible centrado en un punto de la grilla donde
 * todavía entra el centro de una partícula. Termina cuando no queda ninguno: así no
 * quedan huecos en la región bloqueada donde una partícula pueda nacer atrapada.
 * Cada disco tiene radio ≥ r porque solamente se centra donde cabe una partícula.
 * Se repite con grillas de paso grid, grid/2 y grid/4 para cubrir huecos menores que la grilla.
 */
public final class RegionFill {
    /** Región a bloquear, descripta por su distancia a la zona libre. */
    @FunctionalInterface
    public interface Region {
        /** Distancia desde (x, y) hasta la zona libre; ≤ 0 si el punto es libre. */
        double distanceToFree(double x, double y);
    }

    private static final double EPS = 1e-9;
    private static final int MAX_OBSTACLES = 20_000, REFINEMENTS = 3;

    private RegionFill() { }

    /** @param maxRadius radio máximo de cada disco (infinito para no limitarlo).
     *  @param grid separación de la grilla más gruesa, en metros. */
    public static List<Obstacle> fill(SimulationConfig c, Region region, double maxRadius, double grid) {
        return fill(c, region, maxRadius, grid, List.of());
    }

    /** Igual, respetando obstáculos ya ubicados; devuelve solamente los nuevos. */
    public static List<Obstacle> fill(SimulationConfig c, Region region, double maxRadius, double grid, List<Obstacle> existing) {
        if (!(grid > 0) || !(maxRadius >= c.radius() + 2 * EPS)) throw new IllegalArgumentException("Grilla o radio máximo de relleno inválidos");
        List<Obstacle> obstacles = new ArrayList<>(existing);
        for (int pass = 0; pass < REFINEMENTS; pass++) fillPass(c, region, maxRadius, grid / (1 << pass), obstacles);
        return List.copyOf(obstacles.subList(existing.size(), obstacles.size()));
    }

    private static void fillPass(SimulationConfig c, Region region, double maxRadius, double step, List<Obstacle> obstacles) {
        double r = c.radius(), lo = r + 2 * EPS;
        // La grilla incluye las rectas extremas donde puede estar el centro de una partícula.
        int nx = (int) Math.ceil((c.length() - 2 * lo) / step) + 1, ny = (int) Math.ceil((c.width() - 2 * lo) / step) + 1;
        if ((long) nx * ny > 100_000_000L) throw new IllegalArgumentException("Grilla de relleno demasiado fina");
        double sx = (c.length() - 2 * lo) / (nx - 1), sy = (c.width() - 2 * lo) / (ny - 1);
        // Candidatos: puntos bloqueados que admiten el centro de una partícula.
        // limit acota el radio por las paredes, la zona libre y maxRadius; clearance, por los discos ya ubicados.
        double[] xs = new double[1024], ys = new double[1024], limit = new double[1024], clearance = new double[1024];
        int size = 0;
        for (int i = 0; i < nx; i++)
            for (int j = 0; j < ny; j++) {
                double x = lo + i * sx, y = lo + j * sy;
                double free = region.distanceToFree(x, y);
                if (!(free > 0)) continue;
                double wall = Math.min(Math.min(x, c.length() - x), Math.min(y, c.width() - y));
                // Cerca del borde de la zona libre se admite invadirla hasta r para no dejar ranuras.
                double cap = Math.min(Math.min(wall, Math.max(lo, free)), maxRadius), gap = Double.POSITIVE_INFINITY;
                for (Obstacle o : obstacles) {
                    gap = Math.min(gap, Math.hypot(x - o.x(), y - o.y()) - o.radius());
                    if (gap < r + EPS) break;
                }
                if (Math.min(cap, gap) < r + EPS) continue;
                if (size == xs.length) {
                    xs = Arrays.copyOf(xs, 2 * size); ys = Arrays.copyOf(ys, 2 * size);
                    limit = Arrays.copyOf(limit, 2 * size); clearance = Arrays.copyOf(clearance, 2 * size);
                }
                xs[size] = x; ys[size] = y; limit[size] = cap; clearance[size++] = gap;
            }
        while (size > 0) {
            int best = 0;
            for (int k = 1; k < size; k++)
                if (Math.min(limit[k], clearance[k]) > Math.min(limit[best], clearance[best])) best = k;
            double cx = xs[best], cy = ys[best], radius = Math.min(limit[best], clearance[best]) - EPS;
            obstacles.add(new Obstacle(cx, cy, radius));
            if (obstacles.size() > MAX_OBSTACLES) throw new IllegalArgumentException("Relleno con demasiados obstáculos");
            int kept = 0;
            for (int k = 0; k < size; k++) {
                double gap = Math.min(clearance[k], Math.hypot(xs[k] - cx, ys[k] - cy) - radius);
                // Un punto sin lugar para otro disco de radio r ya tampoco admite una partícula.
                if (Math.min(limit[k], gap) < r + EPS) continue;
                xs[kept] = xs[k]; ys[kept] = ys[k]; limit[kept] = limit[k]; clearance[kept++] = gap;
            }
            size = kept;
        }
    }
}
