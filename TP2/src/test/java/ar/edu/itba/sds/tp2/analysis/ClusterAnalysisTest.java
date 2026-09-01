package ar.edu.itba.sds.tp2.analysis;

import ar.edu.itba.sds.tp1.BruteForceNeighborFinder;
import ar.edu.itba.sds.tp1.CellIndexMethod;
import ar.edu.itba.sds.tp2.engine.NeighborLookup;
import ar.edu.itba.sds.tp2.engine.VicsekParticle;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ClusterAnalysisTest {

    private static final double L = 10.0;
    private static final double RC = 1.0;

    private static NeighborLookup lookup(boolean periodic) {
        return new NeighborLookup(new BruteForceNeighborFinder(), L, RC, periodic);
    }

    private static VicsekParticle at(int id, double x, double y) {
        return new VicsekParticle(id, x, y, 0.0);
    }

    @Test
    void particlesFarApartAreEachTheirOwnCluster() {
        List<VicsekParticle> particles = List.of(
                at(1, 1.0, 1.0), at(2, 5.0, 1.0), at(3, 1.0, 5.0), at(4, 5.0, 5.0));

        ClusterStats stats = ClusterAnalysis.of(particles, lookup(false));

        assertEquals(4, stats.clusterCount());
        assertEquals(1, stats.largestSize());
        assertEquals(0.25, stats.s());
    }

    @Test
    void particlesWithinRcFormASingleCluster() {
        List<VicsekParticle> particles = List.of(
                at(1, 5.0, 5.0), at(2, 5.5, 5.0), at(3, 6.0, 5.0), at(4, 6.5, 5.0));

        ClusterStats stats = ClusterAnalysis.of(particles, lookup(false));

        assertEquals(1, stats.clusterCount());
        assertEquals(4, stats.largestSize());
        assertEquals(1.0, stats.s());
    }

    @Test
    void reportsTheLargestOfSeveralGroups() {
        List<VicsekParticle> particles = List.of(
                at(1, 1.0, 1.0), at(2, 1.4, 1.0), at(3, 1.8, 1.0),
                at(4, 8.0, 8.0), at(5, 8.4, 8.0));

        ClusterStats stats = ClusterAnalysis.of(particles, lookup(false));

        assertEquals(2, stats.clusterCount());
        assertEquals(3, stats.largestSize());
        assertEquals(3.0 / 5.0, stats.s());
    }

    @Test
    void connectivityIsTransitiveAlongAChain() {
        List<VicsekParticle> particles = new ArrayList<>();
        for (int id = 1; id <= 10; id++) {
            particles.add(at(id, 0.5 + 0.8 * (id - 1), 5.0));
        }

        ClusterStats stats = ClusterAnalysis.of(particles, lookup(false));

        assertEquals(1, stats.clusterCount());
        assertEquals(1.0, stats.s());
    }

    @Test
    void periodicBoundaryJoinsParticlesOnOppositeEdges() {
        List<VicsekParticle> particles = List.of(at(1, 0.2, 5.0), at(2, 9.9, 5.0));

        assertEquals(1, ClusterAnalysis.of(particles, lookup(true)).clusterCount());
        assertEquals(2, ClusterAnalysis.of(particles, lookup(false)).clusterCount());
    }

    @Test
    void cellIndexMethodAgreesWithBruteForce() {
        Random random = new Random(7);
        List<VicsekParticle> particles = new ArrayList<>();
        for (int id = 1; id <= 300; id++) {
            particles.add(at(id, random.nextDouble() * L, random.nextDouble() * L));
        }
        NeighborLookup cim = new NeighborLookup(
                new CellIndexMethod(CellIndexMethod.maxValidM(L, RC, 0.0)), L, RC, true);

        assertEquals(ClusterAnalysis.of(particles, lookup(true)),
                     ClusterAnalysis.of(particles, cim));
    }

    @Test
    void sIsAlwaysBetweenOneOverNAndOne() {
        Random random = new Random(11);
        List<VicsekParticle> particles = new ArrayList<>();
        for (int id = 1; id <= 200; id++) {
            particles.add(at(id, random.nextDouble() * L, random.nextDouble() * L));
        }

        ClusterStats stats = ClusterAnalysis.of(particles, lookup(true));

        assertTrue(stats.s() >= 1.0 / 200, "S no puede ser menor a 1/N: " + stats.s());
        assertTrue(stats.s() <= 1.0, "S no puede superar 1: " + stats.s());
        assertEquals(200, stats.n());
    }
}
