package ar.edu.itba.sds.tp2.analysis;

import ar.edu.itba.sds.tp2.engine.NeighborLookup;
import ar.edu.itba.sds.tp2.engine.VicsekParticle;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Clusters de un cuadro: un cluster es una componente conexa del grafo de vecinos, o sea un
 * conjunto de particulas donde todo par esta unido por una cadena de saltos entre particulas
 * a distancia menor que rc.
 *
 * <p>El grafo lo arma NeighborLookup con el CIM de TP1, asi que aca solo queda recorrerlo:
 * un BFS por componente, quedandose con la mas grande.
 */
public final class ClusterAnalysis {

    private ClusterAnalysis() {
    }

    public static ClusterStats of(List<VicsekParticle> particles, NeighborLookup lookup) {
        if (particles.isEmpty()) {
            throw new IllegalArgumentException("no hay particulas para analizar");
        }
        return of(particles.size(), lookup.findNeighbors(particles));
    }

    /**
     * Igual que {@link #of(List, NeighborLookup)} pero sobre un grafo ya calculado. El mapa
     * tiene que ser simetrico y traer una entrada por particula, que es lo que garantiza
     * NeighborFinder (las particulas aisladas vienen con el conjunto vacio).
     */
    public static ClusterStats of(int n, Map<Integer, Set<Integer>> neighbors) {
        Set<Integer> visited = new HashSet<>(neighbors.size() * 2);
        int largest = 0;
        int clusters = 0;
        Set<Integer> largestMembers = Set.of();

        for (Integer start : neighbors.keySet()) {
            if (!visited.add(start)) {
                continue;
            }
            clusters++;
            Set<Integer> component = new HashSet<>();
            component.add(start);
            Deque<Integer> pending = new ArrayDeque<>();
            pending.add(start);
            while (!pending.isEmpty()) {
                Integer current = pending.removeFirst();
                for (Integer neighbor : neighbors.getOrDefault(current, Set.of())) {
                    if (visited.add(neighbor)) {
                        component.add(neighbor);
                        pending.addLast(neighbor);
                    }
                }
            }
            if (component.size() > largest) {
                largest = component.size();
                largestMembers = component;
            }
        }

        if (visited.size() != n) {
            throw new IllegalStateException("el grafo de vecinos cubre " + visited.size()
                    + " particulas pero se esperaban " + n);
        }
        return new ClusterStats(largest, clusters, n, largestMembers);
    }
}
