package ar.edu.itba.sds.tp5.engine.layer;

/**
 * Capas A y B: target temporal x_T = x_i + v_d t_a e_t + ℓ n. Solo difieren en cómo calculan ℓ.
 * La regla de lado esquiva hacia el lado opuesto al otro, con desempate a la derecha.
 */
public abstract class LateralTargetLayer implements AvoidanceLayer {
    private final double horizon;
    private final LayerConstants constants;

    LateralTargetLayer(double horizon, LayerConstants constants) {
        if (!(horizon > 0)) throw new IllegalArgumentException("t_a debe ser positivo: " + horizon);
        this.horizon = horizon;
        this.constants = constants;
    }

    /** Capa A: ℓ fijo. */
    public static LateralTargetLayer a(double horizon, double lateral, LayerConstants constants) {
        if (!(lateral >= 0)) throw new IllegalArgumentException("ℓ no puede ser negativo: " + lateral);
        return new LateralTargetLayer(horizon, constants) {
            @Override double lateral(CollisionPrediction p) { return lateral; }
            @Override public String label() { return "capa=A t_a=" + horizon + " l=" + lateral + " rho=" + constants.rho(); }
        };
    }

    /** Capa B: ℓ = k (ρ − d_min). */
    public static LateralTargetLayer b(double horizon, double gain, LayerConstants constants) {
        if (!(gain >= 0)) throw new IllegalArgumentException("k no puede ser negativo: " + gain);
        return new LateralTargetLayer(horizon, constants) {
            @Override double lateral(CollisionPrediction p) { return gain * (constants.rho() - p.dMin()); }
            @Override public String label() { return "capa=B t_a=" + horizon + " k=" + gain + " rho=" + constants.rho(); }
        };
    }

    abstract double lateral(CollisionPrediction p);

    @Override public boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                       double vd, double ex, double ey, double[] out) {
        out[0] = ex;
        out[1] = ey;
        CollisionPrediction p = CollisionPrediction.of(xi, yi, xj, yj, vxj, vyj, vd, ex, ey);
        if (p == null || !p.isCollision(horizon, constants.rho())) return false;
        double lateral = lateral(p);
        // Con ℓ = 0 x_T queda sobre la recta a x_f: se devuelve e_t tal cual, sin el redondeo de renormalizar
        if (lateral == 0) return true;
        double rightX = ey, rightY = -ex;           // e_t^⊥, la normal a la derecha de e_t
        double side = rightX * p.closestX() + rightY * p.closestY();
        double sign = Math.abs(side) > constants.sideEpsilon() ? -Math.signum(side) : 1;
        double tx = vd * horizon * ex + lateral * sign * rightX;
        double ty = vd * horizon * ey + lateral * sign * rightY;
        double norm = Math.hypot(tx, ty);
        out[0] = tx / norm;
        out[1] = ty / norm;
        return true;
    }
}
