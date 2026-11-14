package ar.edu.itba.sds.tp5.engine;

/**
 * Modelo de dinámica peatonal intercambiable: SFM sin fuerza social ({@link Simulation}) o CPM
 * ({@link ar.edu.itba.sds.tp5.engine.cpm.CpmSimulation}). Los dos devuelven filas cada Δt_exp/4 desde t = 0, así que
 * los t_k son las filas múltiplos de {@link Simulation#ROWS_PER_INTERVAL}, y usan las mismas capas de elusión.
 */
public interface Simulator {

    /** Simula hasta {@code intervals} intervalos experimentales, o hasta que se retiren todos. */
    default Simulation.Result run(Agent[] agents, double dtExp, int intervals) {
        return run(agents, dtExp, intervals, null);
    }

    /** Igual, avisando cada paso del modelo a {@code observer} si no es null. No cambia la corrida. */
    Simulation.Result run(Agent[] agents, double dtExp, int intervals, Simulation.StepObserver observer);

    /** Cada cuántos pasos del modelo cae una fila de salida (1 si el paso no está alineado con la salida). */
    int outputEvery();
}
