package ar.edu.itba.sds.tp3.engine;

import ar.edu.itba.sds.tp3.engine.StageGeneration.GridAnchor;
import ar.edu.itba.sds.tp3.models.*;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class GridGenerationTest {
    private static final SimulationConfig C = SimulationConfig.defaults();
    private static final double S = StageGeneration.GRID_EXTRA_SPACING;

    private static StageGeneration.Stage grid(int n, long seed, GridAnchor anchor) {
        return StageGeneration.generateGrid(C, n, seed, List.of(), anchor, S, 0);
    }
    private static int nmax(GridAnchor anchor, double margin) {
        return StageGeneration.gridSites(C, List.of(), anchor, S, margin).size();
    }

    @Test void sameSeedGivesSamePlacementAndDirections() {
        for (GridAnchor anchor : GridAnchor.values()) {
            var a = grid(300, 11, anchor).particles();
            var b = grid(300, 11, anchor).particles();
            var other = grid(300, 12, anchor).particles();
            for (int i = 0; i < a.size(); i++) {
                assertEquals(a.get(i).x(), b.get(i).x()); assertEquals(a.get(i).y(), b.get(i).y());
                assertEquals(a.get(i).vx(), b.get(i).vx()); assertEquals(a.get(i).vy(), b.get(i).vy());
            }
            assertTrue(java.util.stream.IntStream.range(0, a.size()).anyMatch(i -> a.get(i).x() != other.get(i).x()));
        }
    }

    @Test void nmaxFillsEveryLegalSiteWithoutOverlapsForSeveralSeeds() {
        for (GridAnchor anchor : GridAnchor.values()) {
            int n = nmax(anchor, 0);
            for (long seed = 1; seed <= 5; seed++) {
                // El constructor de Stage valida solapes, ids y que todo esté dentro de la mesa.
                var stage = grid(n, seed, anchor);
                assertEquals(n, stage.particles().size());
                for (Particle p : stage.particles()) assertEquals(C.speed(), Math.hypot(p.vx(), p.vy()), 1e-12);
            }
            assertThrows(IllegalArgumentException.class, () -> grid(n + 1, 1, anchor));
        }
    }

    @Test void anchorSiteIsPresentAndSpacingIsTwoRPlusExtra() {
        var center = StageGeneration.gridSites(C, List.of(), GridAnchor.CENTER, S, 0);
        assertTrue(center.contains(new StageGeneration.Site(C.length() / 2, C.width() / 2)));
        var corner = StageGeneration.gridSites(C, List.of(), GridAnchor.CORNER, S, 0);
        assertTrue(corner.contains(new StageGeneration.Site(C.radius(), C.radius())));
        for (var sites : List.of(center, corner)) {
            double min = Double.POSITIVE_INFINITY;
            for (int i = 0; i < sites.size(); i++)
                for (int j = 0; j < i; j++)
                    min = Math.min(min, Math.hypot(sites.get(i).x() - sites.get(j).x(), sites.get(i).y() - sites.get(j).y()));
            assertEquals(2 * C.radius() + S, min, 1e-12);
        }
    }

    @Test void benchmarkConfigurationFillsAllSitesInsideTheTable() {
        // Configuración del benchmark (Tp3Case) y de Main generate --placement grid: ancla corner, margen 0,1 mm.
        int n = nmax(GridAnchor.CORNER, S);
        assertEquals(737, n);
        var stage = StageGeneration.generateGrid(C, n, 1, List.of(), GridAnchor.CORNER, S, S);
        assertEquals(n, stage.particles().size());
        var ps = stage.particles();
        for (int i = 0; i < ps.size(); i++) {
            Particle p = ps.get(i);
            assertTrue(p.x() >= p.radius() && p.x() <= C.length() - p.radius() && p.y() >= p.radius() && p.y() <= C.width() - p.radius());
            for (int j = 0; j < i; j++)
                assertTrue(Math.hypot(p.x() - ps.get(j).x(), p.y() - ps.get(j).y()) >= 2 * C.radius());
        }
        assertThrows(IllegalArgumentException.class, () -> StageGeneration.generateGrid(C, n + 1, 1, List.of(), GridAnchor.CORNER, S, S));
    }

    @Test void wallMarginKeepsSitesAwayFromWallsAndObstaclesAreExcluded() {
        double margin = S;
        for (GridAnchor anchor : GridAnchor.values()) {
            for (var site : StageGeneration.gridSites(C, List.of(), anchor, S, margin)) {
                assertTrue(site.x() >= C.radius() + margin && site.x() <= C.length() - C.radius() - margin);
                assertTrue(site.y() >= C.radius() + margin && site.y() <= C.width() - C.radius() - margin);
            }
            assertTrue(nmax(anchor, margin) <= nmax(anchor, 0));
        }
        var obstacle = List.of(new Obstacle(C.length() / 2, C.width() / 2, 0.1));
        var sites = StageGeneration.gridSites(C, obstacle, GridAnchor.CENTER, S, 0);
        assertTrue(sites.size() < nmax(GridAnchor.CENTER, 0));
        assertDoesNotThrow(() -> StageGeneration.generateGrid(C, sites.size(), 3, obstacle, GridAnchor.CENTER, S, 0));
    }
}
