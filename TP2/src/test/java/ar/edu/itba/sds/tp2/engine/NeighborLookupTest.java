package ar.edu.itba.sds.tp2.engine;

import ar.edu.itba.sds.tp1.BruteForceNeighborFinder;
import ar.edu.itba.sds.tp1.CellIndexMethod;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;

class NeighborLookupTest {

    @Test
    void findsNeighborsForHandPickedPositions() {
        // L=10, rc=1. dist(1,2)=0.5<rc, dist(1,4)=0.9<rc, dist(2,4)=~1.03>rc, 3 está lejos de todos.
        List<VicsekParticle> particles = List.of(
                new VicsekParticle(1, 1.0, 1.0, 0.0),
                new VicsekParticle(2, 1.5, 1.0, 0.0),
                new VicsekParticle(3, 5.0, 5.0, 0.0),
                new VicsekParticle(4, 1.0, 1.9, 0.0)
        );
        NeighborLookup lookup = new NeighborLookup(new BruteForceNeighborFinder(), 10.0, 1.0, false);

        Map<Integer, Set<Integer>> result = lookup.findNeighbors(particles);

        assertEquals(Map.of(
                1, Set.of(2, 4),
                2, Set.of(1),
                3, Set.of(),
                4, Set.of(1)
        ), result);
    }

    @Test
    void cimMatchesBruteForceOnRandomDatasetWallMode() {
        double l = 20.0;
        double rc = 1.0;
        List<VicsekParticle> particles = randomParticles(150, l, new Random(123));
        int m = CellIndexMethod.maxValidM(l, rc, 0.0);

        NeighborLookup bruteForceLookup = new NeighborLookup(new BruteForceNeighborFinder(), l, rc, false);
        NeighborLookup cimLookup = new NeighborLookup(new CellIndexMethod(m), l, rc, false);

        assertEquals(bruteForceLookup.findNeighbors(particles), cimLookup.findNeighbors(particles));
    }

    @Test
    void cimMatchesBruteForceOnRandomDatasetPeriodicMode() {
        double l = 20.0;
        double rc = 1.0;
        List<VicsekParticle> particles = randomParticles(150, l, new Random(123));
        int m = CellIndexMethod.maxValidM(l, rc, 0.0);

        NeighborLookup bruteForceLookup = new NeighborLookup(new BruteForceNeighborFinder(), l, rc, true);
        NeighborLookup cimLookup = new NeighborLookup(new CellIndexMethod(m), l, rc, true);

        assertEquals(bruteForceLookup.findNeighbors(particles), cimLookup.findNeighbors(particles));
    }

    @Test
    void periodicBoundaryDetectsWrapAroundNeighborsOnly() {
        double l = 10.0;
        double rc = 1.0;
        // dist directa = 9.8 (no vecinas sin wrap); dist con wrap-around = 0.2 < rc.
        List<VicsekParticle> particles = List.of(
                new VicsekParticle(1, 0.1, 5.0, 0.0),
                new VicsekParticle(2, l - 0.1, 5.0, 0.0)
        );

        Map<Integer, Set<Integer>> periodicResult =
                new NeighborLookup(new BruteForceNeighborFinder(), l, rc, true).findNeighbors(particles);
        Map<Integer, Set<Integer>> wallResult =
                new NeighborLookup(new BruteForceNeighborFinder(), l, rc, false).findNeighbors(particles);

        assertEquals(Map.of(1, Set.of(2), 2, Set.of(1)), periodicResult);
        assertEquals(Map.of(1, Set.of(), 2, Set.of()), wallResult);
    }

    private static List<VicsekParticle> randomParticles(int n, double l, Random random) {
        List<VicsekParticle> particles = new ArrayList<>(n);
        for (int i = 1; i <= n; i++) {
            double x = random.nextDouble() * l;
            double y = random.nextDouble() * l;
            double theta = random.nextDouble() * 2 * Math.PI;
            particles.add(new VicsekParticle(i, x, y, theta));
        }
        return particles;
    }
}