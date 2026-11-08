package ar.edu.itba.sds.tp5.diagnostics;

import ar.edu.itba.sds.tp5.data.EventParser;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Integrator;
import ar.edu.itba.sds.tp5.engine.SfmParameters;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import ar.edu.itba.sds.tp5.engine.layer.CollisionPrediction;
import ar.edu.itba.sds.tp5.engine.layer.LayerConstants;
import ar.edu.itba.sds.tp5.engine.layer.Layers;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Traza de una corrida: cada conmutación de la capa, con la condición que la causó, y cada episodio de contacto.
 * No es parte del motor y no va al ZIP. Uso:
 * java -cp target/tp5.jar ar.edu.itba.sds.tp5.diagnostics.RunTrace --event N --layer a|b|f --p1 X --p2 Y [--v0-frames 5] [--rho 0.9] [--data data] [--dt-div 64]
 */
public final class RunTrace {
    private RunTrace() { }

    /** Una conmutación: {@code cause} lista las condiciones de la detección que cambiaron respecto del paso anterior. */
    public record Switch(double t, int agent, boolean on, double tStar, double dMin, double sideOffset, double distance, boolean contact, String cause) { }

    /** Un episodio de contacto entre los dos agentes. */
    public record Contact(double start, double end, double maxOverlap) { }

    /** Un cambio del lado de esquive n (regla de A y B) con la capa prendida: {@code side} es el s_c que lo produjo. */
    public record SideFlip(double t, int agent, double side, double distance) { }

    public record Trace(List<Switch> switches, List<Contact> contacts, List<SideFlip> flips, Simulation.Result result) { }

    public static Trace run(PedestrianEvent e, AvoidanceLayer layer, double horizon, LayerConstants constants, int v0Frames) {
        return run(e, layer, horizon, constants, v0Frames, Simulation.DEFAULT_DT_DIV);
    }

    public static Trace run(PedestrianEvent e, AvoidanceLayer layer, double horizon, LayerConstants constants, int v0Frames, int dtDiv) {
        SfmParameters p = SfmParameters.defaults();
        Agent[] agents = { Agent.from(e, 0, v0Frames), Agent.from(e, 1, v0Frames) };
        List<Switch> switches = new ArrayList<>();
        List<Contact> contacts = new ArrayList<>();
        List<SideFlip> flips = new ArrayList<>();
        double[] lastSign = new double[2];      // lado de esquive vigente; 0 con la capa apagada
        boolean[] lastOn = new boolean[2];
        String[] lastState = { "", "" };
        double[] open = { Double.NaN, 0 };      // inicio y mayor solapamiento del episodio en curso
        double[] lastTime = { 0 };
        Simulation sim = new Simulation(p, Integrator.DEFAULT, dtDiv, layer);
        Simulation.Result result = sim.run(agents, e.dtExp(), e.windowIntervals(), (step, t, r, v, active, on) -> {
            double d = Math.hypot(r[0] - r[2], r[1] - r[3]);
            double overlap = 2 * p.radius() - d;
            boolean touching = active[0] && active[1] && overlap > 0;
            if (touching) {
                if (Double.isNaN(open[0])) { open[0] = t; open[1] = 0; }
                open[1] = Math.max(open[1], overlap);
            } else if (!Double.isNaN(open[0])) {
                contacts.add(new Contact(open[0], t, open[1]));
                open[0] = Double.NaN;
            }
            lastTime[0] = t;
            for (int i = 0; i < 2; i++) {
                if (!active[i]) continue;
                int j = 1 - i;
                double dx = agents[i].targetX() - r[2 * i], dy = agents[i].targetY() - r[2 * i + 1], norm = Math.hypot(dx, dy);
                double ex = norm > 0 ? dx / norm : 0, ey = norm > 0 ? dy / norm : 0;
                CollisionPrediction c = active[j]
                        ? CollisionPrediction.of(r[2 * i], r[2 * i + 1], r[2 * j], r[2 * j + 1], v[2 * j], v[2 * j + 1], agents[i].desiredSpeed(), ex, ey)
                        : null;
                String state = state(c, active[j], horizon, constants.rho());
                if (on[i] != lastOn[i]) {
                    double tStar = c == null ? Double.NaN : c.tStar(), dMin = c == null ? Double.NaN : c.dMin();
                    double side = c == null ? Double.NaN : ey * c.closestX() - ex * c.closestY();
                    switches.add(new Switch(t, i, on[i], tStar, dMin, side, d, touching, cause(lastState[i], state)));
                }
                if (on[i] && c != null) {
                    double side = ey * c.closestX() - ex * c.closestY();
                    double sign = Math.abs(side) > constants.sideEpsilon() ? -Math.signum(side) : 1;
                    if (lastSign[i] != 0 && sign != lastSign[i]) flips.add(new SideFlip(t, i, side, d));
                    lastSign[i] = sign;
                } else {
                    lastSign[i] = 0;
                }
                lastOn[i] = on[i];
                lastState[i] = state;
            }
        });
        if (!Double.isNaN(open[0])) contacts.add(new Contact(open[0], lastTime[0], open[1]));
        return new Trace(switches, contacts, flips, result);
    }

