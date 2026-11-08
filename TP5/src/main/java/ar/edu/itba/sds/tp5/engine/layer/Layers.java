package ar.edu.itba.sds.tp5.engine.layer;

import java.util.Locale;

/** Elige la capa por nombre: el módulo es intercambiable sin tocar el simulador. */
public final class Layers {
    private Layers() { }

    /** Parámetros: A (t_a, ℓ), B (t_a, k), F (A_p, B_p). Con "none" se ignoran. */
    public static AvoidanceLayer of(String name, double p1, double p2, LayerConstants constants) {
        return switch (name.strip().toLowerCase(Locale.ROOT)) {
            case "none" -> AvoidanceLayer.NONE;
            case "a" -> LateralTargetLayer.a(p1, p2, constants);
            case "b" -> LateralTargetLayer.b(p1, p2, constants);
            case "f" -> new RepulsiveDirectionLayer(p1, p2, constants);
            default -> throw new IllegalArgumentException("Capa desconocida: " + name);
        };
    }
}
