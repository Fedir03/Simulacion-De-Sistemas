package ar.edu.itba.sds.tp2.analysis;

import java.util.List;
import java.util.Set;

/** Resultado del analisis de clusters de un cuadro. */
public record ClusterStats(int largestSize, int clusterCount, int n, Set<Integer> largestMembers) {

    /** Sin la lista de miembros: util cuando solo interesa el numero. */
    public ClusterStats(int largestSize, int clusterCount, int n) {
        this(largestSize, clusterCount, n, Set.of());
    }

    public ClusterStats {
        if (n <= 0) {
            throw new IllegalArgumentException("n debe ser positivo");
        }
        if (largestSize <= 0 || largestSize > n) {
            throw new IllegalArgumentException("el cluster mas grande no puede tener " + largestSize
                    + " particulas sobre un total de " + n);
        }
    }

    /** Fraccion de particulas en la componente gigante: el observable S del enunciado. */
    public double s() {
        return (double) largestSize / n;
    }

    /** Ids del cluster mas grande, ordenados. Vacio si no se pidieron. */
    public List<Integer> sortedMembers() {
        return largestMembers.stream().sorted().toList();
    }
}
