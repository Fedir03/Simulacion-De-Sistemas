package ar.edu.itba.sds.tp5.engine;

/**
 * Parámetros del SFM sin fuerza social (DEFINICIONES.md, D5) y radio de llegada δ_a (D13).
 *
 * @param mass   m (kg)
 * @param tau    τ (s)
 * @param kn     k_n (N/m)
 * @param kt     k_t (kg/m/s)
 * @param radius r (m)
 * @param deltaA δ_a (m): el peatón se retira a esta distancia de su target
 */
public record SfmParameters(double mass, double tau, double kn, double kt, double radius, double deltaA) {
    public static final double DEFAULT_DELTA_A = 0.1;

    public SfmParameters {
        if (!(mass > 0 && tau > 0 && kn >= 0 && kt >= 0 && radius > 0 && deltaA > 0))
            throw new IllegalArgumentException("Parámetros del SFM inválidos");
    }

    public static SfmParameters defaults() { return withDeltaA(DEFAULT_DELTA_A); }

    public static SfmParameters withDeltaA(double deltaA) {
        return new SfmParameters(80, 0.5, 1.2e5, 2.4e5, 0.25, deltaA);
    }
}
