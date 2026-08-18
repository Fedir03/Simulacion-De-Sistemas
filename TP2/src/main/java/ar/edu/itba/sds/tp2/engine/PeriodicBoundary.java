package ar.edu.itba.sds.tp2.engine;

/** Utilidades para contorno periódico (espacio toroidal de lado L). */
public final class PeriodicBoundary {

    private PeriodicBoundary() {
    }

    /** Envuelve una coordenada al rango [0, l) bajo contorno periódico. */
    static double wrap(double coord, double l) {
        return (coord % l + l) % l;
    }
}