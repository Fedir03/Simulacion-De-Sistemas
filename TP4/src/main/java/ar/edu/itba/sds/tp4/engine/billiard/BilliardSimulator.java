package ar.edu.itba.sds.tp4.engine.billiard;

import ar.edu.itba.sds.tp4.engine.GridPlacement;
import ar.edu.itba.sds.tp4.engine.GridPlacement.Anchor;
import ar.edu.itba.sds.tp4.engine.GridPlacement.Lattice;
import ar.edu.itba.sds.tp4.engine.GridPlacement.Placed;
import ar.edu.itba.sds.tp4.engine.cim.CellIndexMethod;
import ar.edu.itba.sds.tp4.engine.cim.NeighborFinder;
import ar.edu.itba.sds.tp4.engine.cim.Particle;
import ar.edu.itba.sds.tp4.models.BilliardConfig;
import java.io.IOException;
import java.util.List;

/**
 * Sistema 2 con Verlet original (Teórica 4, diapo 13): r(t+Δt) = 2r(t) − r(t−Δt) + (Δt²/m)·f(t).
 * El estado se entrega cada n = dt2/dt pasos (contador entero), con t = 0 incluido.
 */
public final class BilliardSimulator {
    /** Separación extra entre sitios de la grilla (D5): s = 2r + 0,1 mm. */
    public static final double GRID_GAP = 1e-4;

    /**
     * Estado en t = step·dt. Los arreglos son del simulador y se reutilizan: leerlos dentro de la llamada.
     * v es la velocidad central (diapo 13): v(t) = [r(t+Δt) − r(t−Δt)] / (2Δt).
     */
    public record Frame(long step, double time, double[] x, double[] y, double[] vx, double[] vy, boolean[] used,
                        int usedCount, double kineticEnergy, double elasticEnergy) {
        public double totalEnergy() { return kineticEnergy + elasticEnergy; }
    }

    @FunctionalInterface
    public interface Observer { void onFrame(Frame frame) throws IOException; }

    /** COMPLETED: llegó a tf. DIVERGED: en t una partícula quedó fuera de |r| ≤ R. ALL_USED: Nu = N en el cuadro t (--until t100). */
    public enum Status { COMPLETED, DIVERGED, ALL_USED }

    public record Summary(Status status, long steps, double time, int usedCount) { }

    private final BilliardConfig c;
    private final ContactForces forces;
    private final double[] x0, y0, vx0, vy0;

    /** Estado inicial explícito (índice i = partícula i). */
    public BilliardSimulator(BilliardConfig c, double[] x, double[] y, double[] vx, double[] vy, NeighborFinder finder) {
        if (x.length != c.n() || y.length != c.n() || vx.length != c.n() || vy.length != c.n())
            throw new IllegalArgumentException("El estado inicial debe tener N = " + c.n() + " partículas");
        this.c = c;
        this.forces = new ContactForces(c, finder);
        this.x0 = x.clone(); this.y0 = y.clone(); this.vx0 = vx.clone(); this.vy0 = vy.clone();
    }

    /** Condición inicial por grilla única (D5): red hexagonal, sitio en el origen, s = 2r + GRID_GAP, sorteo con la semilla. */
    public static BilliardSimulator fromGrid(BilliardConfig c, NeighborFinder finder) {
        List<Particle> obstacles = c.hasObstacles() ? GridPlacement.obstacles(c.x0(), c.radius()) : List.of();
        List<Placed> placed = GridPlacement.place(GridPlacement.sites(Lattice.HEX, Anchor.SITE_AT_ORIGIN,
                2 * c.radius() + GRID_GAP, c.domainRadius(), c.radius(), obstacles), c.n(), c.seed(), c.speed());
        int n = c.n();
        double[] x = new double[n], y = new double[n], vx = new double[n], vy = new double[n];
        for (int i = 0; i < n; i++) {
            Placed p = placed.get(i);
            x[i] = p.x(); y[i] = p.y(); vx[i] = p.vx(); vy[i] = p.vy();
        }
        return new BilliardSimulator(c, x, y, vx, vy, finder);
    }

