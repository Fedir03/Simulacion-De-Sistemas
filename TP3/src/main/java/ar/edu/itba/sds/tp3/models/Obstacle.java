package ar.edu.itba.sds.tp3.models;

/** Disco fijo de masa infinita. */
public record Obstacle(double x, double y, double radius) {
    public Obstacle {
        if (!Double.isFinite(x) || !Double.isFinite(y) || !Double.isFinite(radius) || radius <= 0)
            throw new IllegalArgumentException("Obstáculo inválido");
    }
}
