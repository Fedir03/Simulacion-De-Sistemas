package ar.edu.itba.sds.tp5.data;

import java.util.Arrays;

/** Trayectoria experimental de un peatón: frames estrictamente crecientes, con posibles huecos. */
public record Trajectory(int id, int[] frames, double[] x, double[] y) {

    public Trajectory {
        if (frames.length < 2 || x.length != frames.length || y.length != frames.length)
            throw new IllegalArgumentException("Trayectoria inválida del ID " + id);
        for (int k = 1; k < frames.length; k++)
            if (frames[k] <= frames[k - 1]) throw new IllegalArgumentException("Frames desordenados en el ID " + id);
    }

    public int firstFrame() { return frames[0]; }
    public int lastFrame() { return frames[frames.length - 1]; }
    public int size() { return frames.length; }

    /** Índice del frame, o negativo si es un hueco. */
    public int indexOf(int frame) { return Arrays.binarySearch(frames, frame); }

    /** Cantidad de frames faltantes entre el primero y el último. */
    public int missingFrames() { return lastFrame() - firstFrame() + 1 - size(); }

    public double targetX() { return x[size() - 1]; }
    public double targetY() { return y[size() - 1]; }

    /** v_d: longitud recorrida sobre duración. Un hueco cuenta como la cuerda entre sus extremos. */
    public double meanSpeed(double dtExp) {
        return meanSpeed(firstFrame(), lastFrame(), dtExp);
    }

    /** v_d entre dos frames presentes de la trayectoria. */
    public double meanSpeed(int fromFrame, int toFrame, double dtExp) {
        int a = indexOf(fromFrame), b = indexOf(toFrame);
        if (a < 0 || b <= a) throw new IllegalArgumentException("Tramo inválido del ID " + id + ": " + fromFrame + "-" + toFrame);
        double length = 0;
        for (int k = a + 1; k <= b; k++) length += Math.hypot(x[k] - x[k - 1], y[k] - y[k - 1]);
        return length / ((toFrame - fromFrame) * dtExp);
    }

    /**
     * Velocidad inicial (D12): pendiente del ajuste lineal por mínimos cuadrados sobre los primeros
     * {@code count} frames disponibles desde {@code startFrame}, con sus tiempos reales.
     *
     * @return {vx, vy}
     */
    public double[] fittedVelocity(int startFrame, int count, double dtExp) {
        if (count < 2) throw new IllegalArgumentException("El ajuste de v0 necesita al menos 2 frames");
        int start = indexOf(startFrame);
        if (start < 0) throw new IllegalArgumentException("El ID " + id + " no tiene el frame " + startFrame);
        int end = start + count;
        if (end > size()) throw new IllegalArgumentException("El ID " + id + " no tiene " + count + " frames desde " + startFrame);
        double meanT = 0, meanX = 0, meanY = 0;
        for (int k = start; k < end; k++) {
            meanT += (frames[k] - startFrame) * dtExp;
            meanX += x[k];
            meanY += y[k];
        }
        meanT /= count; meanX /= count; meanY /= count;
        double stt = 0, stx = 0, sty = 0;
        for (int k = start; k < end; k++) {
            double t = (frames[k] - startFrame) * dtExp - meanT;
            stt += t * t;
            stx += t * (x[k] - meanX);
            sty += t * (y[k] - meanY);
        }
        return new double[] { stx / stt, sty / stt };
    }
}
