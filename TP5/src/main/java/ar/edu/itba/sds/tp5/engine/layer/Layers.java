package ar.edu.itba.sds.tp5.engine.layer;

import java.util.Locale;

/** Elige la capa por nombre: el módulo es intercambiable sin tocar el simulador. */
public final class Layers {
    private Layers() { }

    /** Parámetros: A (t_a, ℓ), B (t_a, k), F (A_p, B_p), E (a, b). Con "none" se ignoran. */
    public static AvoidanceLayer of(String name, double p1, double p2, LayerConstants constants) {
        return switch (name.strip().toLowerCase(Locale.ROOT)) {
            case "none" -> AvoidanceLayer.NONE;
            case "a" -> LateralTargetLayer.a(p1, p2, constants);
            case "b" -> LateralTargetLayer.b(p1, p2, constants);
            case "f" -> new RepulsiveDirectionLayer(p1, p2, constants);
            case "e" -> new EggLayer(p1, p2);
            default -> throw new IllegalArgumentException("Capa desconocida: " + name);
        };
    }

    /**
     * Calibración individual opcional, con parámetros por peatón: el peatón 1 usa (p1, p2) y el 2, (p1', p2'). En E
     * cada uno lleva su propio huevo y ve el del otro; en las demás, cada uno tiene su capa.
     */
    public static AvoidanceLayer perPedestrian(String name, double p1, double p2, double p1Second, double p2Second, LayerConstants constants) {
        if (name.strip().equalsIgnoreCase("e")) return EggLayer.perPedestrian(p1, p2, p1Second, p2Second);
        AvoidanceLayer first = of(name, p1, p2, constants), second = of(name, p1Second, p2Second, constants);
        if (first == AvoidanceLayer.NONE) return AvoidanceLayer.NONE;
        return new AvoidanceLayer() {
            @Override public boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                               double vd, double ex, double ey, double[] out) {
                throw new IllegalStateException("Con parámetros por peatón se usa a través de forAgent");
            }
            @Override public AvoidanceLayer forAgent(int agent) { return agent == 0 ? first : second; }
            @Override public String label() { return first.label() + " | peaton2: " + second.label(); }
        };
    }
}
