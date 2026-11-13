package ar.edu.itba.sds.tp5.engine.layer;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Capa E (huevo): cada peatón lleva un espacio personal con forma de huevo, con la punta hacia su velocidad.
 * En el marco del peatón (u hacia el rumbo, w lateral) el huevo es la mitad trasera de un círculo de radio b
 * (u ≤ 0) y, adelante, |w| ≤ b (1 − (u/a)²)^q para 0 ≤ u ≤ a, con la punta a una distancia a del centro. Con
 * a ≥ b y q ∈ [1/2, 1] es convexo. La punta hacia adelante es la anticipación: la capa no predice nada más.
 * <p>
 * La capa solo reacciona al contacto entre huevos:
 * <ul>
 *   <li>Huevos separados: e_target = e_t (el modelo base, sin cambios).</li>
 *   <li>Huevos en contacto: el huevo del otro es un borde sólido. Si e_t apunta hacia él, se le quita la componente
 *       normal al contacto y el peatón se desliza por la tangente. En el choque frontal exacto, a la derecha.</li>
 *   <li>Huevos solapados (por el paso de tiempo o porque la velocidad tarda τ en seguir a e_target): además gira en
 *       sentido contrario al solape, con una componente normal hacia afuera proporcional a la profundidad.</li>
 * </ul>
 * En cuanto los huevos dejan de tocarse vuelve e_t, así que retoma solo el camino al target final.
 * <p>
 * En la forma del enunciado: mientras los huevos se tocan, el target final se reemplaza por el target temporal
 * x_T = x_i + a e_target, en la punta del huevo; solo cambia la dirección de la velocidad deseada (su módulo sigue
 * siendo v_d) y no se agrega ninguna fuerza. Los parámetros calibrables son a y b; q y la escala de profundidad son
 * constantes declaradas.
 * <p>
 * Con parámetros por peatón (calibración individual opcional), cada uno tiene su huevo (a_i, b_i) y el contacto se
 * decide entre el huevo propio y el del otro, así que los dos ven el mismo contacto.
 * <p>
 * Geometría: la distancia con signo entre dos convexos S_i y S_j es max_n [n·(x_i − x_j) − h_j(n) − h_i(−n)],
 * con h la función soporte; es negativa si se solapan, y el n que la maximiza es la normal del contacto (de j
 * hacia i). Se evalúa en {@value #DIRECTIONS} direcciones.
 */
public final class EggLayer implements AvoidanceLayer {
    /** Exponente q del frente: 1 es una punta con ángulo, 1/2 una media elipse. */
    public static final double TIP_EXPONENT = 0.75;
    /** Profundidad de solape (m) con la que el desvío se abre 45° de la tangente al contacto. */
    public static final double PENETRATION_SCALE = 0.05;
    /** Por debajo de esta rapidez el rumbo no está definido: el propio huevo apunta a e_t y el del otro, hacia i. */
    public static final double MIN_HEADING_SPEED = 0.05;
    static final int DIRECTIONS = 180;
    private static final int TABLE = 720;
    private static final int BOUNDARY_POINTS = 2000;

    /** Funciones soporte ya calculadas, por (a, b): la grilla por peatón crea miles de capas con las mismas formas. */
    private static final Map<List<Double>, double[]> SUPPORTS = new ConcurrentHashMap<>();

    private final double front, half, otherFront, otherHalf;
    /** Función soporte de cada huevo en su marco (punta hacia +x), en TABLE ángulos equiespaciados: el propio y el del otro. */
    private final double[] support, otherSupport;
    private final double[] cos = new double[DIRECTIONS], sin = new double[DIRECTIONS], angle = new double[DIRECTIONS];

    /**
     * @param front a, distancia del centro a la punta (m)
     * @param half  b, semiancho y radio de la parte trasera (m)
     */
    public EggLayer(double front, double half) {
        this(front, half, front, half);
    }

    /** Huevo propio (a, b) frente al huevo del otro (a', b'). */
    private EggLayer(double front, double half, double otherFront, double otherHalf) {
        this.front = front;
        this.half = half;
        this.otherFront = otherFront;
        this.otherHalf = otherHalf;
        support = support(front, half);
        otherSupport = support(otherFront, otherHalf);
        for (int k = 0; k < DIRECTIONS; k++) {
            angle[k] = 2 * Math.PI * k / DIRECTIONS;
            cos[k] = Math.cos(angle[k]);
            sin[k] = Math.sin(angle[k]);
        }
    }

    /** Parámetros por peatón: el peatón 1 con (a1, b1) y el 2 con (a2, b2), cada uno viendo el huevo del otro. */
    public static AvoidanceLayer perPedestrian(double a1, double b1, double a2, double b2) {
        EggLayer first = new EggLayer(a1, b1, a2, b2), second = new EggLayer(a2, b2, a1, b1);
        return new AvoidanceLayer() {
            @Override public boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                               double vd, double ex, double ey, double[] out) {
                throw new IllegalStateException("Con parámetros por peatón se usa a través de forAgent");
            }
            @Override public AvoidanceLayer forAgent(int agent) { return agent == 0 ? first : second; }
            @Override public String label() { return "capa=E a1=" + a1 + " b1=" + b1 + " a2=" + a2 + " b2=" + b2 + " q=" + TIP_EXPONENT; }
        };
    }

    private static double[] support(double front, double half) {
        if (!(half > 0)) throw new IllegalArgumentException("b debe ser positivo: " + half);
        if (!(front >= half)) throw new IllegalArgumentException("a no puede ser menor que b: " + front);
        return SUPPORTS.computeIfAbsent(List.of(front, half), key -> {
            double[][] boundary = boundary(front, half, BOUNDARY_POINTS);
            double[] h = new double[TABLE + 1];
            for (int m = 0; m <= TABLE; m++) {
                double a = 2 * Math.PI * m / TABLE, nx = Math.cos(a), ny = Math.sin(a), best = Double.NEGATIVE_INFINITY;
                for (double[] p : boundary) best = Math.max(best, p[0] * nx + p[1] * ny);
                h[m] = best;
            }
            return h;
        });
    }

    /** Borde del huevo en su marco (punta hacia +x), con unos {@code n} puntos. */
    public static double[][] boundary(double front, double half, int n) {
        int back = n / 3, tip = (n - back) / 2;
        double[][] p = new double[back + 2 * tip][];
        for (int k = 0; k < back; k++) {
            double a = Math.PI / 2 + Math.PI * k / (back - 1);
            p[k] = new double[] { half * Math.cos(a), half * Math.sin(a) };
        }
        for (int k = 0; k < tip; k++) {
            double u = front * k / (tip - 1), w = half * Math.pow(Math.max(0, 1 - (u / front) * (u / front)), TIP_EXPONENT);
            p[back + k] = new double[] { u, w };
            p[back + tip + k] = new double[] { u, -w };
        }
        return p;
    }

    /** h(α − rumbo): función soporte de un huevo con ese rumbo en la dirección de ángulo α. */
    private static double h(double[] support, double alpha, double heading) {
        double x = (alpha - heading) / (2 * Math.PI);
        x = (x - Math.floor(x)) * TABLE;
        int m = (int) x;
        if (m >= TABLE) m = TABLE - 1;
        double f = x - m;
        return support[m] * (1 - f) + support[m + 1] * f;
    }

    /**
     * Distancia con signo entre los huevos (negativa si se solapan), con p = x_i − x_j.
     *
     * @param normal sale con la normal del contacto, de j hacia i
     */
    public double separation(double px, double py, double headingI, double headingJ, double[] normal) {
        double best = Double.NEGATIVE_INFINITY;
        for (int k = 0; k < DIRECTIONS; k++) {
            double s = cos[k] * px + sin[k] * py - h(otherSupport, angle[k], headingJ) - h(support, angle[k] + Math.PI, headingI);
            if (s > best) {
                best = s;
                normal[0] = cos[k];
                normal[1] = sin[k];
            }
        }
        return best;
    }

    @Override public boolean direction(double xi, double yi, double xj, double yj, double vxj, double vyj,
                                       double vd, double ex, double ey, double[] out) {
        // Sin la velocidad propia, el huevo de i apunta a e_t
        return directionWithVelocity(xi, yi, vd * ex, vd * ey, xj, yj, vxj, vyj, vd, ex, ey, out);
    }

    @Override public boolean directionWithVelocity(double xi, double yi, double vxi, double vyi, double xj, double yj, double vxj, double vyj,
                                                   double vd, double ex, double ey, double[] out) {
        out[0] = ex;
        out[1] = ey;
        double px = xi - xj, py = yi - yj;
        if (Math.hypot(px, py) > front + otherFront) return false;  // ni punta contra punta se tocan
        double headingJ = Math.hypot(vxj, vyj) > MIN_HEADING_SPEED ? Math.atan2(vyj, vxj) : Math.atan2(py, px);
        double headingI = Math.hypot(vxi, vyi) > MIN_HEADING_SPEED ? Math.atan2(vyi, vxi) : Math.atan2(ey, ex);
        double[] n = new double[2];
        double gap = separation(px, py, headingI, headingJ, n);
        if (gap > 0) return false;                                  // no se tocan: modelo base

        // Borde sólido: se quita la componente de e_t que entra en el otro huevo
        double into = ex * n[0] + ey * n[1], bx = ex, by = ey;
        if (into < 0) {
            bx = ex - into * n[0];
            by = ey - into * n[1];
            double norm = Math.hypot(bx, by);
            if (norm < 1e-9) {                                      // choque frontal exacto: tangente a la derecha de e_t
                bx = -n[1];
                by = n[0];
                if (bx * ey - by * ex < 0) { bx = -bx; by = -by; }
            } else {
                bx /= norm;
                by /= norm;
            }
        }
        // Solape: gira al revés, con la normal hacia afuera pesada por la profundidad
        double g = -gap / PENETRATION_SCALE, ax = bx + g * n[0], ay = by + g * n[1], norm = Math.hypot(ax, ay);
        out[0] = ax / norm;
        out[1] = ay / norm;
        return true;
    }

    public double front() { return front; }
    public double half() { return half; }

    @Override public String label() {
        return "capa=E a=" + front + " b=" + half + (front == otherFront && half == otherHalf ? "" : " a_otro=" + otherFront + " b_otro=" + otherHalf)
                + " q=" + TIP_EXPONENT;
    }
}
