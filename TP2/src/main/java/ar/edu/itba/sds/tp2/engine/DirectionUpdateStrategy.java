package ar.edu.itba.sds.tp2.engine;

import java.util.List;
import java.util.Random;

/** Estrategia intercambiable para calcular el nuevo ángulo de una partícula (estándar vs votante), mismo patrón que NeighborFinder en TP1. */
public interface DirectionUpdateStrategy {
    double nextAngle(VicsekParticle self, List<VicsekParticle> neighbors, double eta, Random random);
}