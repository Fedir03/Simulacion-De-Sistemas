package ar.edu.itba.sds.tp4.models;

/**
 * Oscilador puntual amortiguado, f = −k·x − γ·v (Teórica 4, diapo 37).
 * Condición inicial x(0) = A, v(0) = −A·γ/(2m), que es la de la solución analítica.
 */
public record Oscillator(double mass, double k, double gamma, double amplitude, double finalTime) {
    public static Oscillator defaults() {
        return new Oscillator(70, 1e4, 100, 1, 5);
    }
    public Oscillator {
        for (double v : new double[]{mass, k, amplitude, finalTime})
            if (!Double.isFinite(v) || v <= 0) throw new IllegalArgumentException("Masa, k, amplitud y tiempo final deben ser positivos");
        if (!Double.isFinite(gamma) || gamma < 0) throw new IllegalArgumentException("γ debe ser no negativo");
        if (k / mass <= gamma * gamma / (4 * mass * mass)) throw new IllegalArgumentException("La solución analítica requiere régimen subamortiguado");
    }
    public double force(double x, double v) { return -k * x - gamma * v; }
    public double x0() { return amplitude; }
    public double v0() { return -amplitude * gamma / (2 * mass); }
    public double analytic(double t) {
        double omega = Math.sqrt(k / mass - gamma * gamma / (4 * mass * mass));
        return amplitude * Math.exp(-gamma * t / (2 * mass)) * Math.cos(omega * t);
    }
}
