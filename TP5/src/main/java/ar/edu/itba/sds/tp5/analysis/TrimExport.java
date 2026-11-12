package ar.edu.itba.sds.tp5.analysis;

import ar.edu.itba.sds.tp5.data.FrontalTrim;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Locale;

/**
 * Exporta el recorte tal como lo usa el motor, para verificarlo a ojo:
 * <ul>
 *   <li>{@code trayectorias_recortadas.csv}: cada frame del evento completo, con una marca de si queda en el recorte.</li>
 *   <li>{@code recorte_eventos.csv}: por peatón, ventana, target, v_d y v_0 sin recorte (D3) y con recorte,
 *   tomados de {@link Agent#from}, más el frame de distancia mínima real.</li>
 * </ul>
 */
public final class TrimExport {
    private TrimExport() { }

    public static void write(Path dir, List<PedestrianEvent> raw, FrontalTrim.Options trim, int v0Frames) throws IOException {
        Files.createDirectories(dir);
        try (PrintWriter tr = new PrintWriter(Files.newBufferedWriter(dir.resolve("trayectorias_recortadas.csv"), StandardCharsets.UTF_8));
             PrintWriter ev = new PrintWriter(Files.newBufferedWriter(dir.resolve("recorte_eventos.csv"), StandardCharsets.UTF_8))) {
            tr.print("evento,peaton,id,frame,x,y,en_recorte\n");
            ev.print("evento,peaton,id,dt_exp,frame_ini,frame_fin,frame_ini_rec,frame_fin_rec,frames_rec,frame_min,d_min,"
                    + "target_x,target_y,target_x_rec,target_y_rec,vd,vd_rec,v0x,v0y,v0x_rec,v0y_rec,recorte\n");
            for (PedestrianEvent full : raw) {
                PedestrianEvent cut = FrontalTrim.apply(full, trim);
                PedestrianEvent.MinDistance min = full.minDistance();
                for (int i = 0; i < 2; i++) {
                    var t = full.pedestrian(i);
                    int framesIn = 0;
                    for (int k = 0; k < t.size(); k++) {
                        int f = t.frames()[k];
                        boolean in = f >= cut.firstFrame() && f <= cut.lastFrame();
                        if (in) framesIn++;
                        tr.print(String.format(Locale.ROOT, "%d,%d,%d,%d,%.5f,%.5f,%d%n", full.number(), i + 1, t.id(), f, t.x()[k], t.y()[k], in ? 1 : 0));
                    }
                    Agent a = Agent.from(full, i, v0Frames), b = Agent.from(cut, i, v0Frames);
                    ev.print(String.format(Locale.ROOT, "%d,%d,%d,%.12f,%d,%d,%d,%d,%d,%d,%.5f,%.5f,%.5f,%.5f,%.5f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%s%n",
                            full.number(), i + 1, t.id(), full.dtExp(), full.firstFrame(), full.lastFrame(), cut.firstFrame(), cut.lastFrame(),
                            framesIn, min.frame(), min.distance(), a.targetX(), a.targetY(), b.targetX(), b.targetY(),
                            a.desiredSpeed(), b.desiredSpeed(), a.vx0(), a.vy0(), b.vx0(), b.vy0(), trim.label()));
                }
            }
        }
    }
}
