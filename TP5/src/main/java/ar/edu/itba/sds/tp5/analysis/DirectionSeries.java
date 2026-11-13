package ar.edu.itba.sds.tp5.analysis;

import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

/**
 * Serie de direcciones de una corrida, para el análisis: en cada fila de salida, e_t y e_target de cada agente.
 * Se evalúa con el estado de esa fila, sin cambiar la corrida. NaN si el agente ya se retiró.
 */
public final class DirectionSeries {
    private DirectionSeries() { }

    public static void write(Path file, PedestrianEvent e, Simulation sim, AvoidanceLayer layer, int v0Frames) throws IOException {
        Files.createDirectories(file.toAbsolutePath().getParent());
        Agent[] agents = { Agent.from(e, 0, v0Frames), Agent.from(e, 1, v0Frames) };
        AvoidanceLayer[] layers = { layer.forAgent(0), layer.forAgent(1) };
        int every = sim.outputEvery();
        StringBuilder text = new StringBuilder("# t on1 ex1 ey1 tx1 ty1 on2 ex2 ey2 tx2 ty2\n");
        double[] out = new double[2];
        sim.run(agents, e.dtExp(), e.windowIntervals(), (step, t, r, v, active, on) -> {
            if (step % every != 0) return;
            text.append(String.format(Locale.ROOT, "%.6f", t));
            for (int i = 0; i < 2; i++) {
                if (!active[i]) {
                    text.append(" NaN NaN NaN NaN NaN");
                    continue;
                }
                int j = 1 - i;
                double dx = agents[i].targetX() - r[2 * i], dy = agents[i].targetY() - r[2 * i + 1], d = Math.hypot(dx, dy);
                double ex = d > 0 ? dx / d : 0, ey = d > 0 ? dy / d : 0;
                out[0] = ex;
                out[1] = ey;
                boolean layerOn = active[j] && d > 0
                        && layers[i].directionWithVelocity(r[2 * i], r[2 * i + 1], v[2 * i], v[2 * i + 1], r[2 * j], r[2 * j + 1], v[2 * j], v[2 * j + 1], agents[i].desiredSpeed(), ex, ey, out);
                text.append(String.format(Locale.ROOT, " %d %.6f %.6f %.6f %.6f", layerOn ? 1 : 0, ex, ey, out[0], out[1]));
            }
            text.append('\n');
        });
        try (BufferedWriter writer = Files.newBufferedWriter(file, StandardCharsets.UTF_8)) {
            writer.write(text.toString());
        }
    }
}
