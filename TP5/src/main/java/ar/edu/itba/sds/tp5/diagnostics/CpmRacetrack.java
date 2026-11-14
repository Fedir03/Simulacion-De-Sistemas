package ar.edu.itba.sds.tp5.diagnostics;

import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.cpm.CpmParameters;
import ar.edu.itba.sds.tp5.engine.cpm.CpmSimulation;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import java.util.Locale;
import java.util.Random;

/**
 * Validación del CPM contra el paper (Baglietto y Parisi 2011, Sec. III A): diagrama fundamental en la pista circular
 * de radios 2 y 4 m, corrido con el mismo {@link CpmSimulation} que usa el TP. No va al ZIP.
 * <p>
 * Como en el paper: posiciones uniformes al azar en la pista (sin solaparse si se puede), r = r_min y velocidad nula al
 * inicio, e_target tangente a la pista (sentido antihorario) en todo momento, 100 s de simulación con una fila cada
 * 0,1 s, se descartan los primeros 30 s, y la velocidad es la proyección de v sobre e_target promediada sobre todas las
 * partículas y los instantes; ρ = N_p/(12π). La dirección tangente se le pasa al motor como una "capa" que ignora al
 * otro agente; los targets finales quedan lejos para que nadie se retire.
 * <p>
 * Uso: java -cp target/tp5.jar ar.edu.itba.sds.tp5.diagnostics.CpmRacetrack [realizaciones] [N1,N2,...]
 * Escribe, para cada juego de parámetros, una línea por N: juego r_min r_max β v_dmax N ρ ⟨v⟩ σ_realizaciones.
 */
public final class CpmRacetrack {
    static final double R_IN = 2, R_OUT = 4, AREA = Math.PI * (R_OUT * R_OUT - R_IN * R_IN);
    static final double DT_OUT = 0.1, T_TOTAL = 100, T_DISCARD = 30, FAR = 1e9;

    private CpmRacetrack() { }

