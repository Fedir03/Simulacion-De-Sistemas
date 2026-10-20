package ar.edu.itba.sds.tp4.engine;

import ar.edu.itba.sds.tp4.engine.cim.Particle;
import java.util.*;

/** Condición inicial por grilla única (D5): sitios fijos dentro del círculo; cada semilla sortea N sin reemplazo. */
public final class GridPlacement {
    private GridPlacement() { }

    public enum Lattice { SQUARE, HEX }
    /** SITE_AT_ORIGIN: hay un sitio en (0, 0). CELL_CENTER_AT_ORIGIN: la red se corre media celda en x e y. */
    public enum Anchor { SITE_AT_ORIGIN, CELL_CENTER_AT_ORIGIN }

    public record Site(double x, double y) { }
    public record Placed(int id, double x, double y, double vx, double vy) {
        public Particle particle(double radius) { return new Particle(id, x, y, radius); }
    }

    /** Los dos obstáculos del enunciado, en (−x0, 0) y (+x0, 0). Ids negativos para no chocar con los de las partículas. */
    public static List<Particle> obstacles(double x0, double radius) {
        return List.of(new Particle(-1, -x0, 0, radius), new Particle(-2, x0, 0, radius));
    }

    /**
     * Sitios de la red con separación {@code spacing} entre vecinos que no tocan la pared (|sitio| ≤ R − r)
     * ni ningún obstáculo (distancia ≥ r + radio del obstáculo). Orden fijo: por fila y dentro de la fila por x.
     */
    public static List<Site> sites(Lattice lattice, Anchor anchor, double spacing, double domainRadius, double radius,
                                   List<Particle> obstacles) {
        if (spacing < 2 * radius) throw new IllegalArgumentException("La separación entre sitios debe ser ≥ 2r: " + spacing);
        double rowHeight = lattice == Lattice.HEX ? spacing * Math.sqrt(3) / 2 : spacing;
        double shift = anchor == Anchor.CELL_CENTER_AT_ORIGIN ? 0.5 : 0;
        int rows = (int) Math.ceil(domainRadius / rowHeight) + 1, cols = (int) Math.ceil(domainRadius / spacing) + 1;
        List<Site> sites = new ArrayList<>();
        for (int j = -rows; j <= rows; j++) {
            // En la hex las filas impares se corren media separación en x
            double rowShift = lattice == Lattice.HEX && Math.floorMod(j, 2) == 1 ? 0.5 : 0;
            double y = (j + shift) * rowHeight;
            for (int i = -cols; i <= cols; i++) {
                double x = (i + rowShift + shift) * spacing;
                if (Math.hypot(x, y) > domainRadius - radius) continue;
                boolean free = true;
                for (Particle o : obstacles)
                    if (Math.hypot(x - o.x(), y - o.y()) < radius + o.radius()) { free = false; break; }
                if (free) sites.add(new Site(x, y));
            }
        }
        return sites;
    }

    /** Sortea n sitios sin reemplazo y direcciones uniformes en [0, 2π), todo con el mismo Random(seed). Ids 1..n. */
    public static List<Placed> place(List<Site> sites, int n, long seed, double speed) {
        if (n <= 0) throw new IllegalArgumentException("N debe ser positivo");
        if (n > sites.size())
            throw new IllegalArgumentException("N imposible: se pidieron " + n + " partículas y la grilla tiene " + sites.size() + " sitios libres");
        Random random = new Random(seed);
        List<Site> shuffled = new ArrayList<>(sites);
        Collections.shuffle(shuffled, random);
        List<Placed> placed = new ArrayList<>(n);
        for (int id = 1; id <= n; id++) {
            Site s = shuffled.get(id - 1);
            double angle = random.nextDouble() * 2 * Math.PI;
            placed.add(new Placed(id, s.x(), s.y(), speed * Math.cos(angle), speed * Math.sin(angle)));
        }
        return placed;
    }
}