    /** CIM de TP1 en el círculo con el M más grande válido (L = 2R, rc = 0). */
    public static NeighborFinder defaultFinder(BilliardConfig c) {
        return CellIndexMethod.forCircle(CellIndexMethod.maxValidM(2 * c.domainRadius(), 0, c.radius()), c.domainRadius());
    }

    public Summary run(Observer observer) throws IOException { return run(observer, false); }

    /** Con stopWhenAllUsed corta en el primer cuadro (múltiplo de dt2) con Nu = N, para t100 en 2.2. */
    public Summary run(Observer observer, boolean stopWhenAllUsed) throws IOException {
        int n = c.n(), every = c.outputEvery();
        long total = c.totalSteps();
        double dt = c.dt(), m = c.mass(), big = c.domainRadius();
        double[] x = x0.clone(), y = y0.clone();
        double[] xPrev = new double[n], yPrev = new double[n], xNext = new double[n], yNext = new double[n];
        double[] fx = new double[n], fy = new double[n], vx = new double[n], vy = new double[n];
        boolean[] used = new boolean[n];
        int usedCount = 0;

        if (outside(x, y, big) >= 0) throw new IllegalArgumentException("Hay partículas iniciales fuera del dominio");
        ContactForces.Result contacts = forces.compute(x, y, fx, fy, used);
        usedCount += contacts.newlyUsed();
        // r(−Δt) por Euler evaluado en −Δt (diapo 14). Con la grilla F(0) = 0 y el paso es exacto
        for (int i = 0; i < n; i++) {
            xPrev[i] = x[i] - dt * vx0[i] + dt * dt * fx[i] / (2 * m);
            yPrev[i] = y[i] - dt * vy0[i] + dt * dt * fy[i] / (2 * m);
        }

        for (long step = 0; ; step++) {
            for (int i = 0; i < n; i++) {
                xNext[i] = 2 * x[i] - xPrev[i] + dt * dt * fx[i] / m;
                yNext[i] = 2 * y[i] - yPrev[i] + dt * dt * fy[i] / m;
            }
            if (step % every == 0) {
                double kinetic = 0;
                for (int i = 0; i < n; i++) {
                    vx[i] = (xNext[i] - xPrev[i]) / (2 * dt);
                    vy[i] = (yNext[i] - yPrev[i]) / (2 * dt);
                    kinetic += 0.5 * m * (vx[i] * vx[i] + vy[i] * vy[i]);
                }
                observer.onFrame(new Frame(step, step * dt, x, y, vx, vy, used, usedCount, kinetic, contacts.elasticEnergy()));
                if (stopWhenAllUsed && usedCount == n) return new Summary(Status.ALL_USED, step, step * dt, usedCount);
            }
            if (step == total) return new Summary(Status.COMPLETED, step, step * dt, usedCount);

            double[] t = xPrev; xPrev = x; x = xNext; xNext = t;
            t = yPrev; yPrev = y; y = yNext; yNext = t;
            // Un dt inestable saca partículas del círculo: se corta la corrida y se informa, sin excepción
            if (outside(x, y, big) >= 0) return new Summary(Status.DIVERGED, step + 1, (step + 1) * dt, usedCount);
            contacts = forces.compute(x, y, fx, fy, used);
            usedCount += contacts.newlyUsed();
        }
    }

    /** Índice de la primera partícula con |r| > R (o no finita), o −1. */
    private static int outside(double[] x, double[] y, double big) {
        // Misma cuenta que la validación del CIM, para que nunca la dispare
        for (int i = 0; i < x.length; i++) if (!(Math.hypot(x[i], y[i]) <= big)) return i;
        return -1;
    }
}
