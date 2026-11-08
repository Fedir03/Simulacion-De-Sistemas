package ar.edu.itba.sds.tp5.diagnostics;

import ar.edu.itba.sds.tp5.data.EventParser;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.data.Trajectory;
import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Integrator;
import ar.edu.itba.sds.tp5.engine.SfmParameters;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import ar.edu.itba.sds.tp5.engine.layer.CollisionPrediction;
import ar.edu.itba.sds.tp5.engine.layer.LayerConstants;
import ar.edu.itba.sds.tp5.engine.layer.Layers;
import ar.edu.itba.sds.tp5.metrics.Ecm;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Locale;
import java.util.Random;
import java.util.stream.IntStream;

/**
 * Mediciones de la auditoría de capas. No es parte del motor y no va al ZIP.
 * Uso: java -cp target/tp5.jar ar.edu.itba.sds.tp5.diagnostics.LayerChecks audit|coin DATA ARCHIVO capa:p1:p2 ... o recovery DATA ARCHIVO
 */
public final class LayerChecks {
    private LayerChecks() { }

    /** Lo que vio la capa de un agente en una corrida, separando las evaluaciones que mueven al agente de las que solo cuentan. */
    public static final class AgentStats {
        long forceCalls, on, overlap, onOverlap, tie, tieLeft;
        int switchesForce, switchesCheck, flipsWithin, flipsEvent;
        double maxTieLeftSin, minTieLeftDistance = Double.POSITIVE_INFINITY;
        private long calls;
        private boolean lastForce, lastCheck;
        private double sideActivation, sideEvent;

        public int switchesForce() { return switchesForce; }
        public int switchesCheck() { return switchesCheck; }
        public int flipsEvent() { return flipsEvent; }
        public long tie() { return tie; }
        public long tieLeft() { return tieLeft; }
        public long onOverlap() { return onOverlap; }
    }

    /**
     * Envuelve una capa sin cambiarla. Beeman evalúa el campo dos veces al arrancar (t = 0 y t = −Δt) y después
     * Simulation y el integrador se alternan: evaluación de conteo, con la v corregida, y evaluación de la fuerza, con la v predicha.
     */
    public static final class Recorder implements AvoidanceLayer {
        private final AvoidanceLayer base;
        private final double sideEpsilon, radius;
        private final AgentStats[] stats = { new AgentStats(), new AgentStats() };

        public Recorder(AvoidanceLayer base, double sideEpsilon, double radius) {
            this.base = base;
            this.sideEpsilon = sideEpsilon;
            this.radius = radius;
        }

        public AgentStats stats(int agent) { return stats[agent]; }

        @Override public AvoidanceLayer forAgent(int agent) {
            AgentStats s = stats[agent];
            return new AvoidanceLayer() {
                @Override public boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                                   double vd, double ex, double ey, double[] out) {
                    boolean on = base.direction(xi, yi, xj, yj, vxj, vyj, vd, ex, ey, out);
                    observe(s, on, xi, yi, xj, yj, vxj, vyj, vd, ex, ey, out);
                    return on;
                }
                @Override public String label() { return base.label(); }
            };
        }

