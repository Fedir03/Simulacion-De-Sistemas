package ar.edu.itba.sds.tp2.engine;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Modelo estándar: nuevo ángulo = promedio vectorial de los ángulos de los vecinos (+ ruido).
 *
 * <p>{@code includeSelf} controla si el promedio incluye el ángulo propio de la partícula
 * además del de sus vecinos. La cátedra confirmó que sí se incluye — por eso
 * {@code SimulateCommand.resolveStrategy} instancia esta clase con {@code includeSelf=true}.
 */
public final class StandardModel implements DirectionUpdateStrategy {
    private final boolean includeSelf;

    public StandardModel(boolean includeSelf) {
        this.includeSelf = includeSelf;
    }

    @Override
    public double nextAngle(VicsekParticle self, List<VicsekParticle> neighbors, double eta, Random random) {
        List<Double> thetas = new ArrayList<>(neighbors.size() + 1);
        if (includeSelf) {
            thetas.add(self.theta());
        }
        for (VicsekParticle neighbor : neighbors) {
            thetas.add(neighbor.theta());
        }

        if (thetas.isEmpty()) {
            return AngleMath.addNoise(self.theta(), eta, random);
        }
        double average = AngleMath.vectorialAverage(thetas);
        return AngleMath.addNoise(average, eta, random);
    }
}