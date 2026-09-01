package ar.edu.itba.sds.tp2.analysis;

import ar.edu.itba.sds.tp2.engine.VicsekParticle;

import java.util.List;

/** Un bloque de tiempo de la corrida: el paso y el estado de todas las particulas. */
public record Frame(int step, List<VicsekParticle> particles) {}
