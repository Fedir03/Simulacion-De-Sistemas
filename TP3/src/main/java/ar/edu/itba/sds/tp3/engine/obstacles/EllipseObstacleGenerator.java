package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.*;

/** Mesa elíptica: elipse centrada en la mesa, con vértices en los arcos (semieje a = L/2) y
 * focos en x = focusX y x = L - focusX. Su borde dentro de la mesa es una cadena de discos de
 * radio edgeRadius y lo que queda fuera de la elipse se rellena con {@link RegionFill}.
 * Una trayectoria que pasa por un foco rebota en el borde y pasa por el otro.
 * En cada foco puede ubicarse un objeto: none, disc (disco concéntrico de radio focusSize),
 * line (recta vertical de discos de semilargo focusSize) o lens (lente biconvexa vertical de
 * semialto focusSize y semiancho lensWidth, con contorno de discos e interior relleno).
 */
public final class EllipseObstacleGenerator implements ObstacleGenerator {
    public enum FocusShape { NONE, DISC, LINE, LENS }

    private static final int SAMPLES = 20_000;
    private final double focusX, edgeRadius, focusSize, lensWidth, maxRadius, grid;
    private final FocusShape shape;

    public EllipseObstacleGenerator(double focusX, double edgeRadius, FocusShape shape, double focusSize,
                                    double lensWidth, double maxRadius, double grid) {
        if (!(focusX > 0) || !Double.isFinite(focusX)) throw new IllegalArgumentException("Foco de la elipse inválido");
        if (!Double.isNaN(edgeRadius) && !(edgeRadius > 0 && Double.isFinite(edgeRadius)))
            throw new IllegalArgumentException("Radio del borde de la elipse debe ser positivo");
        if (shape != FocusShape.NONE && !(focusSize > 0 && Double.isFinite(focusSize)))
            throw new IllegalArgumentException("Tamaño del objeto en el foco debe ser positivo");
        if (shape == FocusShape.LENS && !(lensWidth > 0 && lensWidth < focusSize))
            throw new IllegalArgumentException("Semiancho de la lente debe ser positivo y menor que su semialto");
        this.focusX = focusX;
        this.edgeRadius = edgeRadius;
        this.shape = shape;
        this.focusSize = focusSize;
        this.lensWidth = lensWidth;
        this.maxRadius = maxRadius;
        this.grid = grid;
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed) {
        return generate(c, seed, List.of());
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed, List<Obstacle> existing) {
        double cx = c.length() / 2, cy = c.width() / 2, a = cx, focal = cx - focusX;
        if (focal <= 0) throw new IllegalArgumentException("El foco debe estar a la izquierda del centro de la mesa (x < L/2)");
        double b = Math.sqrt(a * a - focal * focal), rho = Double.isNaN(edgeRadius) ? c.radius() : edgeRadius, gap = 2 * c.radius();
        List<Obstacle> placed = new ArrayList<>();
        // Borde: tramos de la elipse donde un disco de radio ρ entra en la mesa.
        double eps = 1e-9;
        boolean[] inside = new boolean[SAMPLES];
        double[] px = new double[SAMPLES], py = new double[SAMPLES];
        for (int i = 0; i < SAMPLES; i++) {
            double t = 2 * Math.PI * i / SAMPLES;
            px[i] = cx + a * Math.cos(t); py[i] = cy + b * Math.sin(t);
            inside[i] = px[i] >= rho + eps && px[i] <= c.length() - rho - eps && py[i] >= rho + eps && py[i] <= c.width() - rho - eps;
        }
        int start = 0;
        while (start < SAMPLES && inside[start]) start++;
        if (start == SAMPLES) throw new IllegalArgumentException("La elipse no toca las paredes");
        for (int i = 1; i <= SAMPLES; i++) {
            int k = (start + i) % SAMPLES;
            if (!inside[k] || inside[(k - 1 + SAMPLES) % SAMPLES]) continue;
            List<double[]> run = new ArrayList<>();
            for (int j = k; inside[j]; j = (j + 1) % SAMPLES) run.add(new double[]{px[j], py[j]});
            double[] rx = run.stream().mapToDouble(p -> p[0]).toArray(), ry = run.stream().mapToDouble(p -> p[1]).toArray();
            placed.addAll(DiscChain.along(rx, ry, false, rho, gap));
        }
        // Objetos en los focos.
        List<RegionFill.Region> lenses = new ArrayList<>();
        for (double fx : new double[]{focusX, c.length() - focusX}) {
            switch (shape) {
                case DISC -> placed.add(new Obstacle(fx, cy, focusSize));
                case LINE -> placed.addAll(DiscChain.along(new double[]{fx, fx}, new double[]{cy - focusSize, cy + focusSize}, false, rho, gap));
                case LENS -> {
                    // Intersección de dos círculos de radio R centrados en fx ± (R - w).
                    double h = focusSize, w = lensWidth, big = (h * h + w * w) / (2 * w), phi = Math.asin(h / big);
                    int half = 2000;
                    double[] lx = new double[2 * half], ly = new double[2 * half];
                    for (int i = 0; i < half; i++) {
                        double t = -phi + 2 * phi * i / half;
                        lx[i] = fx - (big - w) + big * Math.cos(t); ly[i] = cy + big * Math.sin(t);
                        lx[half + i] = fx + (big - w) - big * Math.cos(t); ly[half + i] = cy - big * Math.sin(t);
                    }
                    placed.addAll(DiscChain.along(lx, ly, true, rho, gap));
                    double left = fx - (big - w), right = fx + (big - w);
                    lenses.add((x, y) -> Math.min(big - Math.hypot(x - left, y - cy), big - Math.hypot(x - right, y - cy)));
                }
                case NONE -> { }
            }
        }
        List<Obstacle> base = new ArrayList<>(existing);
        base.addAll(placed);
        double e0 = a, e1 = b;
        RegionFill.Region region = (x, y) -> {
            double u = Math.abs(x - cx), v = Math.abs(y - cy);
            double outside = u * u / (e0 * e0) + v * v / (e1 * e1) > 1 ? distance(e0, e1, u, v) : 0;
            for (RegionFill.Region lens : lenses) outside = Math.max(outside, lens.distanceToFree(x, y));
            return outside;
        };
        List<Obstacle> result = new ArrayList<>(placed);
        result.addAll(RegionFill.fill(c, region, maxRadius, grid, base));
        return List.copyOf(result);
    }

