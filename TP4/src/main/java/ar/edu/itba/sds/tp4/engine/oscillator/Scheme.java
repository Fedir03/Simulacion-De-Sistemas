package ar.edu.itba.sds.tp4.engine.oscillator;

import ar.edu.itba.sds.tp4.models.Oscillator;

/**
 * Esquemas de integración del Sistema 1 (fórmulas de Teórica 4). Cada uno devuelve las posiciones
 * x(n·Δt) para n = 0..steps. Las variantes dependientes de la velocidad salen de {@link IntegrationOptions}.
 */
public enum Scheme {
    /** Beeman predictor-corrector para fuerzas que dependen de v (diapo 20). */
    BEEMAN("beeman") {
        @Override double[] positions(Oscillator o, double dt, int steps, IntegrationOptions opt) {
            double m = o.mass(), x = o.x0(), v = o.v0(), a = o.force(x, v) / m;
            double[] out = start(x, steps);
            // a(−Δt): estado anterior estimado con Euler evaluado en −Δt.
            double aPrev = o.force(x - dt * v + dt * dt * a / 2, v - dt * a) / m;
            for (int n = 1; n <= steps; n++) {
                double xNext = x + v * dt + (2.0 / 3) * a * dt * dt - (1.0 / 6) * aPrev * dt * dt;
                double vPred = v + 1.5 * a * dt - 0.5 * aPrev * dt;
                double aNext = o.force(xNext, vPred) / m;
                double vNext = v + (1.0 / 3) * aNext * dt + (5.0 / 6) * a * dt - (1.0 / 6) * aPrev * dt;
                if (opt.accelerationUpdate() == IntegrationOptions.AccelerationUpdate.CORRECTED) aNext = o.force(xNext, vNext) / m;
                aPrev = a; a = aNext; x = xNext; v = vNext;
                out[n] = x;
            }
            return out;
        }
    },
    /** Verlet original (diapo 13), con f(t) evaluada con una v(t) estimada. */
    VERLET("verlet") {
        @Override double[] positions(Oscillator o, double dt, int steps, IntegrationOptions opt) {
            double m = o.mass(), x = o.x0();
            double[] out = start(x, steps);
            // r(−Δt) por Euler evaluado en −Δt; v(0) es dato, así que no se estima en el primer paso.
            double v = o.v0(), a = o.force(x, v) / m;
            double xPrev = x - dt * v + dt * dt * a / 2, xPrevPrev = Double.NaN;
            for (int n = 0; n < steps; n++) {
                if (n > 0) v = switch (opt.verletVelocity()) {
                    case BACKWARD -> (x - xPrev) / dt;
                    // v(t−Δt) central necesita r(t−2Δt); en n = 1 se usa v(0), que es exacta.
                    case EULER -> (n == 1 ? o.v0() : (x - xPrevPrev) / (2 * dt)) + a * dt;
                };
                a = o.force(x, v) / m;
                double xNext = 2 * x - xPrev + dt * dt * a;
                xPrevPrev = xPrev; xPrev = x; x = xNext;
                out[n + 1] = x;
            }
            return out;
        }
    },
    /** Velocity Verlet (diapo 17) con Δt²/(2m) en la posición (D19); f(t+Δt) con velocidad predicha. */
    VELOCITY_VERLET("velocity_verlet") {
        @Override double[] positions(Oscillator o, double dt, int steps, IntegrationOptions opt) {
            double m = o.mass(), x = o.x0(), v = o.v0(), a = o.force(x, v) / m;
            double[] out = start(x, steps);
            for (int n = 1; n <= steps; n++) {
                double xNext = x + dt * v + dt * dt * a / 2;
                double vPred = switch (opt.velocityVerletPrediction()) {
                    case EULER -> v + a * dt;
                    case HALF_STEP -> v + a * dt / 2;
                };
                double aNext = o.force(xNext, vPred) / m;
                double vNext = v + dt * (a + aNext) / 2;
                if (opt.accelerationUpdate() == IntegrationOptions.AccelerationUpdate.CORRECTED) aNext = o.force(xNext, vNext) / m;
                x = xNext; v = vNext; a = aNext;
                out[n] = x;
            }
            return out;
        }
    },
    /** Euler predictor-corrector de una pasada (diapos 22–23); no es el Euler modificado de la diapo 10. */
    EULER_PC("euler_pc") {
        @Override double[] positions(Oscillator o, double dt, int steps, IntegrationOptions opt) {
            double m = o.mass(), x = o.x0(), v = o.v0();
            double[] out = start(x, steps);
            for (int n = 1; n <= steps; n++) {
                double a = o.force(x, v) / m;
                double vPred = v + a * dt, xPred = x + v * dt;
                double aNext = o.force(xPred, vPred) / m;
                v = v + aNext * dt;
                x = x + v * dt;
                out[n] = x;
            }
            return out;
        }
    };

    private final String id;
    Scheme(String id) { this.id = id; }
    public String id() { return id; }

    abstract double[] positions(Oscillator o, double dt, int steps, IntegrationOptions opt);

    /** Posiciones x(n·Δt), n = 0..steps. */
    public double[] integrate(Oscillator o, double dt, int steps, IntegrationOptions opt) {
        if (!Double.isFinite(dt) || dt <= 0) throw new IllegalArgumentException("dt debe ser positivo");
        if (steps < 1) throw new IllegalArgumentException("Se necesita al menos un paso");
        return positions(o, dt, steps, opt);
    }

    public static Scheme fromId(String id) {
        for (Scheme s : values()) if (s.id.equals(id)) return s;
        throw new IllegalArgumentException("Esquema desconocido: " + id);
    }

    private static double[] start(double x0, int steps) {
        double[] out = new double[steps + 1];
        out[0] = x0;
        return out;
    }
}
