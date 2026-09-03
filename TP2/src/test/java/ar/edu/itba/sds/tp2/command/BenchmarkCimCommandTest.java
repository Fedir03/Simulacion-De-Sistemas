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

class BenchmarkCimCommandTest {

    private static Path runFile(Path dir, String name, int n, int steps) throws IOException {
        StringBuilder contents = new StringBuilder(
                "model=standard N=" + n + " L=10.0 rc=1.0 dt=1.0 v0=0.03 eta=0.5 "
                        + "periodic=true seedIC=1 seedLoop=2 theta0=random\n");
        for (int t = 0; t <= steps; t++) {
            contents.append("t=").append(t).append('\n');
            for (int id = 1; id <= n; id++) {
                contents.append(id).append(' ').append(id * 0.3 % 10).append(" 5.0 0.0\n");
            }
        }
        Path path = dir.resolve(name);
        Files.writeString(path, contents.toString());
        return path;
    }

    @Test
    void writesOneRowPerInputWithTp1Schema(@TempDir Path tempDir) throws IOException {
        Path a = runFile(tempDir, "a.txt", 10, 20);
        Path b = runFile(tempDir, "b.txt", 20, 20);
        Path out = tempDir.resolve("bench.csv");

        new BenchmarkCimCommand().execute(new String[]{
                "--in=" + a + "," + b, "--out=" + out, "--warmup=0"});

        List<String> lines = Files.readAllLines(out);
        assertEquals("N,L,M,meanMs,stdDevMs,frames", lines.get(0));
        assertEquals(3, lines.size());
        assertTrue(lines.get(1).startsWith("10,"), lines.get(1));
        assertTrue(lines.get(2).startsWith("20,"), lines.get(2));
    }

    @Test
    void warmupDiscardsTheFirstFrames(@TempDir Path tempDir) throws IOException {
        Path in = runFile(tempDir, "a.txt", 5, 20);   // 21 cuadros
        Path out = tempDir.resolve("bench.csv");

        new BenchmarkCimCommand().execute(new String[]{
                "--in=" + in, "--out=" + out, "--warmup=15"});

        String row = Files.readAllLines(out).get(1);
        assertEquals("6", row.split(",")[5], "deberian quedar 21-15=6 cuadros medidos");
    }

    @Test
    void rejectsAWarmupLongerThanTheRun(@TempDir Path tempDir) throws IOException {
        Path in = runFile(tempDir, "a.txt", 5, 5);
        String[] args = {"--in=" + in, "--out=" + tempDir.resolve("bench.csv"), "--warmup=999"};

        IllegalArgumentException error = assertThrows(IllegalArgumentException.class,
                () -> new BenchmarkCimCommand().execute(args));
        assertTrue(error.getMessage().contains("warmup"), error.getMessage());
    }

    @Test
    void reportsPositiveTimes(@TempDir Path tempDir) throws IOException {
        Path in = runFile(tempDir, "a.txt", 50, 30);
        Path out = tempDir.resolve("bench.csv");

        new BenchmarkCimCommand().execute(new String[]{"--in=" + in, "--out=" + out, "--warmup=5"});

        String[] row = Files.readAllLines(out).get(1).split(",");
        assertTrue(Double.parseDouble(row[3]) > 0, "el tiempo medio debe ser positivo: " + row[3]);
        assertTrue(Double.parseDouble(row[4]) >= 0, "el desvio no puede ser negativo: " + row[4]);
    }
}
