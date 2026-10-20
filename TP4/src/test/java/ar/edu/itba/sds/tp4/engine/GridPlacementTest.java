package ar.edu.itba.sds.tp4.engine;

import ar.edu.itba.sds.tp4.engine.GridPlacement.*;
import ar.edu.itba.sds.tp4.engine.cim.Particle;
import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class GridPlacementTest {
    private static final double R = GridCapacity.R, r = GridCapacity.PARTICLE_RADIUS, S = 2 * r + 1e-4;
    private static final List<Particle> TOUCHING = GridPlacement.obstacles(r, r);

    private static List<Site> hex(List<Particle> obstacles) {
        return GridPlacement.sites(Lattice.HEX, Anchor.SITE_AT_ORIGIN, S, R, r, obstacles);
    }

    @Test void everyLatticeAndAnchorPlacesMaxNWithoutOverlap() {
        for (Lattice lattice : Lattice.values())
            for (Anchor anchor : Anchor.values()) {
                List<Site> sites = GridPlacement.sites(lattice, anchor, S, R, r, TOUCHING);
                List<Placed> placed = GridPlacement.place(sites, sites.size(), 1, 1);
                double min = GridCapacity.minClearance(placed, r, TOUCHING);
                assertTrue(min >= 0, lattice + "/" + anchor + ": distancia mínima " + min);
            }
    }

    @Test void obstacleRadiusIsTakenFromTheObstacle() {
        double big = 0.05;
        List<Particle> obstacles = GridPlacement.obstacles(0.2, big);
        for (Site s : hex(obstacles))
            for (Particle o : obstacles) assertTrue(Math.hypot(s.x() - o.x(), s.y() - o.y()) >= r + big);
        assertTrue(hex(obstacles).size() < hex(GridPlacement.obstacles(0.2, r)).size());
    }

    @Test void sameSeedSamePlacementOtherSeedOther() {
        List<Site> sites = hex(TOUCHING);
        assertEquals(GridPlacement.place(sites, 300, 5, 1), GridPlacement.place(sites, 300, 5, 1));
        assertNotEquals(GridPlacement.place(sites, 300, 5, 1), GridPlacement.place(sites, 300, 6, 1));
    }

    @Test void speedsHaveModuleV0() {
        for (Placed p : GridPlacement.place(hex(List.of()), 200, 9, 1)) assertEquals(1, Math.hypot(p.vx(), p.vy()), 1e-12);
    }

    @Test void impossibleNFailsExplicitly() {
        List<Site> sites = hex(TOUCHING);
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class, () -> GridPlacement.place(sites, sites.size() + 1, 1, 1));
        assertTrue(e.getMessage().startsWith("N imposible"), e.getMessage());
        assertThrows(IllegalArgumentException.class, () -> GridPlacement.sites(Lattice.HEX, Anchor.SITE_AT_ORIGIN, 2 * r - 1e-6, R, r, List.of()));
    }
}
