package ar.edu.itba.sds.tp3.engine;

public record SimulationConfig(double length, double width, double goalWidth,
                               double radius, double mass, double speed) {
    public static SimulationConfig defaults() {
        return new SimulationConfig(1.20, 0.68, 0.20, 0.0175, 0.025, 1.0);
    }
    public SimulationConfig {
        for (double v : new double[]{length, width, radius, mass})
            if (!Double.isFinite(v) || v <= 0) throw new IllegalArgumentException("Dimensiones, radio y masa deben ser positivos");
        if (!Double.isFinite(goalWidth) || goalWidth < 0 || goalWidth > width
                || !Double.isFinite(speed) || speed < 0 || 2 * radius >= Math.min(length, width))
            throw new IllegalArgumentException("Configuración inválida");
    }
}
