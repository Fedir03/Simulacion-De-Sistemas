package ar.edu.itba.sds.tp5.engine.layer;

/**
 * Detección común: si i siguiera derecho hacia su target final a v_d, con j a su velocidad actual,
 * r = x_j − x_i, w = v_j − v_d e_t, t* = −(r·w)/|w|², d_min = |r + w t*|.
 *
 * @param tStar    t*
 * @param dMin     d_min
 * @param closestX componente x de r + w t* (posición de j respecto de i en el máximo acercamiento)
 * @param closestY componente y
 */
public record CollisionPrediction(double tStar, double dMin, double closestX, double closestY) {
    /** Por debajo de este |w|² los dos se mueven igual y no hay choque predicho. */
    private static final double MIN_W2 = 1e-12;

    /** @return la predicción, o null si |w| ≈ 0 */
    public static CollisionPrediction of(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                         double vd, double ex, double ey) {
        double rx = xj - xi, ry = yj - yi, wx = vxj - vd * ex, wy = vyj - vd * ey;
        double w2 = wx * wx + wy * wy;
        if (w2 < MIN_W2) return null;
        double t = -(rx * wx + ry * wy) / w2;
        double cx = rx + wx * t, cy = ry + wy * t;
        return new CollisionPrediction(t, Math.hypot(cx, cy), cx, cy);
    }

    /** Choque predicho: 0 < t* ≤ horizonte y d_min < ρ. */
    public boolean isCollision(double horizon, double rho) {
        return tStar > 0 && tStar <= horizon && dMin < rho;
    }
}
