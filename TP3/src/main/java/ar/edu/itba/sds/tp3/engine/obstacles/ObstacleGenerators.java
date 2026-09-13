package ar.edu.itba.sds.tp3.engine.obstacles;

/** Único registro de nombres usados desde la línea de comandos. */
public final class ObstacleGenerators {
    private ObstacleGenerators() { }
    public static ObstacleGenerator create(String name, int count, double radius) {
        return switch (name) {
            case "random" -> new RandomObstacleGenerator(count, radius);
            case "none" -> new EmptyObstacleGenerator();
            default -> throw new IllegalArgumentException("Algoritmo de obstáculos desconocido: " + name + " (disponibles: random, none)");
        };
    }
}
