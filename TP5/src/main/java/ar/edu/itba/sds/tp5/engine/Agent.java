package ar.edu.itba.sds.tp5.engine;

import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.data.Trajectory;

/** Condición inicial, target final y rapidez deseada de un peatón. */
public record Agent(double x0, double y0, double vx0, double vy0, double targetX, double targetY, double desiredSpeed) {

    /** D3 y D12: arranca en el primer frame de la ventana; target y v_d según el evento (con o sin recorte). */
    public static Agent from(PedestrianEvent event, int i, int v0Frames) {
        Trajectory t = event.pedestrian(i);
        int start = t.indexOf(event.firstFrame());
        double[] v0 = t.fittedVelocity(event.firstFrame(), v0Frames, event.dtExp());
        return new Agent(t.x()[start], t.y()[start], v0[0], v0[1], event.targetX(i), event.targetY(i), event.desiredSpeed(i));
    }
}
