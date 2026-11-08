package ar.edu.itba.sds.tp5.engine;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** Prueba de D11: el integrador por defecto es el de menor error a Δt_exp/64 contra el peatón libre, y converge. */
class IntegratorTest {
    private static final int[] DIVS = { 16, 32, 64, 128 };

    @Test
    void defaultIntegratorHasTheLowestErrorAtTheChosenStep() {
        FreePedestrianCheck.Errors chosen = FreePedestrianCheck.measure(Integrator.DEFAULT, Simulation.DEFAULT_DT_DIV);
        for (Integrator other : Integrator.values()) {
            FreePedestrianCheck.Errors e = FreePedestrianCheck.measure(other, Simulation.DEFAULT_DT_DIV);
            assertTrue(chosen.position() <= e.position(), "posición contra " + other);
            assertTrue(chosen.velocity() <= e.velocity(), "velocidad contra " + other);
        }
    }

    @Test
    void bothIntegratorsConverge() {
        for (Integrator integrator : Integrator.values()) {
            double lastR = Double.POSITIVE_INFINITY, lastV = Double.POSITIVE_INFINITY;
            for (int div : DIVS) {
                FreePedestrianCheck.Errors e = FreePedestrianCheck.measure(integrator, div);
                // Cada duplicación tiene que reducir el error al menos a la mitad y un poco (orden ≥ 1)
                assertTrue(e.position() < 0.55 * lastR, integrator + " posición a /" + div);
                assertTrue(e.velocity() < 0.55 * lastV, integrator + " velocidad a /" + div);
                lastR = e.position();
                lastV = e.velocity();
            }
        }
    }

    @Test
    void firstVerletVelocityIsTheInitialOne() {
        Integrator.Field field = (r, v, a) -> a[0] = -2 * v[0] - r[0];
        assertEquals(0.7, Integrator.VERLET.start(field, 1e-3, new double[] { 1 }, new double[] { 0.7 }).velocity()[0], 1e-12);
        assertEquals(0.7, Integrator.BEEMAN.start(field, 1e-3, new double[] { 1 }, new double[] { 0.7 }).velocity()[0], 1e-12);
    }
}
