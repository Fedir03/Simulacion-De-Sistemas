package ar.edu.itba.sds.tp2.analysis;

/** Resultado del analisis de clusters de un cuadro. */
public record ClusterStats(int largestSize, int clusterCount, int n) {

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
}
