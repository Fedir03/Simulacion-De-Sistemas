package ar.edu.itba.sds.tp3.engine;

import ar.edu.itba.sds.tp3.Main;
import ar.edu.itba.sds.tp3.engine.obstacles.*;
import ar.edu.itba.sds.tp3.io.StageFile;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.*;
import java.util.List;
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
        assertThrows(IllegalArgumentException.class, () -> ObstacleGenerators.create("missing", 2, 0.05));
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
        assertThrows(IllegalArgumentException.class, () -> Main.execute(new String[]{"generate", "--obstacles", config.toString(), "--obstacle-algorithm", "random", "--out", out.toString()}));
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
}
