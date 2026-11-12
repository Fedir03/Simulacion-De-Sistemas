package ar.edu.itba.sds.tp5.analysis;

import ar.edu.itba.sds.tp5.engine.Simulation;

/**
 * Distancia mínima entre centros y contactos de una corrida, medidos en cada paso Δt con el {@link Simulation.StepObserver}
 * (no con las filas de salida, que van cada Δt_exp/4). Es un observable de análisis: el motor no lo calcula.
 * <p>
 * Reproduce el control que hacía el motor antes de separarlo: en cada paso se miden todos los pares mientras estuvieron
 * todos los agentes al empezar el paso (antes de los retiros de ese paso). El observador recibe {@code active} ya
 * actualizado con los retiros del paso, así que se usa el estado del paso anterior.
 */
public final class ContactMonitor implements Simulation.StepObserver {
    private final double contactDistance;
    private boolean allActiveBefore = true;
    private double minDistance = Double.POSITIVE_INFINITY, minDistanceTime = Double.NaN;
    private boolean anyContact;

    /** @param radius radio de los peatones: hay contacto si la distancia entre centros es menor que 2R */
    public ContactMonitor(double radius) {
        this.contactDistance = 2 * radius;
    }

    @Override
    public void onStep(long step, double t, double[] r, double[] v, boolean[] active, boolean[] layerOn) {
        int n = active.length;
        if (allActiveBefore) {
            for (int i = 0; i < n; i++) for (int j = i + 1; j < n; j++) {
                double d = Math.hypot(r[2 * i] - r[2 * j], r[2 * i + 1] - r[2 * j + 1]);
                if (d < minDistance) { minDistance = d; minDistanceTime = t; }
                if (d < contactDistance) anyContact = true;
            }
        }
        boolean all = true;
        for (boolean a : active) all &= a;
        allActiveBefore = all;
    }

    /** Resultado de la corrida observada. */
    public Stats stats() {
        return new Stats(minDistance, minDistanceTime, anyContact);
    }

    /**
     * @param minDistance     mínima distancia entre centros mientras estuvieron todos
     * @param minDistanceTime instante de esa distancia mínima
     * @param anyContact      si hubo solapamiento en algún paso
     */
    public record Stats(double minDistance, double minDistanceTime, boolean anyContact) { }
}
