package ar.edu.itba.sds.tp1;

import java.util.List;
import java.util.Map;
import java.util.Set;

public interface NeighborFinder {
    Map<Integer, Set<Integer>> findNeighbors(List<Particle> particles, double l, double rc, boolean periodic);

    static void validatePeriodic(double l, double rc, double maxRadius) {
        if (l <= 2 * (rc + 2 * maxRadius)) {
            throw new IllegalArgumentException(String.format(
                "Condiciones periódicas inválidas: se requiere L > 2·(rc + 2·r_max). " +
                "L=%.4f, rc=%.4f, r_max=%.4f. " +
                "Reducí rc, los radios de partícula, o desactivá las condiciones periódicas.",
                l, rc, maxRadius
            ));
        }
    }

    static double borderToBorderDistance(Particle a, Particle b, double l, boolean periodic) {
        double dx = b.x() - a.x();
        double dy = b.y() - a.y();
        if (periodic) {
            dx -= l * Math.round(dx / l);
            dy -= l * Math.round(dy / l);
        }
        return Math.sqrt(dx * dx + dy * dy) - a.radius() - b.radius();
    }
}