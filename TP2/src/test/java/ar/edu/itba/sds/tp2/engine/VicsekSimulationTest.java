package ar.edu.itba.sds.tp2.engine;

import ar.edu.itba.sds.tp1.BruteForceNeighborFinder;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.regex.Pattern;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class VicsekSimulationTest {

    private static final Pattern PARTICLE_LINE = Pattern.compile("^\\d+ \\S+ \\S+ \\S+$");

    @Test
    void runProducesExpectedBlockCountAndFormat(@TempDir Path tempDir) throws IOException {
        int n = 4;
        double l = 10.0;
        int steps = 3;
        List<VicsekParticle> initial = InitialConditionGenerator.generate(n, l, new Random(1));
        NeighborLookup lookup = new NeighborLookup(new BruteForceNeighborFinder(), l, 1.0, true);
        VicsekSimulation simulation = new VicsekSimulation(
                initial, lookup, new VoterModel(), "voter",
                1.0, 0.03, 0.5, steps, new Random(99), 1L, 99L, "random");

        Path output = tempDir.resolve("output.txt");
        simulation.run(output);

        List<String> lines = Files.readAllLines(output);
        Map<String, String> header = parseHeader(lines.get(0));
        assertEquals("voter", header.get("model"));
        assertEquals(String.valueOf(n), header.get("N"));
        assertEquals("true", header.get("periodic"));

        long blockCount = lines.stream().filter(line -> line.startsWith("t=")).count();
        assertEquals(steps + 1, blockCount);

        long particleLineCount = lines.stream().filter(PARTICLE_LINE.asMatchPredicate()).count();
        assertEquals((long) (steps + 1) * n, particleLineCount);
    }

    @Test
    void sameSeedsProduceByteIdenticalOutput(@TempDir Path tempDir) throws IOException {
        Path outputA = tempDir.resolve("a.txt");
        Path outputB = tempDir.resolve("b.txt");

        runFreshSimulation(outputA, 10, 5, 42L, 7L);
        runFreshSimulation(outputB, 10, 5, 42L, 7L);

        assertArrayEquals(Files.readAllBytes(outputA), Files.readAllBytes(outputB));
    }

    @Test
    void sameInitialConditionDifferentLoopSeedDivergesFromT1(@TempDir Path tempDir) throws IOException {
        double l = 10.0;
        List<VicsekParticle> sharedInitial = InitialConditionGenerator.generate(5, l, new Random(3));
        NeighborLookup lookupA = new NeighborLookup(new BruteForceNeighborFinder(), l, 1.0, true);
        NeighborLookup lookupB = new NeighborLookup(new BruteForceNeighborFinder(), l, 1.0, true);

        VicsekSimulation simA = new VicsekSimulation(
                sharedInitial, lookupA, new VoterModel(), "voter",
                1.0, 0.03, 0.5, 2, new Random(1), 3L, 1L, "random");
        VicsekSimulation simB = new VicsekSimulation(
                sharedInitial, lookupB, new VoterModel(), "voter",
                1.0, 0.03, 0.5, 2, new Random(2), 3L, 2L, "random");

        Path outputA = tempDir.resolve("a.txt");
        Path outputB = tempDir.resolve("b.txt");
        simA.run(outputA);
        simB.run(outputB);

        List<String> linesA = Files.readAllLines(outputA);
        List<String> linesB = Files.readAllLines(outputB);

        List<String> t0BlockA = extractBlock(linesA, "t=0");
        List<String> t0BlockB = extractBlock(linesB, "t=0");
        assertEquals(t0BlockA, t0BlockB);

        List<String> t1BlockA = extractBlock(linesA, "t=1");
        List<String> t1BlockB = extractBlock(linesB, "t=1");
        assertNotEquals(t1BlockA, t1BlockB);
    }

    private static void runFreshSimulation(Path output, int n, int steps, long seedIC, long seedLoop) throws IOException {
        double l = 10.0;
        List<VicsekParticle> initial = InitialConditionGenerator.generate(n, l, new Random(seedIC));
        NeighborLookup lookup = new NeighborLookup(new BruteForceNeighborFinder(), l, 1.0, true);
        VicsekSimulation simulation = new VicsekSimulation(
                initial, lookup, new VoterModel(), "voter",
                1.0, 0.03, 0.5, steps, new Random(seedLoop), seedIC, seedLoop, "random");
        simulation.run(output);
    }

    private static Map<String, String> parseHeader(String headerLine) {
        Map<String, String> fields = new HashMap<>();
        for (String token : headerLine.split(" ")) {
            String[] kv = token.split("=", 2);
            fields.put(kv[0], kv[1]);
        }
        return fields;
    }

    private static List<String> extractBlock(List<String> lines, String marker) {
        int start = lines.indexOf(marker) + 1;
        int end = start;
        while (end < lines.size() && !lines.get(end).startsWith("t=")) {
            end++;
        }
        return lines.subList(start, end);
    }
}