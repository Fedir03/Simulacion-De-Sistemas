package ar.edu.itba.sds.tp4.bench;

import ar.edu.itba.sds.tp4.engine.billiard.BilliardSimulator.Status;
import java.io.IOException;
import java.nio.file.Path;

/**
 * Un caso que RuntimeBenchmark sabe medir (mismo contrato que el TimedCase de TP3): arma la condición inicial y abre
 * la salida fuera del cronómetro, y mide solo el ciclo de la simulación.
 */
public interface TimedCase {
    record RunResult(double runtimeSeconds, long steps, Status status, int usedCount) { }

    /** Descripción estable del caso (motor, geometría, colocación, dt) en JSON; se compara al reanudar. */
    String describeJson();

    /** Arma la condición inicial de (n, seed) hasta tf y abre su salida en dir. No se mide. */
    void prepare(int n, long seed, double tf, Path dir) throws IOException;

    /** Simula la condición preparada y devuelve el tiempo de pared del ciclo (System.nanoTime). */
    RunResult runTimed() throws IOException;
}
