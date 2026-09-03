package ar.edu.itba.sds.tp2.engine;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class InitialConditionFileTest {

    @Test
    void writeThenReadReturnsSameData(@TempDir Path tempDir) throws IOException {
        Path file = tempDir.resolve("ic.txt");
        List<VicsekParticle> particles = InitialConditionGenerator.generate(5, 10.0, new Random(3));

        InitialConditionFile.write(file, 5, 10.0, 3L, particles);
        InitialConditionFile.Data data = InitialConditionFile.read(file);

        assertEquals(5, data.n());
        assertEquals(10.0, data.l());
        assertEquals(3L, data.seedIC());
        assertEquals(particles, data.particles());
    }

    @Test
    void missingSeedICFieldThrowsClearError(@TempDir Path tempDir) throws IOException {
        Path file = tempDir.resolve("ic.txt");
        Files.writeString(file, "N=2 L=10.0\nt=0\n1 1.0 1.0 0.0\n2 2.0 2.0 0.0\n");

        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class,
                () -> InitialConditionFile.read(file));

        assertTrue(exception.getMessage().contains("seedIC"),
                "mensaje inesperado: " + exception.getMessage());
    }

    @Test
    void missingT0MarkerThrowsClearError(@TempDir Path tempDir) throws IOException {
        Path file = tempDir.resolve("ic.txt");
        Files.writeString(file, "N=1 L=10.0 seedIC=1\n1 1.0 1.0 0.0\n");

        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class,
                () -> InitialConditionFile.read(file));

        assertTrue(exception.getMessage().contains("t=0"),
                "mensaje inesperado: " + exception.getMessage());
    }

    @Test
    void tooFewParticleLinesThrowsClearError(@TempDir Path tempDir) throws IOException {
        Path file = tempDir.resolve("ic.txt");
        Files.writeString(file, "N=2 L=10.0 seedIC=1\nt=0\n1 1.0 1.0 0.0\n");

        assertThrows(IllegalArgumentException.class, () -> InitialConditionFile.read(file));
    }
}
