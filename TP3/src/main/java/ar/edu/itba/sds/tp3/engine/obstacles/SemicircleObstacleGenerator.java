package ar.edu.itba.sds.tp3.engine.obstacles;

import ar.edu.itba.sds.tp3.engine.SimulationConfig;
import ar.edu.itba.sds.tp3.models.Obstacle;
import java.util.*;

/** Deja libre solamente el círculo de radio freeRadius centrado sobre el eje de la mesa a
 * distancia centerOffset de la línea del arco derecho, (L - centerOffset, W/2), o también su
 * simétrico (centerOffset, W/2) con bothGoals, y rellena con {@link RegionFill} el resto de la mesa.
 * Con centerOffset = 0 la zona libre es un semicírculo centrado en el arco; con freeRadius = 0.3 L
 * y un solo arco se bloquea el 70 % izquierdo del largo de la mesa. Con ambos arcos forma un
 * cuenco: un embudo de pared curva alrededor de cada arco. Al alejar el centro del arco la pared
 * se cierra sobre él; se exige que los palos sigan dentro de la zona libre.
 * Con edgeRadius finito, la frontera con la zona libre es una cadena de discos de ese radio
 * centrados sobre cada circunferencia ({@link DiscChain}), apoyada en las paredes; el resto se
 * rellena detrás de ella. Con edgeRadius NaN, todo se rellena con {@link RegionFill}.
 */
public final class SemicircleObstacleGenerator implements ObstacleGenerator {
    private static final int SAMPLES = 20_000;
    private final double freeRadius, centerOffset, edgeRadius, maxRadius, grid;
    private final boolean bothGoals;

    public SemicircleObstacleGenerator(double freeRadius, boolean bothGoals, double maxRadius, double grid) {
        this(freeRadius, 0, Double.NaN, bothGoals, maxRadius, grid);
    }

    public SemicircleObstacleGenerator(double freeRadius, double centerOffset, double edgeRadius, boolean bothGoals, double maxRadius, double grid) {
        if (!Double.isFinite(freeRadius) || freeRadius <= 0)
            throw new IllegalArgumentException("Radio libre debe ser positivo");
        if (!Double.isFinite(centerOffset) || centerOffset < 0)
            throw new IllegalArgumentException("El desplazamiento del centro no puede ser negativo");
        if (!Double.isNaN(edgeRadius) && !(edgeRadius > 0 && Double.isFinite(edgeRadius)))
            throw new IllegalArgumentException("Radio de la frontera del semicírculo debe ser positivo");
        this.freeRadius = freeRadius;
        this.edgeRadius = edgeRadius;
        this.centerOffset = centerOffset;
        this.bothGoals = bothGoals;
        this.maxRadius = maxRadius;
        this.grid = grid;
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed) {
        return generate(c, seed, List.of());
    }

    @Override public List<Obstacle> generate(SimulationConfig c, long seed, List<Obstacle> existing) {
        if (freeRadius >= c.length()) throw new IllegalArgumentException("El radio libre debe ser menor que L");
        if (Math.hypot(centerOffset, c.goalWidth() / 2) >= freeRadius)
            throw new IllegalArgumentException("Con desplazamiento " + centerOffset + " los palos quedan fuera de la zona libre: el círculo bloquea el arco");
        double right = c.length() - centerOffset, left = centerOffset, mid = c.width() / 2;
        List<Obstacle> edge = new ArrayList<>();
        if (!Double.isNaN(edgeRadius)) {
            if (bothGoals && right - left < 2 * freeRadius + 2 * edgeRadius)
                throw new IllegalArgumentException("Con frontera de discos, los dos círculos libres no pueden tocarse");
            edge.addAll(edge(c, right, mid));
            if (bothGoals) edge.addAll(edge(c, left, mid));
        }
        List<Obstacle> base = new ArrayList<>(existing);
        base.addAll(edge);
        List<Obstacle> result = new ArrayList<>(edge);
        result.addAll(RegionFill.fill(c, (x, y) -> {
            double toRight = Math.hypot(x - right, y - mid);
            return (bothGoals ? Math.min(toRight, Math.hypot(x - left, y - mid)) : toRight) - freeRadius;
        }, maxRadius, grid, base));
        return List.copyOf(result);
    }

    /** Cadenas de discos de radio ρ centrados sobre la circunferencia de centro (cx, cy): una por
     * cada tramo donde el disco entra en la mesa. Sus extremos quedan apoyados en las paredes. */
    private List<Obstacle> edge(SimulationConfig c, double cx, double cy) {
        double rho = edgeRadius, eps = 1e-9;
        boolean[] inside = new boolean[SAMPLES];
        double[] px = new double[SAMPLES], py = new double[SAMPLES];
        for (int i = 0; i < SAMPLES; i++) {
            double t = 2 * Math.PI * i / SAMPLES;
            px[i] = cx + freeRadius * Math.cos(t); py[i] = cy + freeRadius * Math.sin(t);
            inside[i] = px[i] >= rho + eps && px[i] <= c.length() - rho - eps && py[i] >= rho + eps && py[i] <= c.width() - rho - eps;
        }
        int start = 0;
        while (start < SAMPLES && inside[start]) start++;
        if (start == SAMPLES) throw new IllegalArgumentException("El círculo libre no toca las paredes");
        List<Obstacle> chain = new ArrayList<>();
        for (int i = 1; i <= SAMPLES; i++) {
            int k = (start + i) % SAMPLES;
            if (!inside[k] || inside[(k - 1 + SAMPLES) % SAMPLES]) continue;
            List<double[]> run = new ArrayList<>();
            for (int j = k; inside[j]; j = (j + 1) % SAMPLES) run.add(new double[]{px[j], py[j]});
            chain.addAll(DiscChain.along(run.stream().mapToDouble(p -> p[0]).toArray(),
                    run.stream().mapToDouble(p -> p[1]).toArray(), false, rho, 2 * c.radius()));
        }
        return chain;
    }
}
