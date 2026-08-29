package ar.edu.itba.sds.tp2.engine;

import java.util.List;
import java.util.Random;

/** Utilidades de matemática de ángulos (dominio [0, 2π), distinto del dominio de posición [0, L) de PeriodicBoundary). */
public final class AngleMath {

    private static final double TWO_PI = 2 * Math.PI;

    private AngleMath() {
    }

    /** Envuelve un ángulo al rango [0, 2π). */
    static double normalize(double theta) {
        return (theta % TWO_PI + TWO_PI) % TWO_PI;
    }

    /**
     * Promedio vectorial de una lista de ángulos: suma (cos θ, sin θ) de
     * cada elemento, promedia, aplica atan2 y normaliza el resultado a
     * [0, 2π).
     *
     * <p>Este método NO decide si el ángulo propio de una partícula debe
     * incluirse en el promedio de sus vecinos — esa decisión (para el
     * modelo estándar de Vicsek, la cátedra confirmó que sí se incluye)
     * es responsabilidad de quien arma la lista {@code thetas} antes de
     * llamar a este método.
     */
    static double vectorialAverage(List<Double> thetas) {
        if (thetas.isEmpty()) {
            throw new IllegalArgumentException("vectorialAverage requiere al menos un ángulo, la lista vino vacía");
        }
        double sumCos = 0;
        double sumSin = 0;
        for (double theta : thetas) {
            sumCos += Math.cos(theta);
            sumSin += Math.sin(theta);
        }
        double n = thetas.size();
        return normalize(Math.atan2(sumSin / n, sumCos / n));
    }

    /** Suma ruido uniforme en (-eta/2, eta/2) a theta y normaliza el resultado. */
    static double addNoise(double theta, double eta, Random random) {
        double noise = (random.nextDouble() - 0.5) * eta;
        return normalize(theta + noise);
    }
}