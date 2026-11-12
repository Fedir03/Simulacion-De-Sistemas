package ar.edu.itba.sds.tp5.data;

/**
 * Un evento del LEEME. Índice 0 = peatón que sale por la izquierda, 1 = por la derecha.
 * La ventana común (D3) va del primer al último frame presente en los dos peatones.
 *
 * <p>Las trayectorias son siempre las completas del evento. El target de cada peatón es su posición en
 * {@code targetFrame[i]} y v_d su rapidez media entre {@code speedFrom[i]} y ese frame. Sin recorte son el primer y el
 * último frame de su trayectoria (D3); con recorte los fija {@link FrontalTrim}. Guardar la trayectoria entera hace que
 * el rumbo de los frames del borde se calcule igual al recortar de nuevo, y el recorte sea idempotente.
 */
public record PedestrianEvent(int number, Trajectory left, Trajectory right, double dtExp, double leemeMinDistance,
                              int firstFrame, int lastFrame, int[] speedFrom, int[] targetFrame) {

    public PedestrianEvent {
        for (int i = 0; i < 2; i++) {
            Trajectory t = i == 0 ? left : right;
            if (t.indexOf(targetFrame[i]) < 0 || t.indexOf(speedFrom[i]) < 0 || speedFrom[i] >= targetFrame[i])
                throw new IllegalArgumentException("Target o v_d fuera de la trayectoria del ID " + t.id());
        }
    }

    /** Sin recorte: target en el último frame de cada trayectoria y v_d sobre la trayectoria entera (D3). */
    public PedestrianEvent(int number, Trajectory left, Trajectory right, double dtExp, double leemeMinDistance, int firstFrame, int lastFrame) {
        this(number, left, right, dtExp, leemeMinDistance, firstFrame, lastFrame,
                new int[] { left.firstFrame(), right.firstFrame() }, new int[] { left.lastFrame(), right.lastFrame() });
    }

    public double targetX(int i) { Trajectory t = pedestrian(i); return t.x()[t.indexOf(targetFrame[i])]; }
    public double targetY(int i) { Trajectory t = pedestrian(i); return t.y()[t.indexOf(targetFrame[i])]; }
    public double desiredSpeed(int i) { return pedestrian(i).meanSpeed(speedFrom[i], targetFrame[i], dtExp); }

    public static PedestrianEvent of(int number, Trajectory left, Trajectory right, double dtExp, double leemeMinDistance) {
        int first = Math.max(left.firstFrame(), right.firstFrame());
        int last = Math.min(left.lastFrame(), right.lastFrame());
        while (first <= last && (left.indexOf(first) < 0 || right.indexOf(first) < 0)) first++;
        while (last >= first && (left.indexOf(last) < 0 || right.indexOf(last) < 0)) last--;
        if (first >= last) throw new IllegalArgumentException("El evento " + number + " no tiene ventana común");
        return new PedestrianEvent(number, left, right, dtExp, leemeMinDistance, first, last);
    }

    public Trajectory pedestrian(int i) { return i == 0 ? left : right; }

    /** Duración de la ventana común, en intervalos experimentales. */
    public int windowIntervals() { return lastFrame - firstFrame; }

    /** Frames de la ventana común con posición de los dos peatones. */
    public int commonFramesAvailable() {
        int count = 0;
        for (int f = firstFrame; f <= lastFrame; f++) if (left.indexOf(f) >= 0 && right.indexOf(f) >= 0) count++;
        return count;
    }

    /** Distancia mínima entre centros en los frames comunes, y el frame en que ocurre. */
    public MinDistance minDistance() {
        double best = Double.POSITIVE_INFINITY;
        int at = firstFrame;
        for (int f = firstFrame; f <= lastFrame; f++) {
            int a = left.indexOf(f), b = right.indexOf(f);
            if (a < 0 || b < 0) continue;
            double d = Math.hypot(left.x()[a] - right.x()[b], left.y()[a] - right.y()[b]);
            if (d < best) { best = d; at = f; }
        }
        return new MinDistance(best, at);
    }

    public record MinDistance(double distance, int frame) { }
}
