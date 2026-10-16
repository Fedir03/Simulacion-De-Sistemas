package ar.edu.itba.sds.tp4.io;

import ar.edu.itba.sds.tp4.engine.oscillator.IntegrationOptions;
import ar.edu.itba.sds.tp4.engine.oscillator.OscillatorStudy;
import ar.edu.itba.sds.tp4.engine.oscillator.Scheme;
import ar.edu.itba.sds.tp4.models.Oscillator;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Locale;

/** Salidas de texto del Sistema 1. Las líneas que empiezan con # son metadatos. */
public final class OscillatorFiles {
    private OscillatorFiles() { }

    /** Una fila por (esquema, Δt): scheme dt steps ecm runtime_s. */
    public static void writeEcm(Path out, Oscillator o, IntegrationOptions opt, List<OscillatorStudy.Result> results) throws IOException {
        try (BufferedWriter w = writer(out)) {
            header(w, o, opt);
            w.write("scheme dt steps ecm runtime_s"); w.newLine();
            for (var r : results) {
                w.write(String.format(Locale.ROOT, "%s %.9e %d %.9e %.6e", r.scheme().id(), r.dt(), r.steps(), r.ecm(), r.runtimeSeconds()));
                w.newLine();
            }
        }
    }

    /** Una fila por paso: t analytic y una columna por esquema, en el orden de Scheme.values(). */
    public static void writeTrajectory(Path out, Oscillator o, IntegrationOptions opt, double dt, int steps, double[][] positions) throws IOException {
        try (BufferedWriter w = writer(out)) {
            header(w, o, opt);
            StringBuilder cols = new StringBuilder("t analytic");
            for (Scheme s : Scheme.values()) cols.append(' ').append(s.id());
            w.write(cols.toString()); w.newLine();
            for (int n = 0; n <= steps; n++) {
                StringBuilder line = new StringBuilder(String.format(Locale.ROOT, "%.9e %.12e", n * dt, o.analytic(n * dt)));
                for (double[] x : positions) line.append(String.format(Locale.ROOT, " %.12e", x[n]));
                w.write(line.toString()); w.newLine();
            }
        }
    }

    private static void header(BufferedWriter w, Oscillator o, IntegrationOptions opt) throws IOException {
        w.write(String.format(Locale.ROOT, "# m=%s k=%s gamma=%s A=%s tf=%s", o.mass(), o.k(), o.gamma(), o.amplitude(), o.finalTime()));
        w.newLine();
        w.write("# " + opt.describe()); w.newLine();
    }

    private static BufferedWriter writer(Path out) throws IOException {
        if (out.getParent() != null) Files.createDirectories(out.getParent());
        return Files.newBufferedWriter(out, StandardCharsets.UTF_8);
    }
}
