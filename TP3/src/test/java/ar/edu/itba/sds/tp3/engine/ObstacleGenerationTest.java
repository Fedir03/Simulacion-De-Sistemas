package ar.edu.itba.sds.tp3.engine;

import ar.edu.itba.sds.tp3.Main;
import ar.edu.itba.sds.tp3.engine.obstacles.*;
import ar.edu.itba.sds.tp3.io.StageFile;
import ar.edu.itba.sds.tp3.models.Obstacle;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class ObstacleGenerationTest {
    @TempDir Path temp;
    private static final SimulationConfig C = SimulationConfig.defaults();

    @Test void randomIsReproducibleAndGeometryAllowsParticles() {
        var generator = new RandomObstacleGenerator(4, 0.05);
        var first = generator.generate(C, 42);
        assertEquals(4, first.size());
        assertEquals(first, generator.generate(C, 42));
        assertNotEquals(first, generator.generate(C, 43));
        assertDoesNotThrow(() -> StageGeneration.generate(C, 100, 42, first));
        assertTrue(new EmptyObstacleGenerator().generate(C, 42).isEmpty());
    }

    @Test void invalidOrImpossibleConfigurationsFailWithBoundedAttempts() {
        assertThrows(IllegalArgumentException.class, () -> new RandomObstacleGenerator(0, 0.05));
        assertThrows(IllegalArgumentException.class, () -> new RandomObstacleGenerator(2, Double.NaN));
        assertThrows(IllegalArgumentException.class, () -> new RandomObstacleGenerator(2, 0.001).generate(C, 42));
        assertThrows(IllegalArgumentException.class, () -> new RandomObstacleGenerator(2, 0.4).generate(C, 42));
        assertThrows(IllegalArgumentException.class, () -> new RandomObstacleGenerator(2, 0.34).generate(C, 42));
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("missing", java.util.Map.of()));
    }

    @Test void cliDefaultsToTwoObstaclesAndSupportsEmptyAndFile() throws Exception {
        Path out = temp.resolve("initial.txt");
        Main.execute(new String[]{"generate", "--out", out.toString()});
        assertEquals(2, StageFile.read(out).obstacles().size());
        Main.execute(new String[]{"generate", "--obstacle-algorithm", "none", "--out", out.toString()});
        assertEquals(List.of(), StageFile.read(out).obstacles());
        Path config = temp.resolve("obstacles.txt");
        Files.writeString(config, "0.6 0.34 0.08\n");
        Main.execute(new String[]{"generate", "--obstacles", config.toString(), "--out", out.toString()});
        assertEquals(0.08, StageFile.read(out).obstacles().getFirst().radius());
        // Archivo y algoritmo se combinan: el algoritmo agrega obstáculos sin solapar los del archivo.
        Main.execute(new String[]{"generate", "--obstacles", config.toString(), "--obstacle-algorithm", "random", "--out", out.toString()});
        assertEquals(3, StageFile.read(out).obstacles().size());
        assertEquals(0.08, StageFile.read(out).obstacles().getFirst().radius());
        assertThrows(IllegalArgumentException.class, () -> Main.execute(new String[]{"generate", "--obstacles", config.toString(), "--obstacle-radius", "0.1", "--out", out.toString()}));
        assertThrows(IllegalArgumentException.class, () -> Main.execute(new String[]{"generate", "--obstacle-algorithm", "none", "--obstacle-count", "2", "--out", out.toString()}));
    }

    @Test void cliCanKeepObstaclesFixedAcrossParticleRealizations() throws Exception {
        Path a = temp.resolve("a.txt"), b = temp.resolve("b.txt");
        Main.execute(new String[]{"generate", "--obstacle-algorithm", "random", "--obstacle-count", "3", "--obstacle-radius", "0.04", "--obstacle-seed", "17", "--seed", "1", "--out", a.toString()});
        Main.execute(new String[]{"generate", "--obstacle-algorithm", "random", "--obstacle-count", "3", "--obstacle-radius", "0.04", "--obstacle-seed", "17", "--seed", "2", "--out", b.toString()});
        var first = StageFile.read(a);
        var second = StageFile.read(b);
        assertEquals(3, first.obstacles().size());
        assertEquals(0.04, first.obstacles().getFirst().radius());
        assertEquals(first.obstacles(), second.obstacles());
        assertNotEquals(first.particles().getFirst().x(), second.particles().getFirst().x());
    }

    @Test void singleObstacleDefaultsToTheCenterAndAcceptsCoordinates() {
        assertEquals(List.of(new Obstacle(0.6, 0.34, 0.1)), ObstacleGenerators.create("single", Map.of()).generate(C, 1));
        assertEquals(List.of(new Obstacle(0.3, 0.2, 0.05)),
                ObstacleGenerators.create("single", Map.of("x", "0.3", "y", "0.2", "radius", "0.05")).generate(C, 1));
    }

    @Test void filledRegionsLeaveNoRoomForParticlesAndKeepFreeZoneUsable() {
        // Embudo: esquinas detrás de la recta palo (0, 0.44) – (0.3, 0.68), por simetría en las cuatro.
        RegionFill.Region funnel = (x, y) -> {
            double fx = Math.min(x, C.length() - x), fy = Math.max(y, C.width() - y);
            return 0.3 * (fy - 0.44) - 0.24 * fx > 0 ? 1 : 0;
        };
        RegionFill.Region semicircle = (x, y) -> Math.hypot(x - C.length(), y - C.width() / 2) - 0.36;
        Map<String, RegionFill.Region> regions = Map.of("funnel", funnel, "semicircle", semicircle);
        for (var entry : regions.entrySet()) {
            var obstacles = ObstacleGenerators.create(entry.getKey(), Map.of()).generate(C, 1);
            assertDoesNotThrow(() -> StageGeneration.validate(C, List.of(), obstacles));
            assertDoesNotThrow(() -> StageGeneration.generate(C, 100, 7, obstacles));
            assertEquals(obstacles, ObstacleGenerators.create(entry.getKey(), Map.of()).generate(C, 99));
            // Ningún punto de la región bloqueada, en una grilla más fina que la de relleno, admite una partícula.
            double r = C.radius(), step = 4e-4;
            for (double x = r; x <= C.length() - r; x += step)
                for (double y = r; y <= C.width() - r; y += step) {
                    if (!(entry.getValue().distanceToFree(x, y) > 0)) continue;
                    double px = x, py = y;
                    assertTrue(obstacles.stream().anyMatch(o -> Math.hypot(px - o.x(), py - o.y()) < o.radius() + r),
                            entry.getKey() + ": hueco en (" + x + ", " + y + ")");
                }
        }
    }

    @Test void algorithmsRejectOptionsTheyDoNotUse() {
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("none", Map.of("count", "2")));
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("funnel", Map.of("radius", "0.1")));
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("single", Map.of("seed", "3")));
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("funnel", Map.of("funnel-length", "0.7")).generate(C, 1));
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("semicircle", Map.of("max-radius", "0.01")).generate(C, 1));
    }

    @Test void cliExportsTheCompetitionConfiguration() throws Exception {
        Path out = temp.resolve("initial.txt"), config = temp.resolve("config.txt");
        Main.execute(new String[]{"generate", "--obstacle-algorithm", "funnel", "--obstacle-funnel-length", "0.25",
                "--out", out.toString(), "--obstacles-out", config.toString()});
        assertEquals(StageFile.read(out).obstacles(), StageFile.readObstacles(config));
    }

    @Test void postsAndBowlGenerateValidSymmetricMaps() {
        var posts = ObstacleGenerators.create("posts", Map.of("radius", "0.05")).generate(C, 1);
        double[][] expected = {{0.05, 0.19}, {0.05, 0.49}, {1.15, 0.19}, {1.15, 0.49}};
        assertEquals(4, posts.size());
        for (int i = 0; i < 4; i++) {
            assertEquals(expected[i][0], posts.get(i).x(), 1e-12);
            assertEquals(expected[i][1], posts.get(i).y(), 1e-12);
            assertEquals(0.05, posts.get(i).radius());
        }
        var bowl = ObstacleGenerators.create("semicircle", Map.of("goals", "both", "free-radius", "0.4")).generate(C, 1);
        assertDoesNotThrow(() -> StageGeneration.generate(C, 100, 3, bowl));
        // Ambos arcos quedan libres y el centro de la mesa bloqueado.
        assertTrue(bowl.stream().anyMatch(o -> Math.hypot(0.6 - o.x(), 0.34 - o.y()) < o.radius()));
        assertTrue(bowl.stream().noneMatch(o -> Math.hypot(o.x(), 0.34 - o.y()) < 0.4 - C.radius()));
        assertTrue(bowl.stream().noneMatch(o -> Math.hypot(1.2 - o.x(), 0.34 - o.y()) < 0.4 - C.radius()));
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("semicircle", Map.of("goals", "left")));
    }

    @Test void regionFillRespectsExistingObstacles() {
        List<Obstacle> base = List.of(new Obstacle(0.6, 0.34, 0.32));
        for (String name : List.of("funnel", "semicircle")) {
            var params = name.equals("funnel") ? Map.of("funnel-length", "0.3") : Map.of("goals", "both", "free-radius", "0.3");
            var added = ObstacleGenerators.create(name, params).generate(C, 1, base);
            assertFalse(added.contains(base.getFirst()));
            List<Obstacle> all = new ArrayList<>(base);
            all.addAll(added);
            assertDoesNotThrow(() -> StageGeneration.validate(C, List.of(), all), name);
        }
    }

    @Test void funnelEdgeIsMadeOfMinimumDiscsFacingTheField() {
        double r = C.radius(), post = 0.44;
        for (String length : List.of("0.05", "0.3")) {
            double a = Double.parseDouble(length);
            var obstacles = ObstacleGenerators.create("funnel", Map.of("funnel-length", length, "edge-radius", Double.toString(r))).generate(C, 1);
            assertDoesNotThrow(() -> StageGeneration.generate(C, 100, 5, obstacles));
            double ux = a, uy = C.width() - post, norm = Math.hypot(ux, uy);
            for (Obstacle o : obstacles) {
                double fx = Math.min(o.x(), C.length() - o.x()), fy = Math.max(o.y(), C.width() - o.y());
                // Distancia con signo a la recta palo–banda, positiva hacia la cancha.
                double toField = (uy * fx - ux * (fy - post)) / norm;
                if (toField > -o.radius() + 1e-9) assertEquals(r, o.radius(), 1e-12, "disco de frontera en " + o);
            }
        }
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("funnel", Map.of("edge-radius", "0")));
    }

    @Test void latticeIsEquidistantSymmetricAndPassable() {
        double s = 0.12, r = C.radius();
        var lattice = ObstacleGenerators.create("lattice", Map.of("spacing", Double.toString(s))).generate(C, 1);
        assertDoesNotThrow(() -> StageGeneration.generate(C, 100, 3, lattice));
        for (Obstacle o : lattice) {
            assertEquals(r, o.radius());
            // Paso de al menos 2r contra las paredes, simetría y vecinos a distancia s.
            assertTrue(Math.min(Math.min(o.x(), C.length() - o.x()), Math.min(o.y(), C.width() - o.y())) - r >= 2 * r - 1e-12);
            assertTrue(lattice.stream().anyMatch(q -> Math.hypot(q.x() - (C.length() - o.x()), q.y() - (C.width() - o.y())) < 1e-9));
            double nearest = lattice.stream().filter(q -> q != o).mapToDouble(q -> Math.hypot(q.x() - o.x(), q.y() - o.y())).min().orElseThrow();
            assertEquals(s, nearest, 1e-9);
        }
        var withCenter = new LatticeObstacleGenerator(s, Double.NaN).generate(C, 1, List.of(new Obstacle(0.6, 0.34, 0.2)));
        assertTrue(withCenter.size() < lattice.size());
        assertTrue(withCenter.stream().allMatch(o -> Math.hypot(o.x() - 0.6, o.y() - 0.34) - 0.2 - r >= 2 * r - 1e-12));
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("lattice", Map.of("spacing", "0.06")).generate(C, 1));
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("lattice", Map.of("spacing", "0.07")).generate(C, 1));
    }

    @Test void ellipseHasMinimumEdgeAndObjectsAtBothFoci() {
        double r = C.radius(), a = 0.6, b = Math.sqrt(0.36 - 0.09);
        // Distancia a la elipse: en los ejes y en un punto sobre ella.
        assertEquals(0.1, EllipseObstacleGenerator.distance(a, b, 0.7, 0), 1e-12);
        assertEquals(0.1, EllipseObstacleGenerator.distance(a, b, 0, b + 0.1), 1e-12);
        assertEquals(0, EllipseObstacleGenerator.distance(a, b, a * Math.cos(0.7), b * Math.sin(0.7)), 1e-9);
        for (String shape : List.of("none", "disc", "line", "lens")) {
            Map<String, String> params = shape.equals("none") ? Map.of() : Map.of("focus-shape", shape, "focus-size", "0.1");
            var obstacles = ObstacleGenerators.create("ellipse", params).generate(C, 1);
            assertDoesNotThrow(() -> StageGeneration.generate(C, 100, 9, obstacles), shape);
            for (Obstacle o : obstacles) {
                double u = o.x() - 0.6, v = o.y() - 0.34;
                boolean nearFocus = Math.hypot(Math.abs(u) - 0.3, v) < 0.15;
                // Todo disco del borde que asoma hacia el interior de la elipse es de radio mínimo.
                if (!nearFocus && EllipseObstacleGenerator.distance(a, b, Math.abs(u), Math.abs(v)) < o.radius() - 1e-9)
                    assertEquals(r, o.radius(), 1e-12, shape + " " + o);
            }
            if (!shape.equals("none"))
                for (double fx : new double[]{0.3, 0.9})
                    assertTrue(obstacles.stream().anyMatch(o -> Math.abs(o.x() - fx) < 0.15 && Math.abs(o.y() - 0.34) < 0.15), shape + " foco " + fx);
        }
        var discs = ObstacleGenerators.create("ellipse", Map.of("focus-shape", "disc", "focus-size", "0.08")).generate(C, 1)
                .stream().filter(o -> o.radius() == 0.08).toList();
        assertEquals(2, discs.size());
        assertEquals(0.3, discs.get(0).x(), 1e-12);
        assertEquals(0.9, discs.get(1).x(), 1e-12);
        assertTrue(discs.stream().allMatch(o -> Math.abs(o.y() - 0.34) < 1e-12));
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("ellipse", Map.of("focus-shape", "star")));
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("ellipse", Map.of("focus-x", "0.7")).generate(C, 1));
    }
}