    /** e_target tangente a la pista en la posición del agente (antihorario). */
    static final AvoidanceLayer TANGENT = new AvoidanceLayer() {
        @Override public boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                           double vd, double ex, double ey, double[] out) {
            double d = Math.hypot(xi, yi);
            out[0] = -yi / d;
            out[1] = xi / d;
            return false;
        }
        @Override public String label() { return "pista"; }
    };

    static final CpmSimulation.Wall INNER = (x, y, out) -> radial(R_IN, x, y, out);
    static final CpmSimulation.Wall OUTER = (x, y, out) -> radial(R_OUT, x, y, out);

    private static void radial(double radius, double x, double y, double[] out) {
        double d = Math.hypot(x, y);
        out[0] = radius * x / d;
        out[1] = radius * y / d;
    }

    /** Velocidad media (proyección sobre e_target) de una realización con N partículas. */
    public static double run(CpmParameters p, double vdMax, int n, long seed) {
        Agent[] agents = place(p.rMin(), vdMax, n, new Random(seed));
        int intervals = (int) Math.round(T_TOTAL / (Simulation.ROWS_PER_INTERVAL * DT_OUT));
        Simulation.Result r = new CpmSimulation(p, TANGENT, INNER, OUTER).run(agents, Simulation.ROWS_PER_INTERVAL * DT_OUT, intervals);
        double sum = 0;
        long count = 0;
        for (double[] row : r.rows()) {
            if (row[0] < T_DISCARD - 1e-9) continue;
            for (int i = 0; i < n; i++) {
                double x = row[1 + 4 * i], y = row[2 + 4 * i], d = Math.hypot(x, y);
                sum += (-y * row[3 + 4 * i] + x * row[4 + 4 * i]) / d;
                count++;
            }
        }
        return sum / count;
    }

    /** Distancia mínima entre centros y a las paredes en toda la corrida, en unidades de r_min (para ver que no se atraviesan). */
    public static double minGap(CpmParameters p, double vdMax, int n, long seed) {
        Agent[] agents = place(p.rMin(), vdMax, n, new Random(seed));
        double[] min = { Double.POSITIVE_INFINITY };
        new CpmSimulation(p, TANGENT, INNER, OUTER).run(agents, Simulation.ROWS_PER_INTERVAL * DT_OUT, 50, (step, t, x, v, active, on) -> {
            if (t < 1) return;     // la condición inicial puede venir solapada a densidad alta
            for (int i = 0; i < n; i++) {
                double d = Math.hypot(x[2 * i], x[2 * i + 1]);
                min[0] = Math.min(min[0], Math.min(d - R_IN, R_OUT - d) / p.rMin());
                for (int j = i + 1; j < n; j++)
                    min[0] = Math.min(min[0], Math.hypot(x[2 * i] - x[2 * j], x[2 * i + 1] - x[2 * j + 1]) / p.rMin());
            }
        });
        return min[0];
    }

    static Agent[] place(double rMin, double vdMax, int n, Random rnd) {
        double[] px = new double[n], py = new double[n];
        for (int i = 0; i < n; i++) {
            for (int tries = 0; ; tries++) {
                // uniforme en área: ρ² uniforme entre los radios (dejando r_min a cada pared)
                double a = R_IN + rMin, b = R_OUT - rMin;
                double rho = Math.sqrt(a * a + rnd.nextDouble() * (b * b - a * a)), th = 2 * Math.PI * rnd.nextDouble();
                px[i] = rho * Math.cos(th);
                py[i] = rho * Math.sin(th);
                boolean ok = true;
                for (int j = 0; j < i && ok; j++) ok = Math.hypot(px[i] - px[j], py[i] - py[j]) >= 2 * rMin;
                if (ok || tries > 10_000) break;
            }
        }
        Agent[] agents = new Agent[n];
        for (int i = 0; i < n; i++) agents[i] = new Agent(px[i], py[i], 0, 0, FAR, FAR, vdMax);
        return agents;
    }

    public static void main(String[] args) {
        int reps = args.length > 0 ? Integer.parseInt(args[0]) : 5;
        int[] ns = { 5, 20, 40, 75, 115, 150, 190, 225, 265, 300, 340 };
        if (args.length > 1) ns = java.util.Arrays.stream(args[1].split(",")).mapToInt(Integer::parseInt).toArray();
        // nombre, r_min, r_max, β, v_dmax (Sec. III A y IV del paper)
        Object[][] sets = {
                { "set1", 0.15, 0.32, 0.9, 1.55 },
                { "set2", 0.10, 0.37, 0.9, 0.95 },
                { "rmin0.05", 0.05, 0.37, 0.9, 0.95 },
                { "rmin0.15", 0.15, 0.37, 0.9, 0.95 },
                { "rmax0.30", 0.10, 0.30, 0.9, 0.95 },
                { "rmax0.44", 0.10, 0.44, 0.9, 0.95 },
                { "beta0.5", 0.10, 0.37, 0.5, 0.95 },
                { "beta1.3", 0.10, 0.37, 1.3, 0.95 },
        };
        System.out.println("# juego r_min r_max beta v_dmax N rho v_media sigma_realizaciones  (realizaciones=" + reps + ")");
        for (Object[] s : sets) {
            CpmParameters p = new CpmParameters((double) s[1], (double) s[2], (double) s[3], 0.5, 0.1);
            double vd = (double) s[4];
            for (int n : ns) {
                double sum = 0, sum2 = 0;
                for (int k = 0; k < reps; k++) {
                    double v = run(p, vd, n, 1000L * n + k);
                    sum += v;
                    sum2 += v * v;
                }
                double mean = sum / reps, sd = Math.sqrt(Math.max(0, sum2 / reps - mean * mean));
                System.out.printf(Locale.ROOT, "%s %.2f %.2f %.1f %.2f %d %.3f %.4f %.4f%n", s[0], p.rMin(), p.rMax(), p.beta(), vd, n, n / AREA, mean, sd);
            }
        }
        System.out.printf(Locale.ROOT, "# separación mínima (en r_min) set2 N=150: %.3f%n", minGap(
                new CpmParameters(0.10, 0.37, 0.9, 0.5, 0.1), 0.95, 150, 7));
    }
}
