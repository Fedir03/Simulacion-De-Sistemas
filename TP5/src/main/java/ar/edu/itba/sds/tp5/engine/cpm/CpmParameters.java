package ar.edu.itba.sds.tp5.engine.cpm;

/**
 * Parámetros del CPM (Baglietto y Parisi, Phys. Rev. E 83, 056117, 2011). r_min y r_max son los del enunciado; β y τ, los
 * del paper. La rapidez máxima de cada agente es su v_d (rapidez media experimental) y la de escape, v_e = v_d.
 *
 * @param rMin   r_min (m), radio al que se contrae en contacto
 * @param rMax   r_max (m), radio de un agente libre
 * @param beta   β, exponente de v_d(r) = v_d [(r − r_min)/(r_max − r_min)]^β
 * @param tau    τ (s): el radio crece Δr = r_max Δt/τ por paso
 * @param deltaA δ_a (m): el agente se retira a esta distancia de su target (D13, igual que en el SFM)
 */
public record CpmParameters(double rMin, double rMax, double beta, double tau, double deltaA) {

    public CpmParameters {
        if (!(rMin > 0 && rMax > rMin && beta > 0 && tau > 0 && deltaA > 0))
            throw new IllegalArgumentException("Parámetros del CPM inválidos");
    }

    public static CpmParameters withDeltaA(double deltaA) { return new CpmParameters(0.10, 0.25, 0.9, 0.5, deltaA); }

    /** v_d(r) = v_max [(r − r_min)/(r_max − r_min)]^β. */
    public double speed(double radius, double vMax) {
        double f = (radius - rMin) / (rMax - rMin);
        return f <= 0 ? 0 : vMax * Math.pow(Math.min(f, 1), beta);
    }

    /** Inversa de {@link #speed}: el radio con el que un agente de rapidez máxima vMax camina a {@code speed}, en [r_min, r_max]. */
    public double radiusFor(double speed, double vMax) {
        if (!(vMax > 0) || speed >= vMax) return rMax;
        return rMin + (rMax - rMin) * Math.pow(Math.max(speed, 0) / vMax, 1 / beta);
    }

    /** Δt = r_min / (2 v_max): el paso es una regla del modelo, no un parámetro numérico. */
    public double dt(double vMax) { return rMin / (2 * vMax); }

    public String label() {
        return "modelo=CPM r_min=" + rMin + " r_max=" + rMax + " beta=" + beta + " tau=" + tau + " dt=r_min/(2v_max)";
    }
}
