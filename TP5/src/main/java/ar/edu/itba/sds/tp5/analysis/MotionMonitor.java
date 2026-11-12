package ar.edu.itba.sds.tp5.analysis;

import ar.edu.itba.sds.tp5.engine.Simulation;

/**
 * Longitud recorrida por cada agente y conmutaciones de su capa, medidas en cada paso Δt con el
 * {@link Simulation.StepObserver}. Son observables de análisis: el motor no las calcula.
 * <p>
 * Reproduce lo que hacía el motor antes de separarlo:
 * <ul>
 *   <li>longitud: suma en cada paso el desplazamiento de los agentes que seguían activos al empezar el paso (antes de los
 *   retiros de ese paso). El observador recibe {@code active} ya actualizado, así que se usa el del paso anterior;</li>
 *   <li>conmutaciones: cuenta los cambios de {@code layerOn} de los agentes activos después de los retiros del paso, que es
 *   cuando el motor evalúa la capa.</li>
 * </ul>
 */
public final class MotionMonitor implements Simulation.StepObserver {
    private double[] pathLength, last;
    private boolean[] activeBefore, layerBefore;
    private int[] layerSwitches;

    @Override
    public void onStep(long step, double t, double[] r, double[] v, boolean[] active, boolean[] layerOn) {
        int n = active.length;
        if (last == null) {     // primer paso: posición inicial, todos activos y capa apagada
            pathLength = new double[n];
            layerSwitches = new int[n];
            last = r.clone();
            activeBefore = new boolean[n];
            java.util.Arrays.fill(activeBefore, true);
            layerBefore = new boolean[n];
        }
        for (int i = 0; i < n; i++) {
            if (activeBefore[i]) {
                pathLength[i] += Math.hypot(r[2 * i] - last[2 * i], r[2 * i + 1] - last[2 * i + 1]);
                last[2 * i] = r[2 * i]; last[2 * i + 1] = r[2 * i + 1];
            }
            if (active[i]) {
                if (layerOn[i] != layerBefore[i]) layerSwitches[i]++;
                layerBefore[i] = layerOn[i];
            }
            activeBefore[i] = active[i];
        }
    }

    /** Longitud recorrida por cada agente hasta su retiro. */
    public double[] pathLength() { return pathLength.clone(); }

    /** Veces que la capa de cada agente se prendió o se apagó. */
    public int[] layerSwitches() { return layerSwitches.clone(); }

    /** Varios observadores sobre la misma corrida, en orden. */
    public static Simulation.StepObserver all(Simulation.StepObserver... observers) {
        return (step, t, r, v, active, layerOn) -> {
            for (Simulation.StepObserver o : observers) o.onStep(step, t, r, v, active, layerOn);
        };
    }
}
