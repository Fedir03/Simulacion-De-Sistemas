package ar.edu.itba.sds.tp5.engine;

import java.util.Locale;

/**
 * Integradores candidatos de D11 (Teórica 4), para fuerzas que dependen de la velocidad. Trabajan sobre
 * arreglos planos de componentes. Las fórmulas son las de TP4/engine/oscillator/Scheme con sus opciones por
 * defecto, llevadas a varias componentes.
 */
public enum Integrator {
    /** Verlet original (diapo 13): f(t) con v(t) ≈ [r(t) − r(t−Δt)]/Δt. La velocidad que informa es la central. */
    VERLET {
        @Override public Stepper start(Field field, double dt, double[] r0, double[] v0) {
            return new VerletStepper(field, dt, r0, v0);
        }
    },
    /** Beeman predictor-corrector para fuerzas que dependen de v (diapo 20). */
    BEEMAN {
        @Override public Stepper start(Field field, double dt, double[] r0, double[] v0) {
            return new BeemanStepper(field, dt, r0, v0);
        }
    };

    /** Elegido con la prueba del peatón libre (DEFINICIONES.md, D11). */
    public static final Integrator DEFAULT = BEEMAN;

    public abstract Stepper start(Field field, double dt, double[] r0, double[] v0);

    public static Integrator parse(String text) {
        try { return valueOf(text.strip().toUpperCase(Locale.ROOT)); }
        catch (IllegalArgumentException e) { throw new IllegalArgumentException("Integrador desconocido: " + text); }
    }

    /** a(r, v) sobre arreglos planos; escribe en {@code a}. */
    @FunctionalInterface
    public interface Field { void acceleration(double[] r, double[] v, double[] a); }

    /** Estado en el paso actual. Los arreglos devueltos son del integrador y se reutilizan. */
    public interface Stepper {
        void advance();
        double[] position();
        double[] velocity();
    }

    private static final class VerletStepper implements Stepper {
        private final Field field;
        private final double dt;
        private final int n;
        private double[] prev, r, next;
        private final double[] v, vBack, a;

        VerletStepper(Field field, double dt, double[] r0, double[] v0) {
            this.field = field;
            this.dt = dt;
            n = r0.length;
            r = r0.clone();
            prev = new double[n];
            next = new double[n];
            v = new double[n];
            vBack = v0.clone();
            a = new double[n];
            field.acceleration(r, vBack, a);
            // r(−Δt) por Euler evaluado en −Δt (diapo 14)
            for (int k = 0; k < n; k++) prev[k] = r[k] - dt * vBack[k] + dt * dt * a[k] / 2;
            look();
        }

        /** Calcula r(t+Δt) y con eso la velocidad central v(t). */
        private void look() {
            for (int k = 0; k < n; k++) {
                next[k] = 2 * r[k] - prev[k] + dt * dt * a[k];
                v[k] = (next[k] - prev[k]) / (2 * dt);
            }
        }

        @Override public void advance() {
            double[] t = prev; prev = r; r = next; next = t;
            for (int k = 0; k < n; k++) vBack[k] = (r[k] - prev[k]) / dt;
            field.acceleration(r, vBack, a);
            look();
        }

        @Override public double[] position() { return r; }
        @Override public double[] velocity() { return v; }
    }

    private static final class BeemanStepper implements Stepper {
        private final Field field;
        private final double dt;
        private final int n;
        private final double[] r, v, vPred;
        private double[] a, aPrev, aNext;

        BeemanStepper(Field field, double dt, double[] r0, double[] v0) {
            this.field = field;
            this.dt = dt;
            n = r0.length;
            r = r0.clone();
            v = v0.clone();
            vPred = new double[n];
            a = new double[n];
            aPrev = new double[n];
            aNext = new double[n];
            field.acceleration(r, v, a);
            // a(−Δt): estado anterior estimado con Euler evaluado en −Δt
            double[] rBack = new double[n], vBack = new double[n];
            for (int k = 0; k < n; k++) {
                rBack[k] = r[k] - dt * v[k] + dt * dt * a[k] / 2;
                vBack[k] = v[k] - dt * a[k];
            }
            field.acceleration(rBack, vBack, aPrev);
        }

        @Override public void advance() {
            for (int k = 0; k < n; k++) {
                r[k] += v[k] * dt + (2.0 / 3) * a[k] * dt * dt - (1.0 / 6) * aPrev[k] * dt * dt;
                vPred[k] = v[k] + 1.5 * a[k] * dt - 0.5 * aPrev[k] * dt;
            }
            field.acceleration(r, vPred, aNext);
            for (int k = 0; k < n; k++)
                v[k] += (1.0 / 3) * aNext[k] * dt + (5.0 / 6) * a[k] * dt - (1.0 / 6) * aPrev[k] * dt;
            double[] t = aPrev; aPrev = a; a = aNext; aNext = t;
        }

        @Override public double[] position() { return r; }
        @Override public double[] velocity() { return v; }
    }
}
