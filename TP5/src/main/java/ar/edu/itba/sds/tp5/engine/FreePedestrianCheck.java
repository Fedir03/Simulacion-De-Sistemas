package ar.edu.itba.sds.tp5.engine;

/**
 * Prueba analítica de D11: peatón libre con v_0 colineal al target, de modo que e_target es constante y
 * v(t) = v_d + (v_0 − v_d) e^{−t/τ}, x(t) = x_0 + v_d t + (v_0 − v_d) τ (1 − e^{−t/τ}).
 */
public final class FreePedestrianCheck {
    private static final double DT_EXP = 1 / 15.0192;
    private static final double V0 = 0.4, VD = 1.3, DURATION = 5;

    private FreePedestrianCheck() { }

    /** Errores RMS contra la solución analítica sobre todos los pasos. */
    public record Errors(Integrator integrator, int dtDiv, double position, double velocity) { }

    public static Errors measure(Integrator integrator, int dtDiv) {
        SfmParameters p = SfmParameters.defaults();
        double dt = DT_EXP / dtDiv;
        int steps = (int) Math.round(DURATION / dt);
        // Target muy lejos: no se llega y la dirección no cambia
        Agent[] agent = { new Agent(0, 0, V0, 0, 1e6, 0, VD) };
        Integrator.Stepper s = integrator.start(new SfmField(agent, p, new boolean[] { true }), dt, new double[] { 0, 0 }, new double[] { V0, 0 });
        double sumR = 0, sumV = 0;
        for (int n = 1; n <= steps; n++) {
            s.advance();
            double t = n * dt, decay = Math.exp(-t / p.tau());
            double x = VD * t + (V0 - VD) * p.tau() * (1 - decay), v = VD + (V0 - VD) * decay;
            double er = s.position()[0] - x, ev = s.velocity()[0] - v;
            sumR += er * er;
            sumV += ev * ev;
        }
        return new Errors(integrator, dtDiv, Math.sqrt(sumR / steps), Math.sqrt(sumV / steps));
    }
}
