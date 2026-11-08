package ar.edu.itba.sds.tp5.data;

/**
 * Un evento del LEEME. Índice 0 = peatón que sale por la izquierda, 1 = por la derecha.
 * La ventana común (D3) va del primer al último frame presente en los dos peatones.
 */
public record PedestrianEvent(int number, Trajectory left, Trajectory right, double dtExp, double leemeMinDistance,
                              int firstFrame, int lastFrame) {

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
