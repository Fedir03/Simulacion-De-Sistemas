package ar.edu.itba.sds.tp5.engine.layer;

/**
 * Capa de elusión: solo decide la dirección e_target de la velocidad deseada. No tiene acceso a las fuerzas y no
 * guarda estado: la activación se recalcula en cada evaluación, así que vuelve sola al target final.
 */
public interface AvoidanceLayer {

    /** Sin capa: e_target = e_t siempre. */
    AvoidanceLayer NONE = new AvoidanceLayer() {
        @Override public boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                           double vd, double ex, double ey, double[] out) {
            out[0] = ex;
            out[1] = ey;
            return false;
        }
        @Override public String label() { return "capa=none"; }
    };

    /**
     * Escribe en {@code out} el versor e_target del agente i frente al agente j.
     *
     * @param vd       rapidez deseada de i
     * @param ex       versor e_t hacia el target final de i (x)
     * @param ey       versor e_t (y)
     * @return si la capa reemplazó el target final por uno temporal
     */
    boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                      double vd, double ex, double ey, double[] out);

    /** La capa que usa el agente {@code agent}. Por defecto es la misma para todos. */
    default AvoidanceLayer forAgent(int agent) { return this; }

    /** Capa y parámetros, para el encabezado de los archivos de salida. */
    String label();
}
