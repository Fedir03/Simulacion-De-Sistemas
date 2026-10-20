package ar.edu.itba.sds.tp4.engine;

import ar.edu.itba.sds.tp4.engine.GridPlacement.*;
import ar.edu.itba.sds.tp4.engine.cim.Particle;
import java.io.PrintStream;
import java.util.List;

/** Medición del N máx colocable con la grilla (D6): cuenta sitios y verifica la colocación con N = N máx. */
public final class GridCapacity {
    private GridCapacity() { }
    // Enunciado, Sistema 2
    static final double R = 0.51, PARTICLE_RADIUS = 0.0175, OBSTACLE_RADIUS = 0.0175, V0 = 1;
    static final double[] GAPS = {0, 1e-4, 5e-4, 1e-3};
    static final double[] X0_D13 = {0.0175, 0.06, 0.12, 0.18, 0.24, 0.30, 0.36, 0.43, 0.4925};
    static final int SEEDS = 5;
    /** Por debajo de −1e-12 m es solapamiento real; entre −1e-12 y 0 es redondeo de la red (√3, sumas de s). */
    static final double ROUNDING = 1e-12;

    /** Menor distancia borde a borde: entre partículas, con la pared (R − |r| − r) y con los obstáculos. */
    public static double minClearance(List<Placed> placed, double r, List<Particle> obstacles) {
        double min = Double.POSITIVE_INFINITY;
        for (int i = 0; i < placed.size(); i++) {
            Placed a = placed.get(i);
            min = Math.min(min, R - Math.hypot(a.x(), a.y()) - r);
            for (Particle o : obstacles) min = Math.min(min, Math.hypot(a.x() - o.x(), a.y() - o.y()) - r - o.radius());
            for (int j = i + 1; j < placed.size(); j++) {
                Placed b = placed.get(j);
                min = Math.min(min, Math.hypot(a.x() - b.x(), a.y() - b.y()) - 2 * r);
            }
        }
        return min;
    }

    static String classify(double clearance) {
        return clearance >= 0 ? "ok" : clearance >= -ROUNDING ? "redondeo" : "SOLAPA";
    }

    public static void report(PrintStream out) {
        out.printf("R=%s m  r=%s m  r_obs=%s m  semillas=%d  (separación s = 2r + extra)%n", R, PARTICLE_RADIUS, OBSTACLE_RADIUS, SEEDS);
        out.printf("%-6s %-12s %8s | %9s %12s %-9s | %9s %12s %-9s | %s%n", "red", "anclaje", "extra[mm]",
                "N sin obs", "min [m]", "estado", "N x0=r", "min [m]", "estado", "N mín en x0 de D13");
        for (Lattice lattice : Lattice.values())
            for (Anchor anchor : Anchor.values())
                for (double gap : GAPS) {
                    double s = 2 * PARTICLE_RADIUS + gap;
                    String none = check(lattice, anchor, s, List.of());
                    String touching = check(lattice, anchor, s, GridPlacement.obstacles(PARTICLE_RADIUS, OBSTACLE_RADIUS));
                    int minD13 = Integer.MAX_VALUE;
                    for (double x0 : X0_D13)
                        minD13 = Math.min(minD13, GridPlacement.sites(lattice, anchor, s, R, PARTICLE_RADIUS,
                                GridPlacement.obstacles(x0, OBSTACLE_RADIUS)).size());
                    out.printf("%-6s %-12s %8.1f | %s | %s | %d%n", lattice, anchor == Anchor.SITE_AT_ORIGIN ? "sitio" : "centro-celda",
                            gap * 1e3, none, touching, minD13);
                }
    }

    /** N máx = sitios libres; coloca N máx con cada semilla y se queda con la peor distancia. */
    private static String check(Lattice lattice, Anchor anchor, double s, List<Particle> obstacles) {
        List<Site> sites = GridPlacement.sites(lattice, anchor, s, R, PARTICLE_RADIUS, obstacles);
        double worst = Double.POSITIVE_INFINITY;
        for (long seed = 1; seed <= SEEDS; seed++)
            worst = Math.min(worst, minClearance(GridPlacement.place(sites, sites.size(), seed, V0), PARTICLE_RADIUS, obstacles));
        return String.format("%9d %12.3e %-9s", sites.size(), worst, classify(worst));
    }
}
