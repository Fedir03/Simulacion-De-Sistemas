package ar.edu.itba.sds.tp5.engine.layer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.engine.Agent;
import ar.edu.itba.sds.tp5.engine.Integrator;
import ar.edu.itba.sds.tp5.engine.SfmParameters;
import ar.edu.itba.sds.tp5.engine.Simulation;
import java.util.List;
import org.junit.jupiter.api.Test;

class EggLayerTest {
    private static final double A = 1.0, B = 0.35;
    private final EggLayer layer = new EggLayer(A, B);

    @Test void separationMatchesTheEggGeometry() {
        double[] n = new double[2];
        // Lado a lado, los dos hacia +x: se separan 2b
        assertEquals(0.1, layer.separation(0, 2 * B + 0.1, 0, 0, n), 2e-3);
        assertEquals(1, n[1], 1e-9);
        // Punta contra punta: se tocan a 2a
        assertEquals(0.2, layer.separation(-2 * A - 0.2, 0, 0, Math.PI, n), 2e-3);
        // Punta de i contra la parte trasera de j, que camina delante: a + b
        assertEquals(-0.1, layer.separation(-(A + B) + 0.1, 0, 0, 0, n), 2e-3);
    }

    @Test void separatedEggsKeepTheTargetEvenOnACollisionCourse() {
        double[] out = new double[2];
        // De frente a 2,2 m: los huevos (punta a 1 m) todavía no se tocan, así que no hay desvío
        assertFalse(layer.directionWithVelocity(0, 0, 1.3, 0, 2.2, 0, -1.3, 0, 1.3, 1, 0, out));
        assertEquals(1, out[0], 0);
        assertEquals(0, out[1], 0);
        assertFalse(layer.directionWithVelocity(0, 0, 1.3, 0, -3, 0, -1.3, 0, 1.3, 1, 0, out));
    }

    @Test void touchingEggsSlideAlongTheContact() {
        double[] out = new double[2];
        // Punta contra punta apenas metidas y corridas: e_target queda casi tangente, del lado opuesto al otro
        assertTrue(layer.directionWithVelocity(0, 0, 1.3, 0, 1.6, 0.3, -1.3, 0, 1.3, 1, 0, out));
        assertTrue(out[1] < 0, "el otro está arriba: se desliza hacia abajo");
        assertEquals(1, Math.hypot(out[0], out[1]), 1e-12);
    }

    @Test void exactHeadOnContactGoesRight() {
        double[] out = new double[2];
        assertTrue(layer.directionWithVelocity(0, 0, 1.3, 0, 1.99, 0, -1.3, 0, 1.3, 1, 0, out));
        assertTrue(out[1] < 0, "a la derecha de +x es −y");
    }

    @Test void deeperOverlapTurnsFurtherAway() {
        double[] shallow = new double[2], deep = new double[2];
        assertTrue(layer.directionWithVelocity(0, 0, 1.3, 0, 1.6, 0.3, -1.3, 0, 1.3, 1, 0, shallow));
        assertTrue(layer.directionWithVelocity(0, 0, 1.3, 0, 1.2, 0.3, -1.3, 0, 1.3, 1, 0, deep));
        assertTrue(deep[0] * 1.2 + deep[1] * 0.3 < 0, "se aleja del otro");
        assertTrue(Math.atan2(-deep[1], deep[0]) > Math.atan2(-shallow[1], shallow[0]), "más solape, más giro");
    }

    @Test void perPedestrianEggsSeeTheSameContact() {
        AvoidanceLayer pair = EggLayer.perPedestrian(1.0, 0.35, 3.0, 0.3);
        EggLayer first = (EggLayer) pair.forAgent(0), second = (EggLayer) pair.forAgent(1);
        double[] n = new double[2];
        for (double[] c : new double[][] { { -2.5, 0.4, 0.3, 3.0 }, { -1.2, -0.5, 0, Math.PI }, { 3, 1, 2, -1 } })
            assertEquals(first.separation(c[0], c[1], c[2], c[3], n), second.separation(-c[0], -c[1], c[3], c[2], n), 1e-9);
    }

    @Test void equalParametersPerPedestrianReproduceTheSharedLayer() {
        Agent[] agents = { new Agent(0, 0, 1.3, 0, 10, 0.1, 1.3), new Agent(10, 0.2, -1.2, 0, 0, 0.2, 1.2) };
        for (String name : List.of("a", "b", "f", "e")) {
            double p1 = name.equals("f") ? 0.5 : 3, p2 = name.equals("f") ? 2 : 0.5;
            List<double[]> shared = run(Layers.of(name, p1, p2, LayerConstants.defaults()), agents);
            List<double[]> perPedestrian = run(Layers.perPedestrian(name, p1, p2, p1, p2, LayerConstants.defaults()), agents);
            assertEquals(shared.size(), perPedestrian.size(), name);
            for (int k = 0; k < shared.size(); k++) org.junit.jupiter.api.Assertions.assertArrayEquals(shared.get(k), perPedestrian.get(k), name);
        }
    }

    private static List<double[]> run(AvoidanceLayer layer, Agent[] agents) {
        return new Simulation(SfmParameters.defaults(), Integrator.BEEMAN, 64, layer).run(agents, 1 / 15.0, 120).rows();
    }
}
