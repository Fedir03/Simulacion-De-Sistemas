package ar.edu.itba.sds.tp3.bench;

import ar.edu.itba.sds.tp3.engine.CollisionSimulator;
import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.engine.StageGeneration;
import ar.edu.itba.sds.tp3.engine.StageGeneration.GridAnchor;
import java.io.IOException;
import java.util.*;

/** Motor del TP3 con mesa vacía y la grilla única del TP4; mide el mismo tramo que Main simulate. */
public final class Tp3Case implements TimedCase {
    private final SimulationConfig config = SimulationConfig.defaults();
    private final GridAnchor anchor;
    private final double margin;
    private StageGeneration.Stage stage;

    public Tp3Case(GridAnchor anchor, double margin) { this.anchor = anchor; this.margin = margin; }

    public int maxN() { return StageGeneration.gridSites(config, List.of(), anchor, StageGeneration.GRID_EXTRA_SPACING, margin).size(); }

    @Override public String describeJson() {
        SimulationConfig c = config;
        return "{\"engine\": \"TP3 CollisionSimulator\", \"obstacles\": 0, \"placement\": \"grid hex\", \"anchor\": \""
                + anchor.name().toLowerCase(Locale.ROOT) + "\", \"extra_spacing_m\": " + StageGeneration.GRID_EXTRA_SPACING
                + ", \"wall_margin_m\": " + margin + ", \"grid_sites\": " + maxN() + ", \"L\": " + c.length() + ", \"W\": " + c.width()
                + ", \"goal_width\": " + c.goalWidth() + ", \"r\": " + c.radius() + ", \"m\": " + c.mass() + ", \"v0\": " + c.speed()
                + ", \"frames\": \"ninguno (sink vacío); el original escribía solo el estado inicial y el final\"}";
    }

    @Override public void prepare(int n, long seed) {
        stage = StageGeneration.generateGrid(config, n, seed, List.of(), anchor, StageGeneration.GRID_EXTRA_SPACING, margin);
    }

    @Override public RunResult runTimed(double tf) throws IOException {
        if (stage == null) throw new IllegalStateException("Llamar a prepare antes de runTimed");
        StageGeneration.Stage s = stage;
        stage = null;
        // Mismo tramo que Main simulate: construcción del simulador y ciclo de eventos.
        long start = System.nanoTime();
        var result = new CollisionSimulator(s).run(tf, Integer.MAX_VALUE, (t, e, g, p) -> { });
        double runtime = (System.nanoTime() - start) / 1e9;
        return new RunResult(runtime, result.events(), result.goals(), result.t90());
    }

    /** java -Xms1g -Xmx1g -cp tp3.jar ar.edu.itba.sds.tp3.bench.Tp3Case --out DIR --ns 100,200 --warmup 300:5,600:0.3 [--grid-anchor corner] [--grid-margin 1e-4] ... */
    public static void main(String[] args) {
        try {
            Map<String, String> options = RuntimeBenchmark.parse(args);
            GridAnchor anchor = switch (options.getOrDefault("grid-anchor", "corner")) {
                case "center" -> GridAnchor.CENTER;
                case "corner" -> GridAnchor.CORNER;
                default -> throw new IllegalArgumentException("--grid-anchor debe ser center o corner");
            };
            double margin = Double.parseDouble(options.getOrDefault("grid-margin", Double.toString(StageGeneration.GRID_EXTRA_SPACING)));
            options.remove("grid-anchor"); options.remove("grid-margin");
            Tp3Case c = new Tp3Case(anchor, margin);
            RuntimeBenchmark.run(c, options, args);
        } catch (IllegalArgumentException | IOException e) {
            System.err.println("Error: " + e.getMessage()); System.exit(1);
        }
    }
}
