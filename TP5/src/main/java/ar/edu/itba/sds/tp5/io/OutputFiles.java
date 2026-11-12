package ar.edu.itba.sds.tp5.io;

import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Simulation;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

/**
 * Salida del motor: la trayectoria de cada evento. Sin marcas de tiempo, para que dos corridas iguales den archivos
 * idénticos. El motor no escribe observables (ECM, distancia mínima, contactos).
 */
public final class OutputFiles {
    private OutputFiles() { }

    /** Parámetros de la corrida, para el encabezado de cada archivo. */
    public record RunInfo(String integrator, int dtDiv, int v0Frames, double deltaA, String layer, String trim) {
        public RunInfo(String integrator, int dtDiv, int v0Frames, double deltaA, String layer) {
            this(integrator, dtDiv, v0Frames, deltaA, layer, "recorte=off");
        }

        /** Sin recorte, el encabezado queda como antes del 11/11, para comparar archivos byte a byte. */
        public String header() {
            return String.format(Locale.ROOT, "integrator=%s dt_div=%d v0_frames=%d delta_a=%s %s", integrator, dtDiv, v0Frames, deltaA, layer)
                    + (trim.equals("recorte=off") ? "" : " " + trim);
        }
    }

    public static void writeTrajectory(Path file, PedestrianEvent e, Simulation.Result sim, RunInfo info) throws IOException {
        Files.createDirectories(file.toAbsolutePath().getParent());
        try (BufferedWriter out = Files.newBufferedWriter(file, StandardCharsets.UTF_8)) {
            out.write(String.format(Locale.ROOT, "# evento=%d id1=%d id2=%d frame_inicial=%d frame_final=%d dt_exp=%s %s\n",
                    e.number(), e.left().id(), e.right().id(), e.firstFrame(), e.lastFrame(), e.dtExp(), info.header()));
            out.write("# t x1 y1 vx1 vy1 x2 y2 vx2 vy2\n");
            for (double[] row : sim.rows()) {
                StringBuilder line = new StringBuilder(96);
                for (int c = 0; c < row.length; c++) {
                    if (c > 0) line.append(' ');
                    line.append(String.format(Locale.ROOT, "%.6f", row[c]));
                }
                out.write(line.append('\n').toString());
            }
        }
    }
}
