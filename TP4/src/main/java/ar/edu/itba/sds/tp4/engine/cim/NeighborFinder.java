package ar.edu.itba.sds.tp4.engine.cim;

// Copiado de TP1 (ar.edu.itba.sds.tp1). Agregado en TP4: forEachContact y PairVisitor.

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;

public interface NeighborFinder {
    Map<Integer, Set<Integer>> findNeighbors(List<Particle> particles, double l, double rc, boolean periodic);

    /** Recibe cada par en contacto una sola vez, con i < j (índices de los arreglos). */
    @FunctionalInterface
    interface PairVisitor {
        void visit(int i, int j);
    }

    /**
     * Pares en contacto (rc = 0, sin contorno periódico) de partículas de igual radio en (x[i], y[i]).
     * Ruta genérica sobre findNeighbors, con ids = índices; CellIndexMethod la reemplaza por una sin asignaciones.
     */
    default void forEachContact(double[] x, double[] y, double radius, double l, PairVisitor visitor) {
        List<Particle> particles = new ArrayList<>(x.length);
        for (int i = 0; i < x.length; i++) {
            particles.add(new Particle(i, x[i], y[i], radius));
        }
        Map<Integer, Set<Integer>> neighbors = findNeighbors(particles, l, 0, false);
        for (int i = 0; i < x.length; i++) {
            for (int j : neighbors.get(i)) {
                if (i < j) {
                    visitor.visit(i, j);
                }
            }
        }
    }

    static void validatePeriodic(double l, double rc, double maxRadius) {
        if (l <= 2 * (rc + 2 * maxRadius)) {
            throw new IllegalArgumentException(String.format(
                "Condiciones periódicas inválidas: se requiere L > 2·(rc + 2·r_max). " +
                "L=%s, rc=%s, r_max=%s. " +
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