        @Override public boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                           double vd, double ex, double ey, double[] out) {
            throw new IllegalStateException("Se usa a través de forAgent");
        }

        @Override public String label() { return base.label(); }

        private void observe(AgentStats s, boolean on, double xi, double yi, double xj, double yj, double vxj, double vyj,
                             double vd, double ex, double ey, double[] out) {
            long k = s.calls++;
            if (k == 1) return;                 // estado estimado en −Δt: no es parte de la corrida
            if (k >= 2 && k % 2 == 0) {         // evaluación de conteo
                if (on != s.lastCheck) s.switchesCheck++;
                s.lastCheck = on;
                return;
            }
            s.forceCalls++;
            if (on != s.lastForce) s.switchesForce++;
            s.lastForce = on;
            double d = Math.hypot(xi - xj, yi - yj);
            boolean overlap = d < 2 * radius;
            if (overlap) s.overlap++;
            if (!on) { s.sideActivation = 0; return; }
            s.on++;
            if (overlap) s.onOverlap++;
            double lateral = out[0] * ey - out[1] * ex;     // componente sobre e_t^⊥, la derecha de e_t
            double side = Math.abs(lateral) > 1e-12 ? Math.signum(lateral) : 0;
            if (side != 0) {
                if (s.sideActivation != 0 && side != s.sideActivation) s.flipsWithin++;
                if (s.sideEvent != 0 && side != s.sideEvent) s.flipsEvent++;
                s.sideActivation = side;
                s.sideEvent = side;
            }
            CollisionPrediction p = CollisionPrediction.of(xi, yi, xj, yj, vxj, vyj, vd, ex, ey);
            if (p != null && Math.abs(ey * p.closestX() - ex * p.closestY()) <= sideEpsilon) {
                s.tie++;
                if (lateral < 0) {
                    s.tieLeft++;
                    double sin = d > 0 ? Math.abs(ex * (yj - yi) - ey * (xj - xi)) / d : 0;
                    s.maxTieLeftSin = Math.max(s.maxTieLeftSin, sin);
                    s.minTieLeftDistance = Math.min(s.minTieLeftDistance, d);
                }
            }
        }
    }

    /** El mismo evento reflejado respecto de y = 0. */
    public static PedestrianEvent mirror(PedestrianEvent e) {
        return new PedestrianEvent(e.number(), mirror(e.left()), mirror(e.right()), e.dtExp(), e.leemeMinDistance(), e.firstFrame(), e.lastFrame());
    }

    private static Trajectory mirror(Trajectory t) {
        double[] y = t.y().clone();
        for (int k = 0; k < y.length; k++) y[k] = -y[k];
        return new Trajectory(t.id(), t.frames(), t.x(), y);
    }

    /** Mayor diferencia entre una corrida y el reflejo de otra; infinito si no tienen las mismas filas o un agente se retira en otro momento. */
    public static double mirrorDifference(Simulation.Result a, Simulation.Result b) {
        if (a.rows().size() != b.rows().size()) return Double.POSITIVE_INFINITY;
        double max = 0;
        for (int k = 0; k < a.rows().size(); k++) {
            double[] ra = a.rows().get(k), rb = b.rows().get(k);
            for (int c = 1; c < ra.length; c++) {
                boolean isY = c % 4 == 2 || c % 4 == 0;     // y1, vy1, y2, vy2 son las columnas 2, 4, 6, 8
                double other = isY ? -rb[c] : rb[c];
                if (Double.isNaN(ra[c]) != Double.isNaN(other)) return Double.POSITIVE_INFINITY;
                if (!Double.isNaN(ra[c])) max = Math.max(max, Math.abs(ra[c] - other));
            }
        }
        return max;
    }

    public record Run(Simulation.Result result, Ecm.Event ecm, Recorder recorder) {
        public long ties() { return recorder.stats(0).tie() + recorder.stats(1).tie(); }
    }

    public static Run run(PedestrianEvent e, String layer, double p1, double p2, LayerConstants constants) {
        SfmParameters params = SfmParameters.defaults();
        Recorder recorder = new Recorder(Layers.of(layer, p1, p2, constants), constants.sideEpsilon(), params.radius());
        Simulation sim = new Simulation(params, Integrator.DEFAULT, Simulation.DEFAULT_DT_DIV, recorder);
        Agent[] agents = { Agent.from(e, 0, 5), Agent.from(e, 1, 5) };
        Simulation.Result result = sim.run(agents, e.dtExp(), e.windowIntervals());
        return new Run(result, Ecm.of(e, result), recorder);
    }

    private static void audit(List<PedestrianEvent> events, Path file, String[] pairs) throws IOException {
        LayerConstants c = LayerConstants.defaults();
        Files.createDirectories(file.toAbsolutePath().getParent());
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(file, StandardCharsets.UTF_8))) {
            out.print("# capa p1 p2 evento agente pasos_fuerza pasos_on pasos_solape pasos_on_solape pasos_desempate desempates_izquierda max_sin_izq min_d_izq conm_fuerza conm_conteo cambios_lado_activacion cambios_lado_evento\n");
            out.print("# E capa p1 p2 evento ecm1 ecm1_espejo ecm2 ecm2_espejo dif_espejo desempates desempates_espejo\n");
            for (String pair : pairs) {
                String[] p = pair.split(":");
                double p1 = Double.parseDouble(p[1]), p2 = Double.parseDouble(p[2]);
                for (PedestrianEvent e : events) {
                    Run run = run(e, p[0], p1, p2, c);
                    for (int i = 0; i < 2; i++) {
                        AgentStats s = run.recorder().stats(i);
                        out.print(String.format(Locale.ROOT, "%s %s %s %d %d %d %d %d %d %d %d %.4f %.4f %d %d %d %d", p[0], p[1], p[2], e.number(), i + 1, s.forceCalls, s.on, s.overlap, s.onOverlap,
                                s.tie, s.tieLeft, s.maxTieLeftSin, s.minTieLeftDistance, s.switchesForce, s.switchesCheck, s.flipsWithin, s.flipsEvent) + "\n");
                    }
                    Run mirrored = run(mirror(e), p[0], p1, p2, c);
                    out.print(String.format(Locale.ROOT, "E %s %s %s %d %.6f %.6f %.6f %.6f %.3e %d %d", p[0], p[1], p[2], e.number(),
                            run.ecm().ecm1Excluding(), mirrored.ecm().ecm1Excluding(), run.ecm().ecm2(), mirrored.ecm().ecm2(),
                            mirrorDifference(run.result(), mirrored.result()), run.ties(), mirrored.ties()) + "\n");
                }
            }
        }
    }

    private static final double[] TA = { 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5 };
    private static final double[] LATERAL = { 0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 };
    private static final double[] GAIN = { 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4 };
    private static final double[] AP = { 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9 };
    private static final double[] BP = { 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3 };
    /** Semilla de D8, también para las monedas. */
    public static final long SEED = 20261116L;

    /**
     * La corrida simulada tomada como datos: mismos frames que el experimento y hasta que el agente se retira.
     * El target de estas trayectorias no se usa para simular: los agentes conservan las condiciones del evento real.
     */
    public static PedestrianEvent syntheticEvent(PedestrianEvent e, Simulation.Result sim) {
        return new PedestrianEvent(e.number(), synthetic(e, sim, 0), synthetic(e, sim, 1), e.dtExp(), e.leemeMinDistance(), e.firstFrame(), e.lastFrame());
    }

    private static Trajectory synthetic(PedestrianEvent e, Simulation.Result sim, int agent) {
        Trajectory exp = e.pedestrian(agent);
        List<int[]> kept = new ArrayList<>();
        for (int frame : exp.frames()) {
            if (frame < e.firstFrame() || frame > e.lastFrame()) continue;
            int row = (frame - e.firstFrame()) * Simulation.ROWS_PER_INTERVAL;
            if (!Double.isNaN(sim.x(agent, row))) kept.add(new int[] { frame, row });
        }
        int[] frames = new int[kept.size()];
        double[] x = new double[frames.length], y = new double[frames.length];
        for (int k = 0; k < frames.length; k++) {
            frames[k] = kept.get(k)[0];
            x[k] = sim.x(agent, kept.get(k)[1]);
            y[k] = sim.y(agent, kept.get(k)[1]);
        }
        return new Trajectory(exp.id(), frames, x, y);
    }

    private static Simulation.Result simulate(PedestrianEvent real, AvoidanceLayer layer) {
        Simulation sim = new Simulation(SfmParameters.defaults(), Integrator.DEFAULT, Simulation.DEFAULT_DT_DIV, layer);
        return sim.run(new Agent[] { Agent.from(real, 0, 5), Agent.from(real, 1, 5) }, real.dtExp(), real.windowIntervals());
    }

    private static double[][] pairs(String layer) {
        double[] first = layer.equals("f") ? AP : TA, second = switch (layer) { case "a" -> LATERAL; case "b" -> GAIN; default -> BP; };
        double[][] out = new double[first.length * second.length][];
        for (int i = 0; i < first.length; i++)
            for (int j = 0; j < second.length; j++) out[i * second.length + j] = new double[] { first[i], second[j] };
        return out;
    }

    /** Prueba 4a: genera datos con un par y calibra las tres capas contra ellos, sobre las grillas oficiales. */
    private static void recovery(List<PedestrianEvent> events, Path file) throws IOException {
        LayerConstants c = LayerConstants.defaults();
        Object[][] generators = { { "a", 2.5, 1.5 }, { "b", 2.5, 2.0 }, { "f", 0.8, 3.0 } };
        Files.createDirectories(file.toAbsolutePath().getParent());
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(file, StandardCharsets.UTF_8))) {
            out.print("# generador capa p1 p2 ecm1_excl ecm2 eventos_con_contacto\n");
            for (Object[] g : generators) {
                AvoidanceLayer source = Layers.of((String) g[0], (double) g[1], (double) g[2], c);
                List<PedestrianEvent> data = events.stream().map(e -> syntheticEvent(e, simulate(e, source))).toList();
                String generator = g[0] + ":" + g[1] + ":" + g[2];
                for (String layer : new String[] { "a", "b", "f" }) {
                    double[][] grid = pairs(layer);
                    String[] lines = new String[grid.length];
                    IntStream.range(0, grid.length).parallel().forEach(k -> {
                        AvoidanceLayer fit = Layers.of(layer, grid[k][0], grid[k][1], c);
                        double ecm1 = 0, ecm2 = 0;
                        int contacts = 0;
                        for (int m = 0; m < events.size(); m++) {
                            Simulation.Result run = simulate(events.get(m), fit);
                            Ecm.Event ecm = Ecm.of(data.get(m), run);
                            ecm1 += ecm.ecm1Excluding();
                            ecm2 += ecm.ecm2();
                            if (run.anyContact()) contacts++;
                        }
                        lines[k] = String.format(Locale.ROOT, "%s %s %s %s %.8f %.8f %d", generator, layer, grid[k][0], grid[k][1], ecm1 / events.size(), ecm2 / events.size(), contacts);
                    });
                    for (String line : lines) out.print(line + "\n");
                }
            }
        }
    }

    /** Prueba 4c: la capa elige el lado por una moneda fija de cada agente: refleja e_target respecto de e_t si hace falta. */
    public static AvoidanceLayer coinSide(AvoidanceLayer base, boolean[] toRight) {
        return new AvoidanceLayer() {
            @Override public AvoidanceLayer forAgent(int agent) {
                double sign = toRight[agent] ? 1 : -1;
                return new AvoidanceLayer() {
                    @Override public boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                                       double vd, double ex, double ey, double[] out) {
                        boolean on = base.direction(xi, yi, xj, yj, vxj, vyj, vd, ex, ey, out);
                        if (!on) return false;
                        double along = out[0] * ex + out[1] * ey, lateral = sign * Math.abs(out[0] * ey - out[1] * ex);
                        out[0] = along * ex + lateral * ey;
                        out[1] = along * ey - lateral * ex;
                        return true;
                    }
                    @Override public String label() { return base.label() + " lado=moneda"; }
                };
            }
            @Override public boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                               double vd, double ex, double ey, double[] out) {
                throw new IllegalStateException("Se usa a través de forAgent");
            }
            @Override public String label() { return base.label() + " lado=moneda"; }
        };
    }

    private static void coin(List<PedestrianEvent> events, Path file, String[] pairs) throws IOException {
        LayerConstants c = LayerConstants.defaults();
        Files.createDirectories(file.toAbsolutePath().getParent());
        try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(file, StandardCharsets.UTF_8))) {
            out.print("# capa p1 p2 semilla evento ecm1_excl ecm2 contacto\n");
            for (String pair : pairs) {
                String[] p = pair.split(":");
                AvoidanceLayer base = Layers.of(p[0], Double.parseDouble(p[1]), Double.parseDouble(p[2]), c);
                for (int seed = 0; seed < 20; seed++) {
                    Random random = new Random(SEED + seed);
                    for (PedestrianEvent e : events) {
                        Simulation.Result run = simulate(e, coinSide(base, new boolean[] { random.nextBoolean(), random.nextBoolean() }));
                        Ecm.Event ecm = Ecm.of(e, run);
                        out.print(String.format(Locale.ROOT, "%s %s %s %d %d %.6f %.6f %b", p[0], p[1], p[2], seed, e.number(), ecm.ecm1Excluding(), ecm.ecm2(), run.anyContact()) + "\n");
                    }
                }
            }
        }
    }

    public static void main(String[] args) throws IOException {
        List<PedestrianEvent> events = EventParser.parse(Path.of(args[1]));
        switch (args[0]) {
            case "audit" -> audit(events, Path.of(args[2]), Arrays.copyOfRange(args, 3, args.length));
            case "recovery" -> recovery(events, Path.of(args[2]));
            case "coin" -> coin(events, Path.of(args[2]), Arrays.copyOfRange(args, 3, args.length));
            default -> throw new IllegalArgumentException("Comando desconocido: " + args[0]);
        }
    }
}
