package ar.edu.itba.sds.tp5.diagnostics;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.engine.cpm.CpmParameters;
import org.junit.jupiter.api.Test;

/** El CPM del TP reproduce el diagrama fundamental del paper ("set of parameters 2", Fig. 4) en la pista circular. */
class CpmRacetrackTest {
    private static final CpmParameters SET2 = new CpmParameters(0.10, 0.37, 0.9, 0.5, 0.1);

    @Test void fundamentalDiagramOfSet2() {
        // Fig. 4 leída a ojo: ρ ≈ 2 → 0,45 m/s; ρ ≈ 6 → 0,21 m/s
        assertEquals(0.45, CpmRacetrack.run(SET2, 0.95, 75, 1), 0.04);
        assertEquals(0.21, CpmRacetrack.run(SET2, 0.95, 225, 1), 0.03);
    }

    @Test void particlesNeverCrossEachOtherOrTheWalls() {
        assertTrue(CpmRacetrack.minGap(SET2, 0.95, 150, 3) > 0.5);
    }
}
