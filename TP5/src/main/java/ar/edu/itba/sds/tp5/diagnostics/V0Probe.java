package ar.edu.itba.sds.tp5.diagnostics;

import ar.edu.itba.sds.tp5.Main;
import ar.edu.itba.sds.tp5.data.EventParser;
import ar.edu.itba.sds.tp5.data.FrontalTrim;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Integrator;
import ar.edu.itba.sds.tp5.engine.SfmParameters;
import ar.edu.itba.sds.tp5.engine.Simulation;
import ar.edu.itba.sds.tp5.engine.layer.AvoidanceLayer;
import ar.edu.itba.sds.tp5.engine.layer.LayerConstants;
import ar.edu.itba.sds.tp5.engine.layer.Layers;
import ar.edu.itba.sds.tp5.io.OutputFiles;
import ar.edu.itba.sds.tp5.analysis.ContactMonitor;
import ar.edu.itba.sds.tp5.analysis.Ecm;
import ar.edu.itba.sds.tp5.analysis.EcmReport;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Prueba de la velocidad inicial para el diagnóstico de A. No es parte del motor y no va al ZIP.
 * Corre los 19 eventos como {@code baseline} pero con la velocidad inicial reemplazada (solo como prueba, no como cambio):
 * fit = ajuste de D12 (tiene que reproducir la corrida oficial byte a byte); vd_target = v_d e_target; vd_fitdir = v_d en la dirección del ajuste.
 * Uso: java -cp target/tp5.jar ar.edu.itba.sds.tp5.diagnostics.V0Probe --mode fit|vd_target|vd_fitdir --out DIR
 *      [--layer none|a|b --p1 X --p2 Y] [--rho 0.9] [--v0-frames 5] [--dt-div 64] [--data data] [opciones de recorte]
 */
public final class V0Probe {
    private V0Probe() { }

    static Agent agent(PedestrianEvent e, int i, int v0Frames, String mode) {
        Agent a = Agent.from(e, i, v0Frames);
        double vd = a.desiredSpeed(), dx, dy;
        switch (mode) {
            case "fit" -> { return a; }
            case "vd_target" -> { dx = a.targetX() - a.x0(); dy = a.targetY() - a.y0(); }
            case "vd_fitdir" -> { dx = a.vx0(); dy = a.vy0(); }
            default -> throw new IllegalArgumentException("--mode debe ser fit, vd_target o vd_fitdir: " + mode);
        }
        double n = Math.hypot(dx, dy);
        return new Agent(a.x0(), a.y0(), vd * dx / n, vd * dy / n, a.targetX(), a.targetY(), vd);
    }

    public static void main(String[] args) throws IOException {
        Map<String, String> o = new HashMap<>();
        for (int i = 0; i + 1 < args.length; i += 2) o.put(args[i].substring(2), args[i + 1]);
        String mode = o.getOrDefault("mode", "fit");
        int v0Frames = Integer.parseInt(o.getOrDefault("v0-frames", String.valueOf(Main.DEFAULT_V0_FRAMES)));
        int dtDiv = Integer.parseInt(o.getOrDefault("dt-div", String.valueOf(Simulation.DEFAULT_DT_DIV)));
        double deltaA = SfmParameters.DEFAULT_DELTA_A;
        String name = o.getOrDefault("layer", "none");
        AvoidanceLayer layer = name.equalsIgnoreCase("none") ? AvoidanceLayer.NONE
                : Layers.of(name, Double.parseDouble(o.get("p1")), Double.parseDouble(o.get("p2")),
                        LayerConstants.of(Double.parseDouble(o.getOrDefault("rho", String.valueOf(LayerConstants.DEFAULT_RHO))),
                                LayerConstants.DEFAULT_FRONTAL_DEGREES, LayerConstants.FrontalTie.METRIC));
        Integrator integrator = Integrator.DEFAULT;
        Simulation sim = new Simulation(SfmParameters.withDeltaA(deltaA), integrator, dtDiv, layer);
        FrontalTrim.Options trim = FrontalTrim.Options.parse(o);
        String label = mode.equals("fit") ? layer.label() : layer.label() + " v0=" + mode;
        OutputFiles.RunInfo info = new OutputFiles.RunInfo(integrator.name(), dtDiv, v0Frames, deltaA, label, trim.label());
        Path out = Path.of(o.getOrDefault("out", "outputs/pilot/diagnostico_A/corridas/" + mode));

        List<EcmReport.EventReport> reports = new ArrayList<>();
        for (PedestrianEvent e : FrontalTrim.apply(EventParser.parse(Path.of(o.getOrDefault("data", "data"))), trim)) {
            Agent[] agents = { agent(e, 0, v0Frames, mode), agent(e, 1, v0Frames, mode) };
            ContactMonitor contacts = new ContactMonitor(SfmParameters.withDeltaA(deltaA).radius());
            Simulation.Result result = sim.run(agents, e.dtExp(), e.windowIntervals(), contacts);
            double[] extended = result.arrival().clone();
            if (Double.isNaN(extended[0]) || Double.isNaN(extended[1]))
                extended = sim.run(agents, e.dtExp(), Main.EXTENDED_INTERVALS).arrival();
            EcmReport.EventReport report = new EcmReport.EventReport(e, result, Ecm.of(e, result), contacts.stats(), extended);
            OutputFiles.writeTrajectory(out.resolve(String.format("evento_%02d.txt", e.number())), e, result, info);
            reports.add(report);
        }
        EcmReport.write(out.resolve("ecm.txt"), reports, info);
        System.out.println("Salida: " + out + " | v0=" + mode + " | " + layer.label());
    }
}
