package ar.edu.itba.sds.tp5.engine;

import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;

/**
 * Aceleraciones del SFM sin fuerza social (Teórica 6, diapos 28–33) sobre arreglos planos {x1, y1, x2, y2, ...}:
 * m r̈_i = F_G,i + F_D,i. Un agente retirado no recibe ni ejerce fuerza. La capa de elusión solo decide la dirección
 * de la velocidad deseada dentro de F_D; no entra ninguna fuerza nueva.
 */
public final class SfmField implements Integrator.Field {
    private final Agent[] agents;
    private final SfmParameters p;
    private final boolean[] active;
    private final AvoidanceLayer[] layers;
    private final double[] direction = new double[2];

    /** {@code active} es del simulador, que lo actualiza al retirar agentes. */
    public SfmField(Agent[] agents, SfmParameters p, boolean[] active) {
        this(agents, p, active, AvoidanceLayer.NONE);
    }

    public SfmField(Agent[] agents, SfmParameters p, boolean[] active, AvoidanceLayer layer) {
        this.agents = agents;
        this.p = p;
        this.active = active;
        this.layers = new AvoidanceLayer[agents.length];
        for (int i = 0; i < agents.length; i++) layers[i] = layer.forAgent(i);
    }

    @Override public void acceleration(double[] r, double[] v, double[] a) {
        double m = p.mass();
        for (int i = 0; i < agents.length; i++) {
            int ix = 2 * i, iy = ix + 1;
            if (!active[i]) { a[ix] = 0; a[iy] = 0; continue; }
            // F_D,i = m (v_d e_target − v_i) / τ
            desiredDirection(i, r, v);
            a[ix] = (agents[i].desiredSpeed() * direction[0] - v[ix]) / p.tau();
            a[iy] = (agents[i].desiredSpeed() * direction[1] - v[iy]) / p.tau();
        }
        double contactRange = 2 * p.radius();
        for (int i = 0; i < agents.length; i++) {
            if (!active[i]) continue;
            int ix = 2 * i, iy = ix + 1;
            for (int j = i + 1; j < agents.length; j++) {
                if (!active[j]) continue;
                int jx = 2 * j, jy = jx + 1;
                double rx = r[ix] - r[jx], ry = r[iy] - r[jy], dist = Math.hypot(rx, ry);
                double eps = dist - contactRange;     // g(ε) = 1 si ε < 0: es negativo en el solapamiento
                if (eps >= 0 || dist == 0) continue;
                double nx = rx / dist, ny = ry / dist;  // e^n_ij apunta de j a i
                double tx = -ny, ty = nx;               // e^t_ij; F_G no depende de su sentido (aparece dos veces)
                double vt = (v[ix] - v[jx]) * tx + (v[iy] - v[jy]) * ty;
                double normal = -eps * p.kn(), tangential = vt * eps * p.kt();
                double fx = normal * nx + tangential * tx, fy = normal * ny + tangential * ty;
                a[ix] += fx / m; a[iy] += fy / m;
                a[jx] -= fx / m; a[jy] -= fy / m;
            }
        }
    }

    /** Si la capa está reemplazando el target final del agente i en este estado. */
    boolean layerActive(int i, double[] r, double[] v) {
        return desiredDirection(i, r, v);
    }

    /** Deja e_target en {@code direction}. Con dos agentes, j es siempre el otro; si ya se retiró, no hay capa. */
    private boolean desiredDirection(int i, double[] r, double[] v) {
        int ix = 2 * i, iy = ix + 1;
        Agent agent = agents[i];
        double dx = agent.targetX() - r[ix], dy = agent.targetY() - r[iy], d = Math.hypot(dx, dy);
        double ex = d > 0 ? dx / d : 0, ey = d > 0 ? dy / d : 0;
        direction[0] = ex;
        direction[1] = ey;
        int j = other(i);
        if (j < 0 || d == 0) return false;
        return layers[i].directionWithVelocity(r[ix], r[iy], v[ix], v[iy], r[2 * j], r[2 * j + 1], v[2 * j], v[2 * j + 1], agent.desiredSpeed(), ex, ey, direction);
    }

    private int other(int i) {
        for (int j = 0; j < agents.length; j++) if (j != i && active[j]) return j;
        return -1;
    }
}
