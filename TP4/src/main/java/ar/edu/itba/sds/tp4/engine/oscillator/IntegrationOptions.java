package ar.edu.itba.sds.tp4.engine.oscillator;

import java.util.Locale;

/**
 * Cómo se resuelve la dependencia de la fuerza con la velocidad (f = −k·x − γ·v) en cada esquema.
 * Los valores por defecto son los acordados por el grupo (DEFINICIONES.md, D17).
 */
public record IntegrationOptions(VerletVelocity verletVelocity, PredictedVelocity velocityVerletPrediction,
                                 AccelerationUpdate accelerationUpdate) {

    /** Velocidad v(t) con la que Verlet original evalúa f(t), antes de conocer r(t+Δt). */
    public enum VerletVelocity {
        /** v(t) ≈ [r(t) − r(t−Δt)] / Δt. */
        BACKWARD,
        /** v(t) ≈ v(t−Δt) + a(t−Δt)·Δt, con v(t−Δt) por diferencia central. */
        EULER
    }

    /** Velocidad predicha con la que Velocity Verlet evalúa f(t+Δt). */
    public enum PredictedVelocity {
        /** v(t) + a(t)·Δt. */
        EULER,
        /** v(t+Δt/2) = v(t) + a(t)·Δt/2. */
        HALF_STEP
    }

    /** Aceleración a(t+Δt) que Beeman y Velocity Verlet arrastran al paso siguiente. */
    public enum AccelerationUpdate {
        /** La evaluada con la velocidad predicha (diapos 17 y 20, una evaluación de fuerza por paso). */
        PREDICTED,
        /** Se re-evalúa con la velocidad ya corregida (dos evaluaciones por paso). */
        CORRECTED
    }

    public static IntegrationOptions defaults() {
        return new IntegrationOptions(VerletVelocity.BACKWARD, PredictedVelocity.EULER, AccelerationUpdate.PREDICTED);
    }

    public IntegrationOptions {
        if (verletVelocity == null || velocityVerletPrediction == null || accelerationUpdate == null)
            throw new IllegalArgumentException("Opciones de integración incompletas");
    }

    /** Convierte "half-step" en HALF_STEP, para leer las opciones desde la línea de comandos. */
    public static <E extends Enum<E>> E parse(Class<E> type, String value) {
        try { return Enum.valueOf(type, value.trim().toUpperCase(Locale.ROOT).replace('-', '_')); }
        catch (IllegalArgumentException e) { throw new IllegalArgumentException("Valor inválido para " + type.getSimpleName() + ": " + value); }
    }

    public String describe() {
        return "verletVelocity=" + verletVelocity + " velocityVerletPrediction=" + velocityVerletPrediction
                + " accelerationUpdate=" + accelerationUpdate;
    }
}
