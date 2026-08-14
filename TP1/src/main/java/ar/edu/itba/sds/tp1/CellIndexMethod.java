package ar.edu.itba.sds.tp1;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class CellIndexMethod implements NeighborFinder {

    // Media vecindad: cada celda mira solo estos offsets, nunca hay doble conteo
    private static final int[][] OFFSETS = {{0, 0}, {1, 0}, {1, 1}, {0, 1}, {-1, 1}};

    private final int m;

    public CellIndexMethod(int m) {
        this.m = m;
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
                            // el filtro por id evita el auto-par y los TreeSet absorben el par repetido
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
                    "M invalido: se requiere L/M > rc + 2*rMax, pero L/M = %.4f y rc + 2*rMax = %.4f "
                            + "(L=%.4f, M=%d, rc=%.4f, rMax=%.4f). El M maximo valido es %d.",
                    cellSize, minCellSize, l, m, rc, rMax, maxValidM(l, rc, rMax)));
        }

        if (periodic) {
            NeighborFinder.validatePeriodic(l, rc, rMax);
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
        for (Particle p : particles) {
            int cx = cellIndex(p.x(), cellSize);
            int cy = cellIndex(p.y(), cellSize);
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
