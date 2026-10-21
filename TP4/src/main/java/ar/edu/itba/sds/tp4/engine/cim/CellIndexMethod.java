package ar.edu.itba.sds.tp4.engine.cim;

// Copiado de TP1 (ar.edu.itba.sds.tp1). Agregado en TP4: dominio circular centrado en el origen
// (forCircle, findContacts), con corrimiento +R y validacion |r| <= R (D25), y forEachContact sin
// asignaciones por paso para el motor del Sistema 2.

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class CellIndexMethod implements NeighborFinder {

    // Media vecindad: cada celda mira solo estos offsets, nunca hay doble conteo
    private static final int[][] OFFSETS = {{0, 0}, {1, 0}, {1, 1}, {0, 1}, {-1, 1}};
    private static final double L_TOLERANCE = 1e-12;

    private final int m;
    // Dominio circular: radio R y corrimiento +R que lleva [-R, R]^2 a [0, 2R]^2. NaN y 0 en el cuadrado de TP1
    private final double circleRadius;
    private final double offset;
    // Listas por celda de forEachContact: head[celda] = primera particula (-1 si vacia), next[i] = la siguiente.
    // Se reservan una vez y se reusan, por eso una instancia no se comparte entre hilos
    private int[] head;
    private int[] next = new int[0];

    public CellIndexMethod(int m) {
        this(m, Double.NaN, 0);
    }

    private CellIndexMethod(int m, double circleRadius, double offset) {
        this.m = m;
        this.circleRadius = circleRadius;
        this.offset = offset;
    }

    /** Billar circular de radio R centrado en el origen: la grilla cubre [-R, R]^2 con L = 2R. */
    public static CellIndexMethod forCircle(int m, double radius) {
        if (!(radius > 0)) {
            throw new IllegalArgumentException("R debe ser > 0, se recibio R=" + radius);
        }
        return new CellIndexMethod(m, radius, radius);
    }

    /** Pares en contacto (xi > 0): distancia borde a borde < 0. Solo para forCircle. */
    public Map<Integer, Set<Integer>> findContacts(List<Particle> particles) {
        if (!isCircle()) {
            throw new IllegalStateException("findContacts requiere un CIM creado con forCircle");
        }
        return findNeighbors(particles, 2 * circleRadius, 0, false);
    }

    /**
     * Misma busqueda que findContacts (misma media vecindad, corrimiento +R, recorte de celda y validaciones), pero
     * sobre arreglos y sin HashMap/HashSet ni boxing: cada par en contacto se entrega una sola vez, con i < j.
     */
    @Override
    public void forEachContact(double[] x, double[] y, double radius, double l, PairVisitor visitor) {
        if (!isCircle()) {
            NeighborFinder.super.forEachContact(x, y, radius, l, visitor);
            return;
        }
        int n = x.length;
        validate(l, 0, n == 0 ? 0 : radius, false);
        validateCircle(x, y, l);

        if (head == null) {
            head = new int[m * m];
        }
        if (next.length < n) {
            next = new int[n];
        }
        Arrays.fill(head, -1);
        double cellSize = l / m;
        // De n-1 a 0: cada lista queda en orden creciente de indice
        for (int i = n - 1; i >= 0; i--) {
            int cell = cellIndex(x[i] + offset, cellSize) * m + cellIndex(y[i] + offset, cellSize);
            next[i] = head[cell];
            head[cell] = i;
        }

        for (int cx = 0; cx < m; cx++) {
            for (int cy = 0; cy < m; cy++) {
                int first = head[cx * m + cy];
                if (first < 0) {
                    continue;
                }
                for (int a = first; a >= 0; a = next[a]) {
                    // Pares dentro de la propia celda: b recorre las que siguen a a en la lista
                    for (int b = next[a]; b >= 0; b = next[b]) {
                        visitIfContact(a, b, x, y, radius, visitor);
                    }
                    for (int k = 1; k < OFFSETS.length; k++) {
                        int nx = cx + OFFSETS[k][0];
                        int ny = cy + OFFSETS[k][1];
                        if (nx < 0 || nx >= m || ny < 0 || ny >= m) {
                            continue;
                        }
                        for (int b = head[nx * m + ny]; b >= 0; b = next[b]) {
                            visitIfContact(a, b, x, y, radius, visitor);
                        }
                    }
                }
            }
        }
    }

    // Mismas operaciones que borderToBorderDistance(a, b) < 0, para que el redondeo sea identico
    private static void visitIfContact(int a, int b, double[] x, double[] y, double radius, PairVisitor visitor) {
        double dx = x[b] - x[a];
        double dy = y[b] - y[a];
        if (Math.sqrt(dx * dx + dy * dy) - radius - radius < 0) {
            visitor.visit(Math.min(a, b), Math.max(a, b));
        }
    }

    private boolean isCircle() {
        return !Double.isNaN(circleRadius);
    }

    /** M mas grande que cumple L/M > rc + 2*rMax. */
    public static int maxValidM(double l, double rc, double rMax) {
        double minCellSize = rc + 2 * rMax;
        if (minCellSize <= 0) {
            return 1;
        }
        return Math.max(1, (int) Math.ceil(l / minCellSize) - 1);
    }

    @Override
    public Map<Integer, Set<Integer>> findNeighbors(List<Particle> particles, double l, double rc, boolean periodic) {
        double rMax = 0;
        for (Particle p : particles) {
            rMax = Math.max(rMax, p.radius());
        }
        validate(l, rc, rMax, periodic);
        if (isCircle()) {
            validateCircle(particles, l, periodic);
        }

        List<Particle>[][] grid = buildGrid(l, particles);

        Map<Integer, Set<Integer>> neighbors = new HashMap<>();
        for (Particle p : particles) {
            neighbors.put(p.id(), new HashSet<>());
        }

        for (int cx = 0; cx < m; cx++) {
            for (int cy = 0; cy < m; cy++) {
                List<Particle> cell = grid[cx][cy];
                if (cell.isEmpty()) {
                    continue;
                }

                // Pares dentro de la propia celda: i < j evita el auto-par y el doble conteo
                for (int i = 0; i < cell.size(); i++) {
                    for (int j = i + 1; j < cell.size(); j++) {
                        checkPair(cell.get(i), cell.get(j), l, rc, periodic, neighbors);
                    }
                }

                for (int k = 1; k < OFFSETS.length; k++) {
                    int nx = cx + OFFSETS[k][0];
                    int ny = cy + OFFSETS[k][1];
                    if (periodic) {
                        nx = Math.floorMod(nx, m);
                        ny = Math.floorMod(ny, m);
                    } else if (nx < 0 || nx >= m || ny < 0 || ny >= m) {
                        continue;
                    }

                    for (Particle a : cell) {
                        for (Particle b : grid[nx][ny]) {
                            // Con M chico y contorno periodico una celda vecina puede ser la propia:
                            // el filtro por id evita el auto-par y los HashSet absorben el par repetido
                            if (a.id() != b.id()) {
                                checkPair(a, b, l, rc, periodic, neighbors);
                            }
                        }
                    }
                }
            }
        }

        return neighbors;
    }

    private void validate(double l, double rc, double rMax, boolean periodic) {
        if (m < 1) {
            throw new IllegalArgumentException("M debe ser >= 1, se recibio M=" + m);
        }
        if (rc < 0) {
            throw new IllegalArgumentException("rc debe ser >= 0, se recibio rc=" + rc);
        }

        double cellSize = l / m;
        double minCellSize = rc + 2 * rMax;
        if (cellSize <= minCellSize) {
            throw new IllegalArgumentException(String.format(
                    "M invalido: se requiere L/M > rc + 2*rMax, pero L/M = %s y rc + 2*rMax = %s "
                            + "(L=%s, M=%d, rc=%s, rMax=%s). El M maximo valido es %d.",
                    cellSize, minCellSize, l, m, rc, rMax, maxValidM(l, rc, rMax)));
        }

        if (periodic) {
            NeighborFinder.validatePeriodic(l, rc, rMax);
        }
    }

    // cellIndex recorta los indices a [0, M-1]: sin esta validacion una particula fuera del circulo
    // caeria en una celda del borde sin ningun error
    private void validateCircle(List<Particle> particles, double l, boolean periodic) {
        if (periodic) {
            throw new IllegalArgumentException("El dominio circular no admite contorno periodico");
        }
        validateCircleLength(l);
        for (Particle p : particles) {
            double distance = Math.hypot(p.x(), p.y());
            if (distance > circleRadius) {
                throw new IllegalArgumentException(String.format(
                        "Particula %d fuera del dominio: |r| = %s > R = %s", p.id(), distance, circleRadius));
            }
        }
    }

    // Misma validacion para forEachContact (la particula se nombra por su indice). Lejos del borde,
    // x² + y² < R²·(1 − 1e-9) ya asegura hypot <= R, asi que hypot solo se calcula cerca del borde (o con NaN)
    private void validateCircle(double[] x, double[] y, double l) {
        validateCircleLength(l);
        double surelyInside = circleRadius * circleRadius * (1 - 1e-9);
        for (int i = 0; i < x.length; i++) {
            if (x[i] * x[i] + y[i] * y[i] < surelyInside) {
                continue;
            }
            double distance = Math.hypot(x[i], y[i]);
            if (distance > circleRadius) {
                throw new IllegalArgumentException(String.format(
                        "Particula %d fuera del dominio: |r| = %s > R = %s", i, distance, circleRadius));
            }
        }
    }

    private void validateCircleLength(double l) {
        if (Math.abs(l - 2 * circleRadius) > L_TOLERANCE) {
            throw new IllegalArgumentException(String.format(
                    "Dominio circular: se requiere L = 2R, pero L=%s y 2R=%s", l, 2 * circleRadius));
        }
    }

    @SuppressWarnings("unchecked")
    private List<Particle>[][] buildGrid(double l, List<Particle> particles) {
        List<Particle>[][] grid = new List[m][m];
        for (int i = 0; i < m; i++) {
            for (int j = 0; j < m; j++) {
                grid[i][j] = new ArrayList<>();
            }
        }

        double cellSize = l / m;
        // El corrimiento solo decide la celda; las distancias se calculan con las coordenadas originales
        for (Particle p : particles) {
            int cx = cellIndex(p.x() + offset, cellSize);
            int cy = cellIndex(p.y() + offset, cellSize);
            grid[cx][cy].add(p);
        }
        return grid;
    }

    private int cellIndex(double coordinate, double cellSize) {
        return Math.min(m - 1, Math.max(0, (int) (coordinate / cellSize)));
    }

    private void checkPair(Particle a, Particle b, double l, double rc, boolean periodic, Map<Integer, Set<Integer>> neighbors) {
        double borderDistance = NeighborFinder.borderToBorderDistance(a, b, l, periodic);
        if (borderDistance < rc) {
            neighbors.get(a.id()).add(b.id());
            neighbors.get(b.id()).add(a.id());
        }
    }
}
