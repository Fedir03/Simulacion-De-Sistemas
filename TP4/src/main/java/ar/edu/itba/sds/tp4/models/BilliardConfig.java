package ar.edu.itba.sds.tp4.models;

/**
 * Billar circular del Sistema 2. x0 = {@link #NO_OBSTACLES} es el sistema sin obstáculos; si no, los obstáculos
 * están en (±x0, 0) con el mismo radio que las partículas.
 */
public record BilliardConfig(int n, long seed, double x0, double dt, double dt2, double finalTime,
                             double domainRadius, double radius, double mass, double k, double speed) {
    public static final double NO_OBSTACLES = Double.NaN;
    /** Tolerancia relativa para aceptar dt2 = n·dt y tf = pasos·dt pese al redondeo (0.04 / 1e-3 = 40.00000000000001). */
    private static final double MULTIPLE_TOLERANCE = 1e-9;

    /** Valores del enunciado: R = 0.51 m, r = 0.0175 m, m = 0.025 kg, k = 1e4 N/m, v0 = 1 m/s. */
    public static BilliardConfig of(int n, long seed, double x0, double dt, double dt2, double finalTime) {
        return new BilliardConfig(n, seed, x0, dt, dt2, finalTime, 0.51, 0.0175, 0.025, 1e4, 1);
    }

    public BilliardConfig {
        if (n <= 0) throw new IllegalArgumentException("N debe ser positivo");
        for (double v : new double[]{dt, dt2, finalTime, domainRadius, radius, mass, k})
            if (!Double.isFinite(v) || v <= 0) throw new IllegalArgumentException("dt, dt2, tf, R, r, m y k deben ser positivos");
        if (!Double.isFinite(speed) || speed < 0) throw new IllegalArgumentException("v0 debe ser no negativa");
        if (2 * radius >= domainRadius) throw new IllegalArgumentException("El radio de las partículas no entra en el dominio");
        if (!Double.isNaN(x0) && !(x0 >= radius * (1 - MULTIPLE_TOLERANCE) && x0 <= (domainRadius - radius) * (1 + MULTIPLE_TOLERANCE)))
            throw new IllegalArgumentException("x0 debe estar entre r = " + radius + " y R − r = " + (domainRadius - radius) + ": " + x0);
        multiple(dt2, dt, "dt2");
        multiple(finalTime, dt2, "tf");
    }

    public boolean hasObstacles() { return !Double.isNaN(x0); }

    /** n = dt2/dt: se guarda el estado cada n pasos. */
    public int outputEvery() { return Math.toIntExact(multiple(dt2, dt, "dt2")); }

    public long totalSteps() { return multiple(finalTime, dt, "tf"); }

    /** Cociente value/step si es entero salvo redondeo; si no, error (no se redondea en silencio). */
    private static long multiple(double value, double step, String name) {
        double ratio = value / step;
        long n = Math.round(ratio);
        if (n < 1 || n == Long.MAX_VALUE || Math.abs(ratio - n) > MULTIPLE_TOLERANCE * n)
            throw new IllegalArgumentException(name + " = " + value + " debe ser un múltiplo entero de " + step);
        return n;
    }
}
