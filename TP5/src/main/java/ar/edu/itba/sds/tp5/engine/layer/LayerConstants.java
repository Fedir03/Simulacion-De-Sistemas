package ar.edu.itba.sds.tp5.engine.layer;

/**
 * Constantes de las capas (D10): se declaran, no se calibran.
 *
 * @param rho          ρ, espacio personal (m)
 * @param sideEpsilon  ε de la regla de lado (m): |s_c| ≤ ε es desempate, en A, B y F
 * @param frontalAngle rotación de e_ij en el desempate de F (rad)
 * @param frontalTie   cuándo hay desempate en F
 * @param fHorizon     horizonte de la detección en F (s). La especificación no le da: es infinito salvo para medir la sensibilidad
 * @param fGated       si F pide choque predicho. Sin compuerta (variantes F1 y F3) alcanza con que el otro esté en el semiplano
 * @param fGap         lo que se le resta a d_ij en la exponencial de F, sin bajar de 0: 0 entre centros, 2R entre bordes (variantes F2 y F3)
 */
public record LayerConstants(double rho, double sideEpsilon, double frontalAngle, FrontalTie frontalTie, double fHorizon, boolean fGated, double fGap) {
    public static final double DEFAULT_RHO = 0.9;
    public static final double DEFAULT_FRONTAL_DEGREES = 5;

    /** Criterio de desempate de F. */
    public enum FrontalTie {
        /** Vigente: |s_c| ≤ ε, el mismo criterio métrico que A y B. */
        METRIC,
        /** Versión original de la especificación: |sin θ_j| ≤ frontalAngle. Solo para regenerar la comparación del piloto. */
        ANGULAR
    }

    public static LayerConstants defaults() { return of(DEFAULT_RHO, DEFAULT_FRONTAL_DEGREES, FrontalTie.METRIC); }

    public static LayerConstants of(double rho, double frontalDegrees, FrontalTie frontalTie) {
        return new LayerConstants(rho, 0.05, Math.toRadians(frontalDegrees), frontalTie, Double.POSITIVE_INFINITY, true, 0);
    }

    public LayerConstants withFHorizon(double horizon) {
        return new LayerConstants(rho, sideEpsilon, frontalAngle, frontalTie, horizon, fGated, fGap);
    }

    public LayerConstants withFVariant(boolean gated, double gap) {
        return new LayerConstants(rho, sideEpsilon, frontalAngle, frontalTie, fHorizon, gated, gap);
    }

    public LayerConstants {
        if (!(rho > 0 && sideEpsilon >= 0 && frontalAngle >= 0 && fHorizon > 0 && fGap >= 0) || frontalTie == null)
            throw new IllegalArgumentException("Constantes de capa inválidas");
    }
}
