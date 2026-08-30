package ar.edu.itba.sds.tp2.engine;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** Genera la condición inicial de una simulación de Vicsek: posiciones uniformes al azar y ángulo random o fijo. */
public final class InitialConditionGenerator {

    private InitialConditionGenerator() {
    }

    /** Condición inicial clásica: posiciones y ángulos uniformes al azar. */
    public static List<VicsekParticle> generate(int n, double l, Random random) {
        return generate(n, l, random, null);
    }

    /**
     * Igual que {@link #generate(int, double, Random)}, pero si {@code theta0} no es null todas las
     * partículas arrancan con ese ángulo (en radianes) en vez de uno al azar.
     *
     * <p>El ángulo al azar se consume del stream igual aunque después se descarte: así, para una
     * misma semilla, las posiciones iniciales son idénticas con ángulos random y con ángulo fijo.
     * Eso es lo que permite comparar las dos condiciones iniciales sobre el mismo estado de partida.
     */
    public static List<VicsekParticle> generate(int n, double l, Random random, Double theta0) {
        List<VicsekParticle> particles = new ArrayList<>(n);
        for (int id = 1; id <= n; id++) {
            double x = random.nextDouble() * l;
            double y = random.nextDouble() * l;
            double randomTheta = random.nextDouble() * 2 * Math.PI;
            double theta = theta0 == null ? randomTheta : theta0;
            particles.add(new VicsekParticle(id, x, y, theta));
        }
        return particles;
    }
}
