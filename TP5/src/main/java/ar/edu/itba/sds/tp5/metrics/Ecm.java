package ar.edu.itba.sds.tp5.metrics;

import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.data.Trajectory;
import ar.edu.itba.sds.tp5.engine.Simulation;

/**
 * ECM de un peatón contra su trayectoria simulada, sobre los t_k de la ventana común con posición experimental (D7).
 * <ul>
 *   <li>ECM 1 excluyendo: solo los t_k con posición simulada; N1 depende de cuándo llega el peatón.</li>
 *   <li>ECM 1 rellenando: después del retiro compara contra el target. Es solo una convención de la métrica (D13).</li>
 *   <li>ECM 2: cada punto experimental contra el punto más cercano de toda la trayectoria simulada.</li>
 * </ul>
 */
public final class Ecm {
    private Ecm() { }

    /**
     * @param ecm1Excluding ECM 1 sobre los N1 instantes con posición simulada
     * @param ecm1Filled    ECM 1 sobre los N2 instantes, con el target después del retiro
     * @param ecm2          ECM 2 sobre los N2 instantes
     * @param n1            instantes con posición experimental y simulada
     * @param n2            instantes con posición experimental
     */
    public record Pedestrian(double ecm1Excluding, double ecm1Filled, double ecm2, int n1, int n2) { }

    /** Métricas de un evento: promedio de sus peatones. */
    public record Event(Pedestrian[] pedestrians) {
        public double ecm1Excluding() { return (pedestrians[0].ecm1Excluding() + pedestrians[1].ecm1Excluding()) / 2; }
        public double ecm1Filled() { return (pedestrians[0].ecm1Filled() + pedestrians[1].ecm1Filled()) / 2; }
        public double ecm2() { return (pedestrians[0].ecm2() + pedestrians[1].ecm2()) / 2; }
    }

    public static Event of(PedestrianEvent event, Simulation.Result sim) {
        return new Event(new Pedestrian[] { of(event, sim, 0), of(event, sim, 1) });
    }

    public static Pedestrian of(PedestrianEvent event, Simulation.Result sim, int agent) {
        Trajectory exp = event.pedestrian(agent);
        double sum1 = 0, sumFilled = 0, sum2 = 0;
        int n1 = 0, n2 = 0;
        int rows = sim.rows().size();
        for (int k = 0; k < exp.size(); k++) {
            int frame = exp.frames()[k];
            if (frame < event.firstFrame() || frame > event.lastFrame()) continue;
            double ex = exp.x()[k], ey = exp.y()[k];
            n2++;
            double sx = sim.x(agent, (frame - event.firstFrame()) * Simulation.ROWS_PER_INTERVAL);
            double sy = sim.y(agent, (frame - event.firstFrame()) * Simulation.ROWS_PER_INTERVAL);
            if (Double.isNaN(sx)) {
                sumFilled += squared(ex - exp.targetX(), ey - exp.targetY());
            } else {
                double d = squared(ex - sx, ey - sy);
                sum1 += d;
                sumFilled += d;
                n1++;
            }
            double nearest = Double.POSITIVE_INFINITY;
            for (int r = 0; r < rows; r++) {
                double x = sim.x(agent, r);
                if (Double.isNaN(x)) break;     // no reaparece: el retiro es definitivo
                nearest = Math.min(nearest, squared(ex - x, ey - sim.y(agent, r)));
            }
            sum2 += nearest;
        }
        if (n2 == 0) throw new IllegalArgumentException("El evento " + event.number() + " no tiene instantes para el agente " + agent);
        return new Pedestrian(n1 == 0 ? Double.NaN : sum1 / n1, sumFilled / n2, sum2 / n2, n1, n2);
    }

    private static double squared(double dx, double dy) { return dx * dx + dy * dy; }
}
