package ar.edu.itba.sds.tp5.engine;

import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * SFM sin fuerza social, con capa de elusión opcional. El tiempo es t = paso·Δt con paso entero, con Δt = Δt_exp/dtDiv, así que cada
 * t_k cae exacto en un paso. Guarda una fila cada dtDiv/4 pasos, de modo que los t_k son las filas múltiplos de 4.
 * Un agente se retira al llegar a δ_a de su target (D13); desde esa fila sus columnas valen NaN.
 */
public final class Simulation {
    public static final int DEFAULT_DT_DIV = 64;
    public static final int ROWS_PER_INTERVAL = 4;

    private final SfmParameters params;
    private final Integrator integrator;
    private final int dtDiv;
    private final AvoidanceLayer layer;

    public Simulation(SfmParameters params, Integrator integrator, int dtDiv) {
        this(params, integrator, dtDiv, AvoidanceLayer.NONE);
    }

    public Simulation(SfmParameters params, Integrator integrator, int dtDiv, AvoidanceLayer layer) {
        if (dtDiv <= 0 || dtDiv % ROWS_PER_INTERVAL != 0)
            throw new IllegalArgumentException("dtDiv debe ser un múltiplo positivo de " + ROWS_PER_INTERVAL + ": " + dtDiv);
        this.params = params;
        this.integrator = integrator;
        this.dtDiv = dtDiv;
        this.layer = layer;
    }

    public int outputEvery() { return dtDiv / ROWS_PER_INTERVAL; }

    /**
     * Simula hasta {@code intervals} intervalos experimentales, o hasta que se retiren todos.
     *
     * @return trayectoria, con una fila por dt2 desde t = 0
     */
    public Result run(Agent[] agents, double dtExp, int intervals) {
        return run(agents, dtExp, intervals, null);
    }

    /** Estado de cada paso, para diagnóstico. Los arreglos son del simulador y se reutilizan: leerlos dentro de la llamada. */
    @FunctionalInterface
    public interface StepObserver {
        void onStep(long step, double t, double[] r, double[] v, boolean[] active, boolean[] layerOn);
    }

    /** Igual que {@link #run(Agent[], double, int)}, avisando cada paso a {@code observer} si no es null. No cambia la corrida. */
    public Result run(Agent[] agents, double dtExp, int intervals, StepObserver observer) {
        int n = agents.length, every = outputEvery();
        long totalSteps = (long) intervals * dtDiv;
        double dt = dtExp / dtDiv;
        boolean[] active = new boolean[n];
        Arrays.fill(active, true);
        double[] r0 = new double[2 * n], v0 = new double[2 * n];
        for (int i = 0; i < n; i++) {
            r0[2 * i] = agents[i].x0(); r0[2 * i + 1] = agents[i].y0();
            v0[2 * i] = agents[i].vx0(); v0[2 * i + 1] = agents[i].vy0();
        }
        SfmField field = new SfmField(agents, params, active, layer);
        Integrator.Stepper stepper = integrator.start(field, dt, r0, v0);
        boolean[] layerOn = new boolean[n];
        int[] layerSwitches = new int[n];
        double[] arrival = new double[n], pathLength = new double[n], last = r0.clone();
        Arrays.fill(arrival, Double.NaN);
        double minDistance = Double.POSITIVE_INFINITY, minDistanceTime = Double.NaN;
        boolean anyContact = false;
        List<double[]> rows = new ArrayList<>();
        int remaining = n;

        for (long step = 0; ; step++) {
            double[] r = stepper.position();
            double t = step * dt;
            for (int i = 0; i < n; i++) {
                if (!active[i]) continue;
                pathLength[i] += Math.hypot(r[2 * i] - last[2 * i], r[2 * i + 1] - last[2 * i + 1]);
                last[2 * i] = r[2 * i]; last[2 * i + 1] = r[2 * i + 1];
            }
            if (remaining == n) {
                for (int i = 0; i < n; i++) for (int j = i + 1; j < n; j++) {
                    double d = Math.hypot(r[2 * i] - r[2 * j], r[2 * i + 1] - r[2 * j + 1]);
                    if (d < minDistance) { minDistance = d; minDistanceTime = t; }
                    if (d < 2 * params.radius()) anyContact = true;
                }
            }
            for (int i = 0; i < n; i++) {
                if (active[i] && Math.hypot(agents[i].targetX() - r[2 * i], agents[i].targetY() - r[2 * i + 1]) <= params.deltaA()) {
                    active[i] = false;
                    arrival[i] = t;
                    remaining--;
                }
            }
            if (layer != AvoidanceLayer.NONE) {
                for (int i = 0; i < n; i++) {
                    if (!active[i]) continue;
                    boolean on = field.layerActive(i, r, stepper.velocity());
                    if (on != layerOn[i]) layerSwitches[i]++;
                    layerOn[i] = on;
                }
            }
            if (observer != null) observer.onStep(step, t, r, stepper.velocity(), active, layerOn);
            if (step % every == 0) rows.add(row(t, r, stepper.velocity(), active));
            if (step == totalSteps || remaining == 0) break;
            stepper.advance();
        }
        return new Result(rows, dtExp / ROWS_PER_INTERVAL, arrival, pathLength, minDistance, minDistanceTime, anyContact, layerSwitches);
    }

    private static double[] row(double t, double[] r, double[] v, boolean[] active) {
        double[] row = new double[1 + 2 * r.length];
        row[0] = t;
        for (int i = 0; i < active.length; i++) {
            int base = 1 + 4 * i;
            row[base] = active[i] ? r[2 * i] : Double.NaN;
            row[base + 1] = active[i] ? r[2 * i + 1] : Double.NaN;
            row[base + 2] = active[i] ? v[2 * i] : Double.NaN;
            row[base + 3] = active[i] ? v[2 * i + 1] : Double.NaN;
        }
        return row;
    }

    /**
     * @param rows            filas {t, x1, y1, vx1, vy1, x2, y2, vx2, vy2}, separadas por dt2
     * @param arrival         instante de retiro de cada agente; NaN si no llegó
     * @param pathLength      longitud recorrida por cada agente hasta su retiro
     * @param minDistance     mínima distancia entre centros mientras estuvieron todos
     * @param minDistanceTime instante de esa distancia mínima
     * @param anyContact      si hubo solapamiento
     * @param layerSwitches   veces que la capa de cada agente se prendió o se apagó
     */
    public record Result(List<double[]> rows, double dt2, double[] arrival, double[] pathLength,
                         double minDistance, double minDistanceTime, boolean anyContact, int[] layerSwitches) {
        /** Posición del agente en la fila; NaN si ya se retiró o si la corrida terminó antes. */
        public double x(int agent, int row) { return row < rows.size() ? rows.get(row)[1 + 4 * agent] : Double.NaN; }
        public double y(int agent, int row) { return row < rows.size() ? rows.get(row)[2 + 4 * agent] : Double.NaN; }
    }
}
