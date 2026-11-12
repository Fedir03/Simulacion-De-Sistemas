package ar.edu.itba.sds.tp5.data;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Recorte al tramo frontal (DEFINICIONES, sección 8b). Criterio D(θ): frames comunes en que los dos peatones van a
 * no más de θ del eje x en sentidos opuestos (el izquierdo con vx &gt; 0, el derecho con vx &lt; 0), con las interrupciones
 * de menos de {@code persistence} frames cerradas. El tramo es el bloque que contiene el frame de distancia mínima real.
 *
 * <p>El evento recortado conserva las trayectorias completas y cambia la ventana común, el target y el tramo de v_d
 * (ver {@link PedestrianEvent}). v_d se mide desde el inicio de la ventana y, según {@link Target}:
 * <ul>
 *   <li>{@code COMMON} (opción 1, vigente): target = última posición en la ventana recortada; v_d, su rapidez media.</li>
 *   <li>{@code OWN} (opción 2, sensibilidad): target al final del tramo frontal propio de cada peatón (si termina después).</li>
 * </ul>
 * El rumbo se calcula sobre la trayectoria completa del evento, con diferencia centrada de ±{@code half} frames
 * disponibles y sus tiempos reales.
 *
 * <p>Compuerta de tramo compartido (DEFINICIONES 8c, umbral elegido post-hoc): si el tramo de un peatón en la ventana
 * pasa la x inicial del otro (su x en el primer frame de la ventana) en más de {@code sharedX} metros, la ventana común
 * termina en el último frame común anterior a aquel en que ese peatón la pasa.
 */
public final class FrontalTrim {
    private FrontalTrim() { }

    public enum Target { COMMON, OWN }

    public record Options(boolean enabled, double maxDegrees, int persistence, int half, Target target, boolean shared, double sharedX) {
        public static final double DEFAULT_SHARED_X = 1.5;
        public static final Options OFF = new Options(false, 0, 0, 0, Target.COMMON, false, 0);
        public static final Options DEFAULT = new Options(true, 45, 5, 2, Target.COMMON, true, DEFAULT_SHARED_X);

        public Options {
            if (enabled && (maxDegrees <= 0 || maxDegrees >= 90 || persistence < 1 || half < 1))
                throw new IllegalArgumentException("Recorte inválido: θ en (0, 90), persistencia ≥ 1, semiventana ≥ 1");
            if (shared && !(sharedX >= 0)) throw new IllegalArgumentException("--trim-shared-x debe ser ≥ 0: " + sharedX);
        }

        /** D(θ) sin la compuerta de tramo compartido. */
        public Options(boolean enabled, double maxDegrees, int persistence, int half, Target target) {
            this(enabled, maxDegrees, persistence, half, target, false, 0);
        }

        /** Lee --trim on|off, --trim-deg, --trim-persist, --trim-half, --trim-target common|own, --trim-shared on|off y --trim-shared-x. */
        public static Options parse(Map<String, String> o) {
            boolean on = switch (o.getOrDefault("trim", "on")) {
                case "on" -> true;
                case "off" -> false;
                default -> throw new IllegalArgumentException("--trim debe ser on u off: " + o.get("trim"));
            };
            if (!on) {
                for (String k : List.of("trim-deg", "trim-persist", "trim-half", "trim-target", "trim-shared", "trim-shared-x"))
                    if (o.containsKey(k)) throw new IllegalArgumentException("--" + k + " necesita --trim on");
                return OFF;
            }
            Target target = switch (o.getOrDefault("trim-target", "common")) {
                case "common" -> Target.COMMON;
                case "own" -> Target.OWN;
                default -> throw new IllegalArgumentException("--trim-target debe ser common u own: " + o.get("trim-target"));
            };
            boolean shared = switch (o.getOrDefault("trim-shared", "on")) {
                case "on" -> true;
                case "off" -> false;
                default -> throw new IllegalArgumentException("--trim-shared debe ser on u off: " + o.get("trim-shared"));
            };
            if (!shared && o.containsKey("trim-shared-x")) throw new IllegalArgumentException("--trim-shared-x necesita --trim-shared on");
            return new Options(true, Double.parseDouble(o.getOrDefault("trim-deg", String.valueOf(DEFAULT.maxDegrees))),
                    Integer.parseInt(o.getOrDefault("trim-persist", String.valueOf(DEFAULT.persistence))),
                    Integer.parseInt(o.getOrDefault("trim-half", String.valueOf(DEFAULT.half))), target,
                    shared, shared ? Double.parseDouble(o.getOrDefault("trim-shared-x", String.valueOf(DEFAULT_SHARED_X))) : 0);
        }

