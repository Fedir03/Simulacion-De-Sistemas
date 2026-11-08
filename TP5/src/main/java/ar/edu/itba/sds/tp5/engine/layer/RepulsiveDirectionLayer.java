package ar.edu.itba.sds.tp5.engine.layer;

/**
 * Capa F: modificación del CPM (Teórica 7, diapo 28) sobre el SFM.
 * n_c = e_ij A_p exp(−d_ij/B_p) cos θ_j, con cos θ_j > 0 (semiplano de visión); e_a = (n_c + e_t)/|n_c + e_t|.
 * Sin horizonte: el choque predicho solo pide t* > 0 y d_min < ρ.
 */
public final class RepulsiveDirectionLayer implements AvoidanceLayer {
    private final double intensity, range;
    private final LayerConstants constants;

    public RepulsiveDirectionLayer(double intensity, double range, LayerConstants constants) {
        if (!(intensity >= 0 && intensity < 1)) throw new IllegalArgumentException("A_p debe estar en [0, 1): " + intensity);
        if (!(range > 0)) throw new IllegalArgumentException("B_p debe ser positivo: " + range);
        this.intensity = intensity;
        this.range = range;
        this.constants = constants;
    }

    @Override public boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                       double vd, double ex, double ey, double[] out) {
        out[0] = ex;
        out[1] = ey;
        CollisionPrediction p = CollisionPrediction.of(xi, yi, xj, yj, vxj, vyj, vd, ex, ey);
        if (constants.fGated() && (p == null || !p.isCollision(constants.fHorizon(), constants.rho()))) return false;
        double d = Math.hypot(xi - xj, yi - yj);
        if (d == 0) return false;
        double awayX = (xi - xj) / d, awayY = (yi - yj) / d;    // e_ij
        double cos = -(ex * awayX + ey * awayY);                // cos θ_j = e_t·(x_j − x_i)/d_ij
        if (cos <= 0) return false;
        // Con A_p = 0 se devuelve e_t tal cual, sin el redondeo de renormalizar
        if (intensity == 0) return true;
        if (isTie(p, ex, ey, awayX, awayY)) {
            // Choque casi frontal: n_c ∥ e_t no desvía. e_ij apunta hacia atrás, así que para que i se desvíe a SU
            // derecha hay que rotar e_ij en sentido antihorario (visto desde arriba)
            double c = Math.cos(constants.frontalAngle()), s = Math.sin(constants.frontalAngle());
            double rx = c * awayX - s * awayY, ry = s * awayX + c * awayY;
            // Con el otro a más de ese ángulo del eje, rotar no alcanza: se usa −e_t rotado, como en el choque frontal exacto
            if (constants.frontalTie() == LayerConstants.FrontalTie.METRIC && rx * ey - ry * ex < 0) {
                rx = -c * ex + s * ey;
                ry = -s * ex - c * ey;
            }
            awayX = rx;
            awayY = ry;
        }
        double magnitude = intensity * Math.exp(-Math.max(0, d - constants.fGap()) / range) * cos;
        double ax = magnitude * awayX + ex, ay = magnitude * awayY + ey;
        double norm = Math.hypot(ax, ay);
        out[0] = ax / norm;
        out[1] = ay / norm;
        return true;
    }

    private boolean isTie(CollisionPrediction p, double ex, double ey, double awayX, double awayY) {
        return switch (constants.frontalTie()) {
            // Sin compuerta puede no haber acercamiento futuro, y ahí s_c no significa nada
            case METRIC -> p != null && p.tStar() > 0 && Math.abs(ey * p.closestX() - ex * p.closestY()) <= constants.sideEpsilon();  // |s_c| ≤ ε
            case ANGULAR -> Math.abs(ex * awayY - ey * awayX) <= constants.frontalAngle();              // |sin θ_j| ≤ ε
        };
    }

    @Override public String label() {
        return "capa=F A_p=" + intensity + " B_p=" + range + " rho=" + constants.rho() + " desempate=" + constants.frontalTie()
                + " frontal_deg=" + Math.toDegrees(constants.frontalAngle())
                + (Double.isInfinite(constants.fHorizon()) ? "" : " t_a_F=" + constants.fHorizon())
                + (constants.fGated() ? "" : " sin_compuerta")
                + (constants.fGap() == 0 ? "" : " resta_d=" + constants.fGap());
    }
}
