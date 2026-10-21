package ar.edu.itba.sds.tp3.bench;

import java.io.IOException;

/**
 * Un caso que RuntimeBenchmark sabe medir: arma la condición inicial fuera del cronómetro y mide solo el ciclo
 * de la simulación. Para medir otro motor con el mismo protocolo (p. ej. Sistema 2 del TP4) alcanza con otra
 * implementación de esta interfaz.
 */
public interface TimedCase {
    record RunResult(double runtimeSeconds, long events, int goals, double t90) { }

    /** Descripción estable del caso (motor, geometría, colocación) en JSON; se compara al reanudar. */
    String describeJson();

    /** Arma la condición inicial de (n, seed). No se mide. */
    void prepare(int n, long seed);

    /** Simula la condición preparada hasta tf y devuelve el tiempo de pared del ciclo (System.nanoTime). */
    RunResult runTimed(double tf) throws IOException;
}
