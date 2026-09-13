package ar.edu.itba.sds.tp3.engine;

import ar.edu.itba.sds.tp3.Main;
import ar.edu.itba.sds.tp3.io.StageFile;
import ar.edu.itba.sds.tp3.models.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class EngineTest {
    @TempDir Path temp;
    private static final double EPS = 1e-9;
    private static final SimulationConfig C = SimulationConfig.defaults();
    private Particle particle(int id, double x, double y, double vx, double vy) {
        return new Particle(id, x, y, vx, vy, C.radius(), C.mass());
    }
    private StageGeneration.Stage stage(List<Particle> p, List<Obstacle> o) {
        return new StageGeneration.Stage(C, 42, p, o);
    }
    private double energy(List<Particle> ps) {
        return ps.stream().mapToDouble(p -> p.mass() * (p.vx()*p.vx() + p.vy()*p.vy()) / 2).sum();
    }
    @Test void predictsApproachingButNotSeparatingOrTangentDiscs() {
        assertEquals(0.4, CollisionSimulator.collisionTime(1, 0, -2, 0, 0.2), EPS);
        assertEquals(Double.POSITIVE_INFINITY, CollisionSimulator.collisionTime(1, 0, 2, 0, 0.2));
        assertEquals(Double.POSITIVE_INFINITY, CollisionSimulator.collisionTime(1, 0.2, -2, 0, 0.2));
        assertEquals(Double.POSITIVE_INFINITY, CollisionSimulator.collisionTime(1, 0, 0, 0, 0.2));
    }
    @Test void unequalMassObliqueCollisionConservesMomentumAndEnergy() {
        Particle a = new Particle(1, 0, 0, 1, 0.7, 0.05, 2);
        Particle b = new Particle(2, 0.06, 0.08, -0.3, -0.5, 0.05, 3);
        double e = energy(List.of(a,b)), px = a.mass()*a.vx()+b.mass()*b.vx(), py = a.mass()*a.vy()+b.mass()*b.vy();
        CollisionSimulator.bounce(a,b);
        assertEquals(e, energy(List.of(a,b)), EPS);
        assertEquals(px, a.mass()*a.vx()+b.mass()*b.vx(), EPS);
        assertEquals(py, a.mass()*a.vy()+b.mass()*b.vy(), EPS);
    }
    @Test void eventBecomesInvalidAfterCollision() {
        Particle p = particle(1, 0.5, 0.3, 1, 0);
        Event event = new Event(1, Event.Type.VERTICAL_WALL, p, null, null, 0);
        assertTrue(event.valid());
        p.setVelocityAfterCollision(-1, 0);
        assertFalse(event.valid());
    }
    @Test void goalsCountOnlyOnceAndOriginalStageIsNotMutated() throws Exception {
        Particle p = particle(1, 0.6, 0.34, 1, 0);
        var result = new CollisionSimulator(stage(List.of(p), List.of())).run(4, 1000, (t,e,g,ps) -> {});
        assertEquals(1, result.goals());
        assertEquals(0.5825, result.t90(), EPS);
        assertEquals(4, result.time());
        assertFalse(p.used()); assertEquals(0.6, p.x());
    }
    @Test void outsideGoalDoesNotScore() throws Exception {
        var result = new CollisionSimulator(stage(List.of(particle(1, 0.6, 0.1, 1, 0)), List.of())).run(2, 1, (t,e,g,ps) -> {});
        assertEquals(0, result.goals()); assertTrue(Double.isNaN(result.t90()));
    }
    @Test void savesIncomingVelocityAtCollisionAndContinuesWithReflectedVelocity() throws Exception {
        Particle p = particle(1, 0.6, 0.34, 1, 0);
        double contactTime = C.length() - C.radius() - p.x();
        List<Double> times = new ArrayList<>();
        var result = new CollisionSimulator(stage(List.of(p), List.of())).run(contactTime + 0.1, 1, (t,e,g,ps) -> {
            times.add(t);
            if (e == 1 && Math.abs(t - contactTime) < EPS) {
                assertEquals(C.length() - C.radius(), ps.getFirst().x(), EPS);
                assertEquals(1, ps.getFirst().vx(), EPS);
                assertEquals(0, g);
                assertFalse(ps.getFirst().used());
            } else if (t > contactTime) {
                assertEquals(C.length() - C.radius() - 0.1, ps.getFirst().x(), EPS);
                assertEquals(-1, ps.getFirst().vx(), EPS);
                assertEquals(1, g);
            }
        });
        assertEquals(3, times.size());
        assertEquals(contactTime, times.get(1), EPS);
        assertEquals(1, result.goals());
    }
    @Test void reflectsBothWallsAtCorner() throws Exception {
        double duration = 0.2;
        Particle p = particle(1, C.length()-C.radius()-duration, C.width()-C.radius()-duration, 1, 1);
        new CollisionSimulator(stage(List.of(p), List.of())).run(0.3, 1, (t,e,g,ps) -> {
            if (t == 0.3) { assertEquals(-1, ps.getFirst().vx()); assertEquals(-1, ps.getFirst().vy()); }
        });
    }
    @Test void obstacleReflectsAndHeadOnParticlesExchangeVelocities() throws Exception {
        new CollisionSimulator(stage(List.of(particle(1, 0.3, 0.34, 1, 0)), List.of(new Obstacle(0.6,0.34,0.1))))
                .run(0.2, 1, (t,e,g,ps) -> { if (t == 0.2) assertEquals(-1, ps.getFirst().vx(), EPS); });
        new CollisionSimulator(stage(List.of(particle(1,0.4,0.34,1,0),particle(2,0.8,0.34,-1,0)), List.of()))
                .run(0.2, 1, (t,e,g,ps) -> { if (t == 0.2) { assertEquals(-1, ps.get(0).vx(), EPS); assertEquals(1, ps.get(1).vx(), EPS); }});
    }
    @Test void seededGenerationAndFileRoundTrip() throws Exception {
        var a = StageGeneration.generate(C, 100, 42, List.of(new Obstacle(0.6,0.34,0.08)));
        var b = StageGeneration.generate(C, 100, 42, a.obstacles());
        Path first = temp.resolve("a.txt"), second = temp.resolve("b.txt");
        StageFile.write(first,a); StageFile.write(second,b);
        assertEquals(Files.readString(first),Files.readString(second));
        StageFile.write(second, StageFile.read(first));
        assertEquals(Files.readString(first),Files.readString(second));
        for (Particle p : a.particles()) assertEquals(1, Math.hypot(p.vx(),p.vy()), EPS);
    }
    @Test void rejectsInvalidGeometryAndMalformedInput() throws Exception {
        assertThrows(IllegalArgumentException.class, () -> StageGeneration.generate(C, 1, 42, List.of(new Obstacle(0,0,0.1))));
        assertThrows(IllegalArgumentException.class, () -> StageGeneration.generate(C, 1, 42, List.of(new Obstacle(0.5,0.3,0.1),new Obstacle(0.51,0.3,0.1))));
        assertThrows(IllegalArgumentException.class, () -> stage(List.of(particle(1,0.5,0.3,0,0),particle(2,0.5,0.3,0,0)),List.of()));
        Files.writeString(temp.resolve("bad.txt"),"format=tp3-v1 N=2\n");
        assertThrows(IllegalArgumentException.class, () -> StageFile.read(temp.resolve("bad.txt")));
    }
    @Test void manyCollisionsConserveEnergyAndKeepDiscsInsideWithoutOverlap() throws Exception {
        var s = StageGeneration.generate(C, 100, 123, List.of(new Obstacle(0.6,0.34,0.08)));
        double initial = energy(s.particles());
        var result = new CollisionSimulator(s).run(3, 50, (t,e,g,ps) -> {
            assertEquals(initial, energy(ps), EPS);
            for (int i=0; i<ps.size(); i++) {
                Particle p = ps.get(i);
                assertTrue(p.x() >= p.radius()-EPS && p.x() <= C.length()-p.radius()+EPS);
                assertTrue(p.y() >= p.radius()-EPS && p.y() <= C.width()-p.radius()+EPS);
                for (Obstacle o : s.obstacles()) assertTrue(Math.hypot(p.x()-o.x(),p.y()-o.y()) >= p.radius()+o.radius()-EPS);
                for (int j=0; j<i; j++) {
                    Particle b = ps.get(j);
                    assertTrue(Math.hypot(p.x()-b.x(),p.y()-b.y()) >= p.radius()+b.radius()-EPS);
                }
            }
        });
        assertTrue(result.events()>1000); assertEquals(3, result.time());
    }
    @Test void commandsProduceInitialAndFinalFrames() throws Exception {
        Path ic = temp.resolve("initial.txt"), out = temp.resolve("run.txt");
        Main.execute(new String[]{"generate","--n","10","--out",ic.toString()});
        Main.execute(new String[]{"simulate","--input",ic.toString(),"--time","0.5","--every","100","--out",out.toString()});
        String text = Files.readString(out);
        assertTrue(text.contains("t=0.0 events=0")); assertTrue(text.contains("t=0.5 events="));
        assertTrue(text.contains("# tf=0.5 outputEvery=100"));
        assertThrows(IllegalArgumentException.class, () -> Main.execute(new String[]{"simulate","--input",ic.toString(),"--out",ic.toString()}));
    }
}
