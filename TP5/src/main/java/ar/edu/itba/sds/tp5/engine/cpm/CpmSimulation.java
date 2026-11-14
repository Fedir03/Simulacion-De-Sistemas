package ar.edu.itba.sds.tp5.engine.cpm;

import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.Simulator;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * CPM (Baglietto y Parisi, 2011) con capa de elusión opcional. En cada paso Δt = r_min/(2 v_max), con v_max la mayor
 * rapidez del evento:
 * <ol>
 *   <li>se retiran los agentes a δ_a o menos de su target (D13);</li>
 *   <li>contactos: i toca a j si |x_i − x_j| &lt; r_i + r_j;</li>
 *   <li>en contacto: r_i = r_min y v_i = v_e e_esc, con e_esc el versor de la suma de los e_ij (de j hacia i) y v_e = v_d;</li>
 *   <li>libre: r_i = min(r_max, r_i + r_max Δt/τ), v_i = v_d(r_i) e_target, con v_d(r) = v_d [(r − r_min)/(r_max − r_min)]^β;</li>
 *   <li>x_i(t+Δt) = x_i(t) + v_i Δt.</li>
 * </ol>
 * La capa de elusión es la misma que en el SFM y solo decide e_target del agente libre (Teórica 7, diapo 29: "si la
 * partícula NO está en contacto"); ve las velocidades del paso anterior. En contacto manda el escape del CPM.
 * <p>
 * Condición inicial: el agente arranca con la posición y la velocidad experimentales; la velocidad v_0 se usa en el
 * primer paso y el radio inicial es el que corresponde a su rapidez, r_0 = v_d⁻¹(|v_0|) acotado a [r_min, r_max].
 * <p>
 * Salida: Δt no divide a Δt_exp, así que las filas (cada Δt_exp/4, como en el SFM) se evalúan sobre la trayectoria del
 * CPM, que es lineal dentro de cada paso: x(t) = x(t_s) + v_s (t − t_s). Es exacta, no una interpolación aproximada.
 * Cada fila es {t, x1, y1, vx1, vy1, x2, y2, vx2, vy2, r1, r2}; NaN desde el retiro.
 */
public final class CpmSimulation implements Simulator {
    private final CpmParameters params;
    private final AvoidanceLayer layer;

    public CpmSimulation(CpmParameters params, AvoidanceLayer layer) {
        this.params = params;
        this.layer = layer;
    }

    public CpmParameters params() { return params; }

    /** Δt del CPM para estos agentes: r_min/(2 v_max), con v_max la mayor entre las v_d y las rapideces iniciales. */
    public double dt(Agent[] agents) {
        double vMax = 0;
        for (Agent a : agents) vMax = Math.max(vMax, Math.max(a.desiredSpeed(), Math.hypot(a.vx0(), a.vy0())));
        return params.dt(vMax);
    }

    @Override public int outputEvery() { return 1; }

    @Override
    public Simulation.Result run(Agent[] agents, double dtExp, int intervals, Simulation.StepObserver observer) {
        int n = agents.length;
        double dt = dt(agents), dt2 = dtExp / Simulation.ROWS_PER_INTERVAL;
        int totalRows = intervals * Simulation.ROWS_PER_INTERVAL + 1;
        AvoidanceLayer[] layers = new AvoidanceLayer[n];
        for (int i = 0; i < n; i++) layers[i] = layer.forAgent(i);

        double[] x = new double[2 * n], v = new double[2 * n], vPrev = new double[2 * n], radius = new double[n];
        boolean[] active = new boolean[n], contact = new boolean[n], layerOn = new boolean[n];
        double[] arrival = new double[n];
        int[] contactSteps = new int[n];
        Arrays.fill(active, true);
        Arrays.fill(arrival, Double.NaN);
        for (int i = 0; i < n; i++) {
            Agent a = agents[i];
            x[2 * i] = a.x0(); x[2 * i + 1] = a.y0();
            v[2 * i] = a.vx0(); v[2 * i + 1] = a.vy0();
            radius[i] = params.radiusFor(Math.hypot(a.vx0(), a.vy0()), a.desiredSpeed());
        }
        List<double[]> rows = new ArrayList<>(totalRows);
        double[] out = new double[2];
        int remaining = n, nextRow = 0;

        for (long step = 0; nextRow < totalRows; step++) {
            double t = step * dt;
            for (int i = 0; i < n; i++) {
                if (active[i] && Math.hypot(agents[i].targetX() - x[2 * i], agents[i].targetY() - x[2 * i + 1]) <= params.deltaA()) {
                    active[i] = false;
                    arrival[i] = t;
                    remaining--;
                    v[2 * i] = 0; v[2 * i + 1] = 0;
                }
            }
            // Contactos con los radios del paso anterior
            for (int i = 0; i < n; i++) {
                contact[i] = false;
                if (!active[i]) continue;
                for (int j = 0; j < n; j++) {
                    if (j == i || !active[j]) continue;
                    if (Math.hypot(x[2 * i] - x[2 * j], x[2 * i + 1] - x[2 * j + 1]) < radius[i] + radius[j]) contact[i] = true;
                }
            }
            System.arraycopy(v, 0, vPrev, 0, v.length);
            for (int i = 0; i < n; i++) {
                layerOn[i] = false;
                if (!active[i]) continue;
                int ix = 2 * i, iy = ix + 1;
                Agent a = agents[i];
                if (contact[i]) {
                    contactSteps[i]++;
                    radius[i] = params.rMin();
                    double ex = 0, ey = 0;
                    for (int j = 0; j < n; j++) {
                        if (j == i || !active[j]) continue;
                        double dx = x[ix] - x[2 * j], dy = x[iy] - x[2 * j + 1], d = Math.hypot(dx, dy);
                        if (d > 0) { ex += dx / d; ey += dy / d; }
                    }
                    double norm = Math.hypot(ex, ey);
                    v[ix] = norm > 0 ? a.desiredSpeed() * ex / norm : 0;
                    v[iy] = norm > 0 ? a.desiredSpeed() * ey / norm : 0;
                    continue;
                }
                if (step == 0) continue;   // primer paso: velocidad y radio experimentales
                radius[i] = Math.min(params.rMax(), radius[i] + params.rMax() * dt / params.tau());
                double dx = a.targetX() - x[ix], dy = a.targetY() - x[iy], d = Math.hypot(dx, dy);
                double ex = d > 0 ? dx / d : 0, ey = d > 0 ? dy / d : 0;
                out[0] = ex;
                out[1] = ey;
                int j = other(i, active);
                if (j >= 0 && d > 0)
                    layerOn[i] = layers[i].directionWithVelocity(x[ix], x[iy], vPrev[ix], vPrev[iy], x[2 * j], x[2 * j + 1],
                            vPrev[2 * j], vPrev[2 * j + 1], a.desiredSpeed(), ex, ey, out);
                double speed = params.speed(radius[i], a.desiredSpeed());
                v[ix] = speed * out[0];
                v[iy] = speed * out[1];
            }
            if (observer != null) observer.onStep(step, t, x, v, active, layerOn);
            // Filas con t en [t, t + Δt): la trayectoria es lineal dentro del paso
            while (nextRow < totalRows && nextRow * dt2 < t + dt) {
                rows.add(row(nextRow * dt2, t, x, v, radius, active));
                nextRow++;
            }
            if (remaining == 0) break;
            for (int i = 0; i < n; i++) {
                if (!active[i]) continue;
                x[2 * i] += v[2 * i] * dt;
                x[2 * i + 1] += v[2 * i + 1] * dt;
            }
        }
        return new Simulation.Result(rows, dt2, arrival, contactSteps);
    }

    private static int other(int i, boolean[] active) {
        for (int j = 0; j < active.length; j++) if (j != i && active[j]) return j;
        return -1;
    }

    private static double[] row(double tOut, double t, double[] x, double[] v, double[] radius, boolean[] active) {
        int n = active.length;
        double[] row = new double[1 + 5 * n];
        row[0] = tOut;
        double h = tOut - t;
        for (int i = 0; i < n; i++) {
            int base = 1 + 4 * i;
            row[base] = active[i] ? x[2 * i] + v[2 * i] * h : Double.NaN;
            row[base + 1] = active[i] ? x[2 * i + 1] + v[2 * i + 1] * h : Double.NaN;
            row[base + 2] = active[i] ? v[2 * i] : Double.NaN;
            row[base + 3] = active[i] ? v[2 * i + 1] : Double.NaN;
            row[1 + 4 * n + i] = active[i] ? radius[i] : Double.NaN;
        }
        return row;
    }

    public String label() { return params.label(); }
}
