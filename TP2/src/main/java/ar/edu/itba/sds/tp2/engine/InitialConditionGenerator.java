package ar.edu.itba.sds.tp2.engine;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** Genera la condición inicial de una simulación de Vicsek: posición y ángulo uniformes al azar. */
public final class InitialConditionGenerator {

    private InitialConditionGenerator() {
    }

    public static List<VicsekParticle> generate(int n, double l, Random random) {
        List<VicsekParticle> particles = new ArrayList<>(n);
        for (int id = 1; id <= n; id++) {
            double x = random.nextDouble() * l;
            double y = random.nextDouble() * l;
            double theta = random.nextDouble() * 2 * Math.PI;
            particles.add(new VicsekParticle(id, x, y, theta));
        }
        return particles;
    }
}