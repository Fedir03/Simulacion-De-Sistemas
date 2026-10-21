package ar.edu.itba.sds.tp4.io;

import ar.edu.itba.sds.tp4.engine.billiard.BilliardSimulator;
import ar.edu.itba.sds.tp4.engine.billiard.BilliardSimulator.Frame;
import ar.edu.itba.sds.tp4.engine.billiard.BilliardSimulator.Summary;
import ar.edu.itba.sds.tp4.models.BilliardConfig;
import java.io.BufferedWriter;
import java.io.Closeable;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

/**
 * Salidas del Sistema 2 (D4), una fila o cuadro cada dt2. Las líneas que empiezan con # son metadatos; la última es
 * "# fin estado=... runtime_s=...". Las energías van con precisión completa (Double.toString) para graficar ΔE/E(0).
 * <ul>
 *   <li>observables.txt: t E_tot E_cin E_el Nu</li>
 *   <li>dynamic.txt (opcional): por cuadro "t=... Nu=..." y N líneas "id x y vx vy used" (used: 0 fresca, 1 usada)</li>
 * </ul>
 */
public final class BilliardFiles implements BilliardSimulator.Observer, Closeable {
    public static final String OBSERVABLES = "observables.txt", DYNAMIC = "dynamic.txt";

    private final BufferedWriter observables, dynamic;

    /** dynamic = false: solo observables.txt. neighbors describe la búsqueda de vecinos, para la cabecera. */
    public BilliardFiles(Path dir, BilliardConfig c, String neighbors, boolean dynamic) throws IOException {
        Files.createDirectories(dir);
        this.observables = Files.newBufferedWriter(dir.resolve(OBSERVABLES), StandardCharsets.UTF_8);
        header(observables, c, neighbors);
        observables.write("t E_tot E_cin E_el Nu"); observables.newLine();
        if (dynamic) {
            this.dynamic = Files.newBufferedWriter(dir.resolve(DYNAMIC), StandardCharsets.UTF_8);
            header(this.dynamic, c, neighbors);
            if (c.hasObstacles())
                for (double ox : new double[]{-c.x0(), c.x0()}) {
                    this.dynamic.write("# obstacle " + ox + " 0.0 " + c.radius()); this.dynamic.newLine();
                }
            this.dynamic.write("# t=... Nu=... y luego N líneas: id x y vx vy used"); this.dynamic.newLine();
        } else this.dynamic = null;
    }

    @Override public void onFrame(Frame f) throws IOException {
        String t = time(f.time());
        observables.write(t + " " + f.totalEnergy() + " " + f.kineticEnergy() + " " + f.elasticEnergy() + " " + f.usedCount());
        observables.newLine();
        if (dynamic == null) return;
        dynamic.write("t=" + t + " Nu=" + f.usedCount()); dynamic.newLine();
        StringBuilder line = new StringBuilder(96);
        for (int i = 0; i < f.x().length; i++) {
            line.setLength(0);
            line.append(i + 1).append(' ').append(f.x()[i]).append(' ').append(f.y()[i]).append(' ')
                    .append(f.vx()[i]).append(' ').append(f.vy()[i]).append(' ').append(f.used()[i] ? 1 : 0);
            dynamic.write(line.toString()); dynamic.newLine();
        }
    }

    /** Pie con el resultado y el tiempo de ejecución medido (no forma parte de los datos). */
    public void footer(Summary s, double runtimeSeconds) throws IOException {
        String status = switch (s.status()) {
            case COMPLETED -> "completa";
            case DIVERGED -> "divergio"; // t = primer instante con una partícula fuera de |r| ≤ R
            case ALL_USED -> "t100";
        };
        String line = "# fin estado=" + status + " t=" + time(s.time()) + " pasos=" + s.steps() + " Nu=" + s.usedCount()
                + " runtime_s=" + runtimeSeconds;
        observables.write(line); observables.newLine();
        if (dynamic != null) { dynamic.write(line); dynamic.newLine(); }
    }

    @Override public void close() throws IOException {
        try { observables.close(); }
        finally { if (dynamic != null) dynamic.close(); }
    }

    private static void header(BufferedWriter w, BilliardConfig c, String neighbors) throws IOException {
        w.write("# format=tp4-billiard-v1 N=" + c.n() + " seed=" + c.seed() + " x0=" + (c.hasObstacles() ? c.x0() : "none")
                + " dt=" + c.dt() + " dt2=" + c.dt2() + " tf=" + c.finalTime() + " R=" + c.domainRadius() + " r=" + c.radius()
                + " m=" + c.mass() + " k=" + c.k() + " v0=" + c.speed() + " neighbors=" + neighbors);
        w.newLine();
    }

    /** t = paso·dt; 9 decimales sobran (dt ≥ 1e-6) y evitan el 0.04000000000000001 del producto. */
    private static String time(double t) { return String.format(Locale.ROOT, "%.9f", t); }
}
