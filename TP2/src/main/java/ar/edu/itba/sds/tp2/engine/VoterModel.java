package ar.edu.itba.sds.tp2.engine;

import java.util.List;
import java.util.Random;

/** Modelo votante: copia el ángulo de un vecino elegido al azar (o solo ruido si no hay vecinos). */
public final class VoterModel implements DirectionUpdateStrategy {

    /**
     * {@code neighbors} nunca debería contener a {@code self} — eso ya está
     * garantizado por contrato de {@code NeighborFinder} de TP1 (nunca compara
     * una partícula contra sí misma al buscar vecinos), así que este método no
     * filtra nada por su cuenta.
     */
    @Override
    public double nextAngle(VicsekParticle self, List<VicsekParticle> neighbors, double eta, Random random) {
        if (neighbors.isEmpty()) {
            return AngleMath.addNoise(self.theta(), eta, random);
        }
        VicsekParticle chosen = neighbors.get(random.nextInt(neighbors.size()));
        return AngleMath.addNoise(chosen.theta(), eta, random);
    }
}