        /** Para los encabezados de salida. */
        public String label() {
            if (!enabled) return "recorte=off";
            String base = String.format(Locale.ROOT, "recorte=D%s_p%d_h%d_%s", maxDegrees, persistence, half, target.name().toLowerCase(Locale.ROOT));
            return shared ? base + String.format(Locale.ROOT, "_sx%s", sharedX) : base;     // sin compuerta, igual que antes
        }
    }

    public static List<PedestrianEvent> apply(List<PedestrianEvent> events, Options options) {
        if (!options.enabled()) return events;
        List<PedestrianEvent> out = new ArrayList<>(events.size());
        for (PedestrianEvent e : events) out.add(apply(e, options));
        return out;
    }

    public static PedestrianEvent apply(PedestrianEvent e, Options options) {
        if (!options.enabled()) return e;
        int[] window = window(e, options);
        int first = window[0], last = window[1];
        if (options.shared()) last = sharedEnd(e, first, last, options.sharedX());
        int[] target = { last, last };
        if (options.target() == Target.OWN) {
            int minFrame = e.minDistance().frame();
            target[0] = Math.max(last, ownEnd(e.left(), 1, minFrame, options));
            target[1] = Math.max(last, ownEnd(e.right(), -1, minFrame, options));
        }
        return new PedestrianEvent(e.number(), e.left(), e.right(), e.dtExp(), e.leemeMinDistance(), first, last,
                new int[] { first, first }, target);
    }

    /** Primer y último frame común del tramo frontal. */
    public static int[] window(PedestrianEvent e, Options options) {
        List<Integer> common = new ArrayList<>();
        for (int f = e.firstFrame(); f <= e.lastFrame(); f++)
            if (e.left().indexOf(f) >= 0 && e.right().indexOf(f) >= 0) common.add(f);
        double[] hl = headings(e.left(), 1, e.dtExp(), options.half());
        double[] hr = headings(e.right(), -1, e.dtExp(), options.half());
        boolean[] ok = new boolean[common.size()];
        int[] frames = new int[common.size()];
        for (int k = 0; k < ok.length; k++) {
            int f = common.get(k);
            frames[k] = f;
            ok[k] = hl[e.left().indexOf(f)] <= options.maxDegrees() && hr[e.right().indexOf(f)] <= options.maxDegrees();
        }
        int[] block = block(frames, closeGaps(ok, options.persistence()), e.minDistance().frame());
        if (block == null || block[0] == block[1])
            throw new IllegalArgumentException("El evento " + e.number() + " no tiene tramo frontal con θ = " + options.maxDegrees());
        return block;
    }

    /**
     * Compuerta de tramo compartido: si un peatón pasa la x inicial del otro en más de {@code x} metros dentro de la
     * ventana, devuelve el último frame común anterior al primero en que la pasa (el menor de los dos, si son ambos).
     */
    public static int sharedEnd(PedestrianEvent e, int first, int last, double x) {
        int end = last;
        for (int i = 0; i < 2; i++) {
            Trajectory t = e.pedestrian(i), o = e.pedestrian(1 - i);
            int sense = i == 0 ? 1 : -1;
            double x0 = o.x()[o.indexOf(first)];
            if (overshoot(t, sense, x0, first, last) <= x) continue;
            int previous = first;
            for (int f = first; f <= last; f++) {
                int k = t.indexOf(f);
                if (k < 0 || o.indexOf(f) < 0) continue;
                if (sense * (t.x()[k] - x0) > 0) break;
                previous = f;
            }
            end = Math.min(end, previous);
        }
        if (end <= first) throw new IllegalArgumentException("El evento " + e.number() + " queda sin ventana con la compuerta de tramo compartido");
        return end;
    }

