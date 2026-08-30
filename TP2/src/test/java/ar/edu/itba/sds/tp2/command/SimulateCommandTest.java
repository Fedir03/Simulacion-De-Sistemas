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

    @Test
    void theta0KeepsInitialPositionsAndAlignsAngles(@TempDir Path tempDir) throws IOException {
        Path randomOut = tempDir.resolve("random.txt");
        Path alignedOut = tempDir.resolve("aligned.txt");

        new SimulateCommand().execute(theta0Args(randomOut, "random"));
        new SimulateCommand().execute(theta0Args(alignedOut, "0"));

        List<String> randomBlock = firstBlock(Files.readAllLines(randomOut));
        List<String> alignedBlock = firstBlock(Files.readAllLines(alignedOut));
        assertEquals(randomBlock.size(), alignedBlock.size());

        for (int i = 0; i < randomBlock.size(); i++) {
            String[] randomFields = randomBlock.get(i).split(" ");
            String[] alignedFields = alignedBlock.get(i).split(" ");
            assertEquals(randomFields[0], alignedFields[0], "id");
            assertEquals(randomFields[1], alignedFields[1], "x debe ser identico");
            assertEquals(randomFields[2], alignedFields[2], "y debe ser identico");
            assertEquals(0.0, Double.parseDouble(alignedFields[3]));
        }
    }

    @Test
    void headerRecordsTheta0(@TempDir Path tempDir) throws IOException {
        Path out = tempDir.resolve("output.txt");
        new SimulateCommand().execute(theta0Args(out, "1.25"));

        assertTrue(Files.readAllLines(out).get(0).contains("theta0=1.25"));
    }

    @Test
    void invalidTheta0ThrowsClearError(@TempDir Path tempDir) {
        String[] args = theta0Args(tempDir.resolve("output.txt"), "nonsense");

        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class,
                () -> new SimulateCommand().execute(args));

        assertTrue(exception.getMessage().contains("theta0"),
                "mensaje inesperado: " + exception.getMessage());
    }

    private static String[] theta0Args(Path out, String theta0) {
        return new String[]{
                "--model=standard",
                "--n=8",
                "--eta=0.5",
                "--steps=1",
                "--out=" + out,
                "--seedIC=1",
                "--seedLoop=2",
                "--theta0=" + theta0
        };
    }

    private static List<String> firstBlock(List<String> lines) {
        int start = lines.indexOf("t=0") + 1;
        int end = start;
        while (end < lines.size() && !lines.get(end).startsWith("t=")) {
            end++;
        }
        return lines.subList(start, end);
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