    /** Las tres condiciones de la detección, codificadas para comparar pasos. */
    private static String state(CollisionPrediction c, boolean otherActive, double horizon, double rho) {
        if (!otherActive) return "retirado";
        if (c == null) return "w0";
        return (c.tStar() > 0 ? "T" : "t") + (c.tStar() <= horizon ? "H" : "h") + (c.dMin() < rho ? "R" : "r");
    }

    private static String cause(String before, String now) {
        if (now.equals("retirado")) return "otro_retirado";
        if (before.length() != 3 || now.length() != 3) return "otra";
        List<String> causes = new ArrayList<>();
        if (before.charAt(0) != now.charAt(0)) causes.add("t*_cruza_0");
        if (before.charAt(1) != now.charAt(1)) causes.add("t*_cruza_t_a");
        if (before.charAt(2) != now.charAt(2)) causes.add("d_min_cruza_rho");
        return causes.isEmpty() ? "vision" : String.join("+", causes);
    }

    public static void main(String[] args) throws IOException {
        Map<String, String> o = new HashMap<>();
        for (int i = 0; i + 1 < args.length; i += 2) o.put(args[i].substring(2), args[i + 1]);
        int event = Integer.parseInt(o.get("event"));
        double p1 = Double.parseDouble(o.get("p1")), p2 = Double.parseDouble(o.get("p2"));
        String layerName = o.get("layer");
        LayerConstants constants = LayerConstants.of(Double.parseDouble(o.getOrDefault("rho", "0.9")), LayerConstants.DEFAULT_FRONTAL_DEGREES, LayerConstants.FrontalTie.METRIC);
        int v0Frames = Integer.parseInt(o.getOrDefault("v0-frames", "5"));
        double horizon = layerName.equalsIgnoreCase("f") ? Double.POSITIVE_INFINITY : p1;
        PedestrianEvent e = EventParser.parse(Path.of(o.getOrDefault("data", "data"))).stream().filter(x -> x.number() == event).findFirst().orElseThrow();
        int dtDiv = Integer.parseInt(o.getOrDefault("dt-div", String.valueOf(Simulation.DEFAULT_DT_DIV)));
        Trace trace = run(e, Layers.of(layerName, p1, p2, constants), horizon, constants, v0Frames, dtDiv);
        PrintStream out = System.out;
        out.printf(Locale.ROOT, "R id1=%d id2=%d conm1=%d conm2=%d d_min=%.4f t_d_min=%.4f%n", e.left().id(), e.right().id(),
                trace.result().layerSwitches()[0], trace.result().layerSwitches()[1], trace.result().minDistance(), trace.result().minDistanceTime());
        for (SideFlip f : trace.flips()) out.printf(Locale.ROOT, "L %.4f %d %.4f %.4f%n", f.t(), f.agent() + 1, f.side(), f.distance());
        for (Contact c : trace.contacts()) out.printf(Locale.ROOT, "C %.4f %.4f %.5f%n", c.start(), c.end(), c.maxOverlap());
        for (Switch s : trace.switches())
            out.printf(Locale.ROOT, "S %.4f %d %s %.4f %.4f %.4f %.4f %b %s%n", s.t(), s.agent() + 1, s.on() ? "on" : "off", s.tStar(), s.dMin(), s.sideOffset(), s.distance(), s.contact(), s.cause());
    }
}
