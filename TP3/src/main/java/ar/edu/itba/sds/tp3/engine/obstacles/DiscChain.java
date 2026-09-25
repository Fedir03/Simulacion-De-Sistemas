package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.*;

/** Cadena de discos iguales centrados sobre una polilínea: pared de obstáculos chicos que
 * sigue una curva. Los discos se reparten uniformemente por longitud de arco; se usa la
 * mayor cantidad que no produce solapamientos y se exige que el hueco entre discos
 * consecutivos sea menor que maxGap, para que ninguna partícula atraviese la cadena.
 */
final class DiscChain {
    private DiscChain() { }

    /** @param closed si la polilínea se cierra sobre sí misma (el último punto se une al primero). */
    static List<Obstacle> along(double[] xs, double[] ys, boolean closed, double rho, double maxGap) {
        int m = xs.length;
        double[] arc = new double[m + 1];
        for (int i = 1; i <= m; i++) {
            if (i == m && !closed) { arc[i] = arc[i - 1]; break; }
            arc[i] = arc[i - 1] + Math.hypot(xs[i % m] - xs[i - 1], ys[i % m] - ys[i - 1]);
        }
        double total = closed ? arc[m] : arc[m - 1];
        for (int n = (int) Math.floor(total / (2 * rho)) + (closed ? 0 : 1); n >= (closed ? 3 : 2); n--) {
            List<Obstacle> chain = new ArrayList<>();
            for (int k = 0; k < n; k++) {
                double s = total * k / (closed ? n : n - 1);
                int i = Math.max(0, Math.min(m - 1, upper(arc, s) - 1));
                double seg = arc[i + 1] - arc[i], f = seg > 0 ? (s - arc[i]) / seg : 0;
                chain.add(new Obstacle(xs[i] + f * (xs[(i + 1) % m] - xs[i]), ys[i] + f * (ys[(i + 1) % m] - ys[i]), rho));
            }
            if (!valid(chain, closed, rho, maxGap)) continue;
            return chain;
        }
        throw new IllegalArgumentException("No se pudo cubrir la curva con discos de radio " + rho + " sin huecos ni solapamientos");
    }

    private static boolean valid(List<Obstacle> chain, boolean closed, double rho, double maxGap) {
        int n = chain.size();
        for (int i = 0; i < n; i++)
            for (int j = i + 1; j < n; j++)
                if (Math.hypot(chain.get(i).x() - chain.get(j).x(), chain.get(i).y() - chain.get(j).y()) < 2 * rho * (1 + 1e-9)) return false;
        for (int i = 0; i + 1 < n || closed && i < n; i++) {
            Obstacle a = chain.get(i), b = chain.get((i + 1) % n);
            if (Math.hypot(a.x() - b.x(), a.y() - b.y()) - 2 * rho >= maxGap)
                throw new IllegalArgumentException("La curva es demasiado curva o corta para una cadena sin huecos de discos de radio " + rho);
        }
        return true;
    }

    /** Primer índice con arc[i] > s. */
    private static int upper(double[] arc, double s) {
        int lo = 0, hi = arc.length;
        while (lo < hi) { int mid = (lo + hi) >>> 1; if (arc[mid] <= s) lo = mid + 1; else hi = mid; }
        return lo;
    }
}
