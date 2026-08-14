package ar.edu.itba.sds.tp1;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class BruteForceNeighborFinder implements NeighborFinder {

    @Override
    public Map<Integer, Set<Integer>> findNeighbors(List<Particle> particles, double l, double rc, boolean periodic) {
        if (periodic) {
            double maxRadius = particles.stream().mapToDouble(Particle::radius).max().orElse(0.0);
            NeighborFinder.validatePeriodic(l, rc, maxRadius);
        }

        Map<Integer, Set<Integer>> neighbors = new HashMap<>();
        for (Particle p : particles) {
            neighbors.put(p.id(), new HashSet<>());
        }

        for (int i = 0; i < particles.size(); i++) {
            for (int j = i + 1; j < particles.size(); j++) {
                Particle a = particles.get(i);
                Particle b = particles.get(j);
                if (NeighborFinder.borderToBorderDistance(a, b, l, periodic) < rc) {
                    neighbors.get(a.id()).add(b.id());
                    neighbors.get(b.id()).add(a.id());
                }
            }
        }

        return neighbors;
    }
}