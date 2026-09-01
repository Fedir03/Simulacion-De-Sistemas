package ar.edu.itba.sds.tp2.analysis;

import ar.edu.itba.sds.tp1.BruteForceNeighborFinder;
import ar.edu.itba.sds.tp2.engine.InitialConditionGenerator;
import ar.edu.itba.sds.tp2.engine.NeighborLookup;
import ar.edu.itba.sds.tp2.engine.VicsekParticle;
import ar.edu.itba.sds.tp2.engine.VicsekSimulation;
import ar.edu.itba.sds.tp2.engine.VoterModel;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class SimulationReaderTest {

    private static final String HEADER = "model=standard N=2 L=10.0 rc=1.0 dt=1.0 v0=0.03 "
            + "eta=0.5 periodic=true seedIC=1 seedLoop=2 theta0=random";

    private static Path write(Path dir, String contents) throws IOException {
        Path path = dir.resolve("corrida.txt");
        Files.writeString(path, contents);
        return path;
    }

    @Test
    void readsBackARunWrittenByTheEngine(@TempDir Path tempDir) throws IOException {
        int n = 5;
        int steps = 4;
        double l = 10.0;
        List<VicsekParticle> initial = InitialConditionGenerator.generate(n, l, new Random(1));
        NeighborLookup lookup = new NeighborLookup(new BruteForceNeighborFinder(), l, 1.0, true);
        Path out = tempDir.resolve("run.txt");
        new VicsekSimulation(initial, lookup, new VoterModel(), "voter",
                1.0, 0.03, 0.5, steps, new Random(2), 1L, 2L, "random").run(out);

        List<Frame> frames = new ArrayList<>();
        RunHeader header;
        try (SimulationReader reader = SimulationReader.open(out)) {
            header = reader.header();
            Frame frame;
            while ((frame = reader.next()) != null) {
                frames.add(frame);
            }
        }

        assertEquals("voter", header.model());
        assertEquals(n, header.n());
        assertEquals(l, header.l());
        assertTrue(header.periodic());
        assertEquals(0.05, header.density(), 1e-12);   // N=5 sobre L=10
        assertEquals(steps + 1, frames.size());
        assertEquals(0, frames.get(0).step());
        assertEquals(steps, frames.get(frames.size() - 1).step());
        for (Frame frame : frames) {
            assertEquals(n, frame.particles().size());
        }
        assertEquals(initial, frames.get(0).particles());
    }

    @Test
    void defaultsTheta0ForRunsWithoutTheField(@TempDir Path tempDir) throws IOException {
        Path path = write(tempDir, HEADER.replace(" theta0=random", "")
                + "\nt=0\n1 1.0 2.0 0.0\n2 3.0 4.0 1.0\n");

        try (SimulationReader reader = SimulationReader.open(path)) {
            assertEquals("random", reader.header().theta0());
        }
    }

    @Test
    void returnsNullAtTheEndOfTheFile(@TempDir Path tempDir) throws IOException {
        Path path = write(tempDir, HEADER + "\nt=0\n1 1.0 2.0 0.0\n2 3.0 4.0 1.0\n");

        try (SimulationReader reader = SimulationReader.open(path)) {
            assertEquals(0, reader.next().step());
            assertNull(reader.next());
        }
    }

    @Test
    void rejectsATruncatedBlock(@TempDir Path tempDir) throws IOException {
        Path path = write(tempDir, HEADER + "\nt=0\n1 1.0 2.0 0.0\n");

        try (SimulationReader reader = SimulationReader.open(path)) {
            IllegalArgumentException error = assertThrows(IllegalArgumentException.class, reader::next);
            assertTrue(error.getMessage().contains("se esperaban 2 particulas"),
                    "mensaje inesperado: " + error.getMessage());
        }
    }

    @Test
    void rejectsMissingHeaderFields(@TempDir Path tempDir) throws IOException {
        Path path = write(tempDir, HEADER.replace(" seedLoop=2", "") + "\nt=0\n");

        IllegalArgumentException error = assertThrows(IllegalArgumentException.class,
                () -> SimulationReader.open(path));
        assertTrue(error.getMessage().contains("seedLoop"),
                "mensaje inesperado: " + error.getMessage());
    }

    @Test
    void rejectsNonIncreasingTimeBlocks(@TempDir Path tempDir) throws IOException {
        Path path = write(tempDir, HEADER
                + "\nt=1\n1 1.0 2.0 0.0\n2 3.0 4.0 1.0\n"
                + "t=0\n1 1.0 2.0 0.0\n2 3.0 4.0 1.0\n");

        try (SimulationReader reader = SimulationReader.open(path)) {
            reader.next();
            assertThrows(IllegalArgumentException.class, reader::next);
        }
    }

    @Test
    void rejectsAnEmptyFile(@TempDir Path tempDir) throws IOException {
        Path path = write(tempDir, "");

        assertThrows(IllegalArgumentException.class, () -> SimulationReader.open(path));
    }
}
