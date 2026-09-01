package ar.edu.itba.sds.tp2.command;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ClustersCommandTest {

    private static Path runFile(Path dir, int steps, String particles) throws IOException {
        StringBuilder contents = new StringBuilder(
                "model=standard N=2 L=10.0 rc=1.0 dt=1.0 v0=0.03 eta=0.5 "
                        + "periodic=true seedIC=1 seedLoop=2 theta0=random\n");
        for (int t = 0; t <= steps; t++) {
            contents.append("t=").append(t).append('\n').append(particles);
        }
        Path path = dir.resolve("corrida.txt");
        Files.writeString(path, contents.toString());
        return path;
    }

    @Test
    void writesOneRowPerFrameWithHeaderAndColumns(@TempDir Path tempDir) throws IOException {
        Path in = runFile(tempDir, 2, "1 5.0 5.0 0.0\n2 5.5 5.0 0.0\n");
        Path out = tempDir.resolve("S.csv");

        new ClustersCommand().execute(new String[]{"--in=" + in, "--out=" + out});

        List<String> lines = Files.readAllLines(out);
        assertTrue(lines.get(0).startsWith("# model=standard"), lines.get(0));
        assertEquals("t,S", lines.get(1));
        assertEquals(3, lines.size() - 2);
        // las dos particulas estan a 0.5 < rc: un solo cluster, S = 1
        assertEquals("0,1.0", lines.get(2));
    }

    @Test
    void separatedParticlesGiveSOneOverN(@TempDir Path tempDir) throws IOException {
        Path in = runFile(tempDir, 0, "1 1.0 1.0 0.0\n2 6.0 6.0 0.0\n");
        Path out = tempDir.resolve("S.csv");

        new ClustersCommand().execute(new String[]{"--in=" + in, "--out=" + out});

        assertEquals("0,0.5", Files.readAllLines(out).get(2));
    }

    @Test
    void strideKeepsOnlyMultiplesOfTheStep(@TempDir Path tempDir) throws IOException {
        Path in = runFile(tempDir, 20, "1 5.0 5.0 0.0\n2 5.5 5.0 0.0\n");
        Path out = tempDir.resolve("S.csv");

        new ClustersCommand().execute(new String[]{"--in=" + in, "--out=" + out, "--stride=5"});

        List<String> steps = Files.readAllLines(out).stream()
                .filter(line -> !line.startsWith("#") && !line.equals("t,S"))
                .map(line -> line.split(",")[0])
                .toList();
        assertEquals(List.of("0", "5", "10", "15", "20"), steps);
    }

    @Test
    void rejectsANonPositiveStride(@TempDir Path tempDir) throws IOException {
        Path in = runFile(tempDir, 1, "1 5.0 5.0 0.0\n2 5.5 5.0 0.0\n");
        String[] args = {"--in=" + in, "--out=" + tempDir.resolve("S.csv"), "--stride=0"};

        assertThrows(IllegalArgumentException.class, () -> new ClustersCommand().execute(args));
    }

    @Test
    void missingRequiredFlagThrowsClearError(@TempDir Path tempDir) throws IOException {
        Path in = runFile(tempDir, 1, "1 5.0 5.0 0.0\n2 5.5 5.0 0.0\n");
        String[] args = {"--in=" + in};

        IllegalArgumentException error = assertThrows(IllegalArgumentException.class,
                () -> new ClustersCommand().execute(args));
        assertTrue(error.getMessage().contains("--out"), error.getMessage());
    }
}
