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

class SimulateCommandTest {

    @Test
    void validStandardRunProducesExpectedOutputFile(@TempDir Path tempDir) throws IOException {
        Path out = tempDir.resolve("output.txt");
        int steps = 2;
        String[] args = {
                "--model=standard",
                "--n=4",
                "--eta=0.5",
                "--steps=" + steps,
                "--out=" + out,
                "--seedIC=1",
                "--seedLoop=2"
        };

        new SimulateCommand().execute(args);

        List<String> lines = Files.readAllLines(out);
        long blockCount = lines.stream().filter(line -> line.startsWith("t=")).count();
        assertEquals(steps + 1, blockCount);
        assertTrue(lines.get(0).startsWith("model=standard"));
    }

    @Test
    void unknownModelThrowsClearError(@TempDir Path tempDir) {
        String[] args = baseArgs(tempDir, "nonsense");

        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class,
                () -> new SimulateCommand().execute(args));

        assertTrue(exception.getMessage().contains("Modelo desconocido: 'nonsense'"),
                "mensaje inesperado: " + exception.getMessage());
    }

    @Test
    void validVoterRunProducesExpectedOutputFile(@TempDir Path tempDir) throws IOException {
        Path out = tempDir.resolve("output.txt");
        int steps = 2;
        String[] args = {
                "--model=voter",
                "--n=4",
                "--eta=0.5",
                "--steps=" + steps,
                "--out=" + out,
                "--seedIC=1",
                "--seedLoop=2"
        };

        new SimulateCommand().execute(args);

        List<String> lines = Files.readAllLines(out);
        long blockCount = lines.stream().filter(line -> line.startsWith("t=")).count();
        assertEquals(steps + 1, blockCount);
        assertTrue(lines.get(0).startsWith("model=voter"));
    }

    @Test
    void missingRequiredFlagThrowsClearError(@TempDir Path tempDir) {
        String[] args = {
                "--n=4",
                "--eta=0.5",
                "--steps=1",
                "--out=" + tempDir.resolve("output.txt"),
                "--seedIC=1",
                "--seedLoop=2"
        }; // falta --model

        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class,
                () -> new SimulateCommand().execute(args));

        assertTrue(exception.getMessage().contains("--model"),
                "mensaje inesperado: " + exception.getMessage());
    }

    @Test
    void strictPeriodicParsingRejectsInvalidLiteral(@TempDir Path tempDir) {
        Path out = tempDir.resolve("output.txt");
        String[] args = {
                "--model=voter",
                "--n=4",
                "--eta=0.5",
                "--steps=1",
                "--out=" + out,
                "--seedIC=1",
                "--seedLoop=2",
                "--periodic=yes"
        };

        assertThrows(IllegalArgumentException.class, () -> new SimulateCommand().execute(args));
    }

    private static String[] baseArgs(Path tempDir, String model) {
        return new String[]{
                "--model=" + model,
                "--n=4",
                "--eta=0.5",
                "--steps=1",
                "--out=" + tempDir.resolve("output.txt"),
                "--seedIC=1",
                "--seedLoop=2"
        };
    }
}