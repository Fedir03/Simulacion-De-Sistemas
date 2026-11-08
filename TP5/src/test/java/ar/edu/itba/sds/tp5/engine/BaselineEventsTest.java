package ar.edu.itba.sds.tp5.engine;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import ar.edu.itba.sds.tp5.Main;
import ar.edu.itba.sds.tp5.data.EventParser;
import ar.edu.itba.sds.tp5.data.PedestrianEvent;
import ar.edu.itba.sds.tp5.io.OutputFiles;
import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

/** Condiciones de D13 sobre los 19 eventos, sin capa. */
class BaselineEventsTest {
    private static final Simulation SIM = new Simulation(SfmParameters.defaults(), Integrator.DEFAULT, Simulation.DEFAULT_DT_DIV);
    private static List<OutputFiles.EventReport> reports;

    @BeforeAll
    static void runAll() throws IOException {
        reports = new ArrayList<>();
        for (PedestrianEvent e : EventParser.parse(Path.of("data"))) reports.add(Main.run(SIM, e, Main.DEFAULT_V0_FRAMES));
    }

    @Test
    void everyPedestrianReachesTheTargetWithoutOrbiting() {
        for (OutputFiles.EventReport r : reports) {
            PedestrianEvent e = r.event();
            Agent[] agents = { Agent.from(e, 0, Main.DEFAULT_V0_FRAMES), Agent.from(e, 1, Main.DEFAULT_V0_FRAMES) };
            Simulation.Result full = SIM.run(agents, e.dtExp(), Main.EXTENDED_INTERVALS);
            for (int i = 0; i < 2; i++) {
                assertTrue(full.arrival()[i] > 0, "evento " + e.number() + ", peatón " + (i + 1) + " no llega");
                double straight = Math.hypot(agents[i].targetX() - agents[i].x0(), agents[i].targetY() - agents[i].y0());
                assertTrue(full.pathLength()[i] < 1.5 * straight, "evento " + e.number() + ", peatón " + (i + 1)
                        + ": recorrió " + full.pathLength()[i] + " para una recta de " + straight);
            }
        }
    }

    /** Si falla en algún evento, el retiro cambia la interacción: hay que avisar antes de seguir (D13). */
    @Test
    void arrivalHappensAfterTheClosestApproach() {
        for (OutputFiles.EventReport r : reports) {
            PedestrianEvent e = r.event();
            Agent[] agents = { Agent.from(e, 0, Main.DEFAULT_V0_FRAMES), Agent.from(e, 1, Main.DEFAULT_V0_FRAMES) };
            Simulation.Result full = SIM.run(agents, e.dtExp(), Main.EXTENDED_INTERVALS);
            double firstArrival = Math.min(full.arrival()[0], full.arrival()[1]);
            assertTrue(full.minDistanceTime() < firstArrival - 2 * full.dt2(),
                    "evento " + e.number() + ": t_dmin = " + full.minDistanceTime() + ", primera llegada = " + firstArrival);
        }
    }

    @Test
    void firstMetricVariantsMatchUntilSomeoneLeaves() {
        for (OutputFiles.EventReport r : reports) {
            for (int i = 0; i < 2; i++) {
                var p = r.ecm().pedestrians()[i];
                if (p.n1() == p.n2()) assertEquals(p.ecm1Excluding(), p.ecm1Filled(), 1e-12, "evento " + r.event().number());
                else assertTrue(p.n1() < p.n2());
            }
        }
    }
}