    /** Cuánto pasa el peatón la x dada, en su sentido de avance, entre los frames first y last (negativo si no llega). */
    public static double overshoot(Trajectory t, int sense, double x0, int first, int last) {
        double best = Double.NEGATIVE_INFINITY;
        for (int k = 0; k < t.size(); k++)
            if (t.frames()[k] >= first && t.frames()[k] <= last) best = Math.max(best, sense * (t.x()[k] - x0));
        return best;
    }

    /** Último frame del tramo frontal propio del peatón (mismo criterio, solo con su rumbo). */
    static int ownEnd(Trajectory t, int sense, int minFrame, Options options) {
        double[] h = headings(t, sense, 0, options.half());     // el dt no cambia el ángulo
        boolean[] ok = new boolean[h.length];
        for (int k = 0; k < h.length; k++) ok[k] = h[k] <= options.maxDegrees();
        int[] block = block(t.frames(), closeGaps(ok, options.persistence()), minFrame);
        return block == null ? t.lastFrame() : block[1];
    }

    /**
     * Ángulo (°) entre la velocidad y el sentido de avance sobre x: 0 = de frente, 90 = perpendicular. La velocidad es
     * la diferencia entre los frames disponibles k − half y k + half (recortados en los bordes) sobre su tiempo real.
     */
    public static double[] headings(Trajectory t, int sense, double dtExp, int half) {
        int n = t.size();
        double[] out = new double[n];
        for (int k = 0; k < n; k++) {
            int a = Math.max(0, k - half), b = Math.min(n - 1, k + half);
            double dt = dtExp > 0 ? (t.frames()[b] - t.frames()[a]) * dtExp : (t.frames()[b] - t.frames()[a]);
            double vx = (t.x()[b] - t.x()[a]) / dt, vy = (t.y()[b] - t.y()[a]) / dt;
            out[k] = Math.toDegrees(Math.atan2(Math.abs(vy), sense * vx));
        }
        return out;
    }

    /** Cierra las corridas de false más cortas que persistence que están entre dos true. */
    static boolean[] closeGaps(boolean[] ok, int persistence) {
        boolean[] out = ok.clone();
        int k = 0, n = out.length;
        while (k < n) {
            if (out[k]) { k++; continue; }
            int j = k;
            while (j < n && !out[j]) j++;
            if (k > 0 && j < n && j - k < persistence) for (int m = k; m < j; m++) out[m] = true;
            k = j;
        }
        return out;
    }

    /** Bloque de true que contiene el frame; si ese frame no cumple, el bloque más largo. Null si no hay ninguno. */
    static int[] block(int[] frames, boolean[] ok, int frame) {
        int idx = java.util.Arrays.binarySearch(frames, frame);
        if (idx >= 0 && ok[idx]) {
            int a = idx, b = idx;
            while (a > 0 && ok[a - 1]) a--;
            while (b < ok.length - 1 && ok[b + 1]) b++;
            return new int[] { frames[a], frames[b] };
        }
        int[] best = null;
        for (int k = 0; k < ok.length; ) {
            if (!ok[k]) { k++; continue; }
            int j = k;
            while (j < ok.length - 1 && ok[j + 1]) j++;
            if (best == null || j - k > best[1] - best[0]) best = new int[] { k, j };
            k = j + 1;
        }
        return best == null ? null : new int[] { frames[best[0]], frames[best[1]] };
    }
}
