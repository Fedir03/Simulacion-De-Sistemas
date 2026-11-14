package ar.edu.itba.sds.tp5.engine.cpm;

import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.Simulator;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * CPM (Baglietto y Parisi, Phys. Rev. E 83, 056117, 2011) con capa de elusión opcional. Paso fijo
 * Δt = r_min / (2 max(v_d,max, v_e)) (Ec. 2), con v_e = v_d,max (Ec. 9) y v_d,max la mayor rapidez deseada del evento.
 * Cada paso sigue el pseudocódigo del paper:
 * <ol>
 *   <li>(D13) se retiran los agentes a δ_a o menos de su target;</li>
 *   <li>contactos (iteración 1): i toca a j si |x_i − x_j| &lt; r_i + r_j, y a una pared si la distancia al punto más
 *       cercano de la pared es &lt; r_i; e_esc es el versor de la suma de los e_ij = (x_i − x_j)/|x_i − x_j| sobre
 *       los j en contacto (Ec. 6 y 7);</li>
 *   <li>radios (iteración 2): en contacto r_i = r_min; libre r_i = min(r_max, r_i + r_max Δt/τ) (Ec. 8);</li>
 *   <li>velocidad deseada (iteración 3): v_d = v_d(r_i) e_target, con v_d(r) = v_d,max [(r − r_min)/(r_max − r_min)]^β
 *       (Ec. 1 y 5);</li>
 *   <li>(iteración 4) v_i = v_d si está libre (r_i &gt; r_min), v_i = v_e e_esc si está en contacto (Ec. 4), y
 *       x_i(t + Δt) = x_i(t) + v_i Δt (Ec. 3).</li>
 * </ol>
 * El paper deja el target afuera del modelo ("could be done by higher level algorithms that consider ... efficient
 * avoidance"): la capa de elusión, la misma que en el SFM, solo decide e_target del agente libre (Teórica 7, diapo 29:
 * "si la partícula NO está en contacto") y ve las velocidades del paso anterior. En contacto manda el escape.
 * <p>
 * Condición inicial (enunciado: posición y velocidad experimentales): en el CPM la velocidad no es una variable de
 * estado sino que sale del radio (Ec. 1), así que v_0 entra como el radio que le corresponde, r_0 = v_d⁻¹(|v_0|) acotado
 * a [r_min, r_max], y como la velocidad del paso anterior que ve la capa en el primer paso. Desde el primer paso, las
 * reglas son las del paper.
 * <p>
 * Salida: Δt no divide a Δt_exp, así que las filas (cada Δt_exp/4, como en el SFM) se evalúan sobre la trayectoria del
 * CPM, que es lineal dentro de cada paso: x(t) = x(t_s) + v_s (t − t_s). Es exacta, no una interpolación aproximada.
 * Cada fila es {t, x1, y1, vx1, vy1, x2, y2, vx2, vy2, r1, r2}, con la velocidad y el radio del paso; NaN desde el retiro.
 */
public final class CpmSimulation implements Simulator {

    /** Pared (u obstáculo) del CPM: escribe en {@code out} su punto más cercano a (x, y). */
    @FunctionalInterface
    public interface Wall {
        void nearest(double x, double y, double[] out);
    }

    private final CpmParameters params;
    private final AvoidanceLayer layer;
    private final Wall[] walls;

    public CpmSimulation(CpmParameters params, AvoidanceLayer layer, Wall... walls) {
        this.params = params;
        this.layer = layer;
        this.walls = walls.clone();
    }

    public CpmParameters params() { return params; }

    /** Δt del CPM para estos agentes: r_min/(2 v_d,max), con v_d,max la mayor rapidez deseada (v_e = v_d,max). */
    public double dt(Agent[] agents) {
        double vMax = 0;
        for (Agent a : agents) vMax = Math.max(vMax, a.desiredSpeed());
        return params.dt(vMax);
    }

    @Override public int outputEvery() { return 1; }

    @Override
    public Simulation.Result run(Agent[] agents, double dtExp, int intervals, Simulation.StepObserver observer) {
        int n = agents.length;
        double dt = dt(agents), dt2 = dtExp / Simulation.ROWS_PER_INTERVAL, growth = params.rMax() * dt / params.tau();
        int totalRows = intervals * Simulation.ROWS_PER_INTERVAL + 1;
        AvoidanceLayer[] layers = new AvoidanceLayer[n];
        for (int i = 0; i < n; i++) layers[i] = layer.forAgent(i);

        double[] x = new double[2 * n], v = new double[2 * n], vPrev = new double[2 * n], esc = new double[2 * n];
        double[] radius = new double[n], arrival = new double[n], out = new double[2], wall = new double[2];
        boolean[] active = new boolean[n], contact = new boolean[n], layerOn = new boolean[n];
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
            // Iteración 1: contactos (con los radios del paso anterior) y suma de los e_ij de los que tocan
            Arrays.fill(contact, false);
            Arrays.fill(esc, 0);
            for (int i = 0; i < n; i++) {
                if (!active[i]) continue;
                int ix = 2 * i, iy = ix + 1;
                for (int j = i + 1; j < n; j++) {
                    if (!active[j]) continue;
                    double dx = x[ix] - x[2 * j], dy = x[iy] - x[2 * j + 1], s = radius[i] + radius[j], d2 = dx * dx + dy * dy;
                    if (d2 >= s * s) continue;
                    contact[i] = contact[j] = true;
                    double d = Math.sqrt(d2);
                    if (d > 0) { esc[ix] += dx / d; esc[iy] += dy / d; esc[2 * j] -= dx / d; esc[2 * j + 1] -= dy / d; }
                }
                for (Wall w : walls) {
                    w.nearest(x[ix], x[iy], wall);
                    double dx = x[ix] - wall[0], dy = x[iy] - wall[1], d = Math.hypot(dx, dy);
                    if (d >= radius[i]) continue;
                    contact[i] = true;
                    if (d > 0) { esc[ix] += dx / d; esc[iy] += dy / d; }
                }
            }
            System.arraycopy(v, 0, vPrev, 0, v.length);
            for (int i = 0; i < n; i++) {
                layerOn[i] = false;
                if (!active[i]) continue;
                int ix = 2 * i, iy = ix + 1;
                Agent a = agents[i];
                if (contact[i]) {
                    // Iteraciones 2 y 4 en contacto: r = r_min y v = v_e e_esc, con v_e = v_d,max
                    contactSteps[i]++;
                    radius[i] = params.rMin();
                    double norm = Math.hypot(esc[ix], esc[iy]);
                    v[ix] = norm > 0 ? a.desiredSpeed() * esc[ix] / norm : 0;
                    v[iy] = norm > 0 ? a.desiredSpeed() * esc[iy] / norm : 0;
                    continue;
                }
                // Iteración 2 libre: el radio crece r_max Δt/τ hasta r_max
                radius[i] = Math.min(params.rMax(), radius[i] + growth);
                // Iteración 3: dirección (target final o temporal de la capa) y módulo v_d(r)
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
            // Iteración 4: x(t + Δt) = x(t) + v Δt
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
