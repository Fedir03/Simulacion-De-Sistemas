package ar.edu.itba.sds.tp2.engine;

import ar.edu.itba.sds.tp1.NeighborFinder;
import ar.edu.itba.sds.tp1.Particle;

import java.util.List;
import java.util.Map;
import java.util.Set;

/** Adapta VicsekParticle al NeighborFinder de TP1 (pluggable: CIM o BruteForce). */
public final class NeighborLookup {
    private final NeighborFinder neighborFinder;
    private final double l;
    private final double rc;
    private final boolean periodic;

    public NeighborLookup(NeighborFinder neighborFinder, double l, double rc, boolean periodic) {
        this.neighborFinder = neighborFinder;
        this.l = l;
        this.rc = rc;
        this.periodic = periodic;
    }

    public Map<Integer, Set<Integer>> findNeighbors(List<VicsekParticle> particles) {
        List<Particle> tp1Particles = particles.stream()
                .map(p -> new Particle(p.id(), p.x(), p.y(), 0.0))
                .toList();
        return neighborFinder.findNeighbors(tp1Particles, l, rc, periodic);
    }

    public double l() {
        return l;
    }

    public double rc() {
        return rc;
    }

    public boolean periodic() {
        return periodic;
    }
}