package ar.edu.itba.sds.tp4.bench;

import ar.edu.itba.sds.tp4.engine.billiard.BilliardSimulator;
import ar.edu.itba.sds.tp4.engine.cim.CellIndexMethod;
import ar.edu.itba.sds.tp4.io.BilliardFiles;
import ar.edu.itba.sds.tp4.models.BilliardConfig;
import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;

/**
 * Sistema 2 con obstáculos en ±x0 (D7: x0 = r) y la grilla única (D5). Mide el mismo tramo que Main billiard:
 * BilliardSimulator.run con observables.txt escrito cada dt2 (D4, lo usa 2.4); sin dynamic.txt.
 */
public final class Tp4Case implements TimedCase {
    private final double dt, dt2, x0;
    private BilliardSimulator sim;
    private BilliardFiles files;

    public Tp4Case(double dt, double dt2, double x0) { this.dt = dt; this.dt2 = dt2; this.x0 = x0; }

    @Override public String describeJson() {
        BilliardConfig c = BilliardConfig.of(1, 1, x0, dt, dt2, dt2); // valida dt, dt2 y x0 antes de medir
        return "{\"engine\": \"TP4 BilliardSimulator (Verlet)\", \"neighbors\": \"cim M=" + cells(c)
                + "\", \"placement\": \"grid hex, sitio en el origen, s = 2r + " + BilliardSimulator.GRID_GAP + "\", \"x0\": " + x0
                + ", \"dt\": " + dt + ", \"dt2\": " + dt2 + ", \"R\": " + c.domainRadius() + ", \"r\": " + c.radius() + ", \"m\": " + c.mass()
                + ", \"k\": " + c.k() + ", \"v0\": " + c.speed()
                + ", \"output\": \"observables.txt cada dt2 dentro del tramo medido (como Main billiard); sin dynamic.txt\"}";
    }

    @Override public void prepare(int n, long seed, double tf, Path dir) throws IOException {
        if (files != null) files.close();
        BilliardConfig c = BilliardConfig.of(n, seed, x0, dt, dt2, tf);
        int m = cells(c);
        sim = BilliardSimulator.fromGrid(c, CellIndexMethod.forCircle(m, c.domainRadius()));
        files = new BilliardFiles(dir, c, "cim M=" + m, false);
    }

    @Override public RunResult runTimed() throws IOException {
        if (sim == null) throw new IllegalStateException("Llamar a prepare antes de runTimed");
        BilliardSimulator s = sim;
        sim = null;
        try (BilliardFiles out = files) {
            files = null;
            // Mismo tramo que Main billiard (D11): la simulación con su escritura; sin colocación ni apertura del archivo
            long start = System.nanoTime();
            BilliardSimulator.Summary summary = s.run(out, false);
            double runtime = (System.nanoTime() - start) / 1e9;
            out.footer(summary, runtime);
            return new RunResult(runtime, summary.steps(), summary.status(), summary.usedCount());
        }
    }

    private static int cells(BilliardConfig c) { return CellIndexMethod.maxValidM(2 * c.domainRadius(), 0, c.radius()); }

    /** Se lanza con scripts/sim_gen/runtime_tp4.sh: --out DIR --ns 100,200 --rounds 10 --warmup 300:1,600:0.5 [--dt 1e-5] [--dt2 0.04] [--x0 0.0175] ... */
    public static void main(String[] args) {
        try {
            Map<String, String> options = RuntimeBenchmark.parse(args);
            double dt = Double.parseDouble(take(options, "dt", "1e-5"));
            double dt2 = Double.parseDouble(take(options, "dt2", "0.04"));
            double x0 = Double.parseDouble(take(options, "x0", "0.0175"));
            RuntimeBenchmark.run(new Tp4Case(dt, dt2, x0), options, args);
        } catch (IllegalArgumentException | IllegalStateException | IOException e) {
            System.err.println("Error: " + e.getMessage()); System.exit(1);
        }
    }

    private static String take(Map<String, String> options, String key, String fallback) {
        String v = options.remove(key);
        return v == null ? fallback : v;
    }
}