    /** Distancia de (y0, y1), en el primer cuadrante, a la elipse de semiejes e0 ≥ e1 (Eberly). */
    public static double distance(double e0, double e1, double y0, double y1) {
        if (y1 > 0) {
            if (y0 > 0) {
                double z0 = y0 / e0, z1 = y1 / e1, g = z0 * z0 + z1 * z1 - 1;
                if (g == 0) return 0;
                double r0 = (e0 / e1) * (e0 / e1), n0 = r0 * z0, s0 = z1 - 1, s1 = g < 0 ? 0 : Math.hypot(n0, z1) - 1, s = 0;
                for (int i = 0; i < 200; i++) {
                    s = (s0 + s1) / 2;
                    if (s == s0 || s == s1) break;
                    double q0 = n0 / (s + r0), q1 = z1 / (s + 1), f = q0 * q0 + q1 * q1 - 1;
                    if (f > 0) s0 = s; else if (f < 0) s1 = s; else break;
                }
                return Math.hypot(r0 * y0 / (s + r0) - y0, y1 / (s + 1) - y1);
            }
            return Math.abs(y1 - e1);
        }
        double numer = e0 * y0, denom = e0 * e0 - e1 * e1;
        if (numer < denom) {
            double t = numer / denom;
            return Math.hypot(e0 * t - y0, e1 * Math.sqrt(1 - t * t));
        }
        return Math.abs(y0 - e0);
    }
}
