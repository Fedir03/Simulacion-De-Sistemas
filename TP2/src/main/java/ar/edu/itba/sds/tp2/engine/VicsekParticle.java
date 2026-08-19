package ar.edu.itba.sds.tp2.engine;

/** Partícula del modelo de Vicsek: posición + ángulo de dirección. Distinta de ar.edu.itba.sds.tp1.Particle a propósito. */
public record VicsekParticle(int id, double x, double y, double theta) {}