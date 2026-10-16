package ar.edu.itba.sds.tp4.engine.oscillator;

import ar.edu.itba.sds.tp4.models.Oscillator;

/** ECM(Δt) contra la solución analítica (enunciado 1.2). */
public final class OscillatorStudy {
    private OscillatorStudy() { }

    public record Result(Scheme scheme, double dt, int steps, double ecm, double runtimeSeconds) { }

    /** Pasos hasta tf: round(tf/Δt); si Δt no divide a tf, la corrida termina a menos de Δt/2 de tf. */
    public static int steps(Oscillator o, double dt) {
        long n = Math.round(o.finalTime() / dt);
        if (n < 1 || n > Integer.MAX_VALUE - 1) throw new IllegalArgumentException("dt fuera de rango: " + dt);
        return (int) n;
    }

    /**
     * ECM = Σ_{n=1..steps} (x_num(nΔt) − x_an(nΔt))² / steps. t = 0 no se cuenta: ahí ambas coinciden por construcción.
     */
    public static double ecm(Oscillator o, double dt, double[] positions) {
        int steps = positions.length - 1;
        double sum = 0;
        for (int n = 1; n <= steps; n++) {
            double d = positions[n] - o.analytic(n * dt);
            sum += d * d;
        }
        return sum / steps;
    }

    /** El tiempo medido cubre solo la integración, no el cálculo del ECM. */
    public static Result run(Oscillator o, Scheme scheme, double dt, IntegrationOptions opt) {
        int steps = steps(o, dt);
        long start = System.nanoTime();
        double[] x = scheme.integrate(o, dt, steps, opt);
        double runtime = (System.nanoTime() - start) / 1e9;
        return new Result(scheme, dt, steps, ecm(o, dt, x), runtime);
    }

    /** count valores de Δt espaciados logarítmicamente en [dtMin, dtMax], de mayor a menor. */
    public static double[] logSpaced(double dtMin, double dtMax, int count) {
        if (!(dtMin > 0) || !(dtMax >= dtMin) || count < 1 || count == 1 && dtMin != dtMax)
            throw new IllegalArgumentException("Barrido de dt inválido");
        double[] dts = new double[count];
        for (int i = 0; i < count; i++)
            dts[i] = count == 1 ? dtMax : Math.exp(Math.log(dtMax) + i * (Math.log(dtMin) - Math.log(dtMax)) / (count - 1));
        return dts;
    }
}
