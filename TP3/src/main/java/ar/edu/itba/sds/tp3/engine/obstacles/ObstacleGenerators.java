package ar.edu.itba.sds.tp3.engine.obstacles;

import java.util.*;

/** Único registro de nombres usados desde la línea de comandos.
 * Los parámetros llegan sin el prefijo --obstacle-; cada algoritmo rechaza los que no utiliza.
 */
public final class ObstacleGenerators {
    public static final List<String> NAMES = List.of("random", "none", "single", "funnel", "semicircle", "posts", "lattice", "ellipse");

    private ObstacleGenerators() { }

    public static ObstacleGenerator create(String name, Map<String, String> params) {
        Set<String> accepted = switch (name) {
            case "random" -> Set.of("count", "radius", "seed");
            case "none" -> Set.of();
            case "single" -> Set.of("x", "y", "radius");
            case "funnel" -> Set.of("funnel-length", "edge-radius", "max-radius", "grid");
            case "semicircle" -> Set.of("free-radius", "center-offset", "edge-radius", "goals", "max-radius", "grid");
            case "posts" -> Set.of("radius");
            case "lattice" -> Set.of("spacing", "radius");
            case "ellipse" -> Set.of("focus-x", "edge-radius", "focus-shape", "focus-size", "lens-width", "max-radius", "grid");
            default -> throw new IllegalArgumentException("Algoritmo de obstáculos desconocido: " + name + " (disponibles: " + String.join(", ", NAMES) + ")");
        };
        for (String key : params.keySet())
            if (!accepted.contains(key)) throw new IllegalArgumentException("El algoritmo " + name + " no utiliza --obstacle-" + key);
        return switch (name) {
            case "random" -> new RandomObstacleGenerator(Integer.parseInt(params.getOrDefault("count", "2")), number(params, "radius", "0.05"));
            case "single" -> new SingleObstacleGenerator(number(params, "x", "NaN"), number(params, "y", "NaN"), number(params, "radius", "0.1"));
            case "funnel" -> new FunnelObstacleGenerator(number(params, "funnel-length", "0.3"), number(params, "edge-radius", "NaN"),
                    number(params, "max-radius", "Infinity"), number(params, "grid", "0.001"));
            case "semicircle" -> new SemicircleObstacleGenerator(number(params, "free-radius", "0.36"), number(params, "center-offset", "0"),
                    number(params, "edge-radius", "NaN"), goals(params),
                    number(params, "max-radius", "Infinity"), number(params, "grid", "0.001"));
            case "posts" -> new PostsObstacleGenerator(number(params, "radius", "0.05"));
            case "lattice" -> new LatticeObstacleGenerator(number(params, "spacing", "0.1"), number(params, "radius", "NaN"));
            case "ellipse" -> new EllipseObstacleGenerator(number(params, "focus-x", "0.3"), number(params, "edge-radius", "NaN"),
                    focusShape(params), number(params, "focus-size", "0.1"), number(params, "lens-width", "0.03"),
                    number(params, "max-radius", "Infinity"), number(params, "grid", "0.001"));
            default -> new EmptyObstacleGenerator();
        };
    }

    private static EllipseObstacleGenerator.FocusShape focusShape(Map<String, String> params) {
        String shape = params.getOrDefault("focus-shape", "none");
        return switch (shape) {
            case "none", "disc", "line", "lens" -> EllipseObstacleGenerator.FocusShape.valueOf(shape.toUpperCase(Locale.ROOT));
            default -> throw new IllegalArgumentException("--obstacle-focus-shape debe ser none, disc, line o lens");
        };
    }

    private static boolean goals(Map<String, String> params) {
        return switch (params.getOrDefault("goals", "right")) {
            case "right" -> false;
            case "both" -> true;
            default -> throw new IllegalArgumentException("--obstacle-goals debe ser right o both");
        };
    }

    private static double number(Map<String, String> params, String key, String fallback) {
        return Double.parseDouble(params.getOrDefault(key, fallback));
    }
}
