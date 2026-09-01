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

    @Test
    void icFileGivesIdenticalT0AndDivergesFromT1AcrossModels(@TempDir Path tempDir) throws IOException {
        Path icFile = tempDir.resolve("ic.txt");
        new GenerateIcCommand().execute(new String[]{
                "--n=5", "--l=10.0", "--seedIC=3", "--out=" + icFile
        });

        Path standardOut = tempDir.resolve("standard.txt");
        Path voterOut = tempDir.resolve("voter.txt");
        new SimulateCommand().execute(new String[]{
                "--model=standard", "--icFile=" + icFile, "--eta=0.5", "--steps=2",
                "--out=" + standardOut, "--seedLoop=1"
        });
        new SimulateCommand().execute(new String[]{
                "--model=voter", "--icFile=" + icFile, "--eta=0.5", "--steps=2",
                "--out=" + voterOut, "--seedLoop=2"
        });

        List<String> standardLines = Files.readAllLines(standardOut);
        List<String> voterLines = Files.readAllLines(voterOut);
        assertEquals(firstBlock(standardLines), firstBlock(voterLines));

        List<String> standardT1 = block(standardLines, "t=1");
        List<String> voterT1 = block(voterLines, "t=1");
        assertTrue(!standardT1.equals(voterT1), "las corridas deberian divergir desde t=1");
    }

    @Test
    void icFileCombinedWithNThrowsClearError(@TempDir Path tempDir) throws IOException {
        Path icFile = tempDir.resolve("ic.txt");
        new GenerateIcCommand().execute(new String[]{
                "--n=4", "--seedIC=1", "--out=" + icFile
        });

        String[] args = {
                "--model=standard", "--icFile=" + icFile, "--n=4", "--eta=0.5", "--steps=1",
                "--out=" + tempDir.resolve("output.txt"), "--seedLoop=1"
        };

        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class,
                () -> new SimulateCommand().execute(args));

        assertTrue(exception.getMessage().contains("--icFile"),
                "mensaje inesperado: " + exception.getMessage());
    }

    @Test
    void icFileCombinedWithTheta0ThrowsClearError(@TempDir Path tempDir) throws IOException {
        Path icFile = tempDir.resolve("ic.txt");
        new GenerateIcCommand().execute(new String[]{
                "--n=4", "--seedIC=1", "--out=" + icFile
        });

        String[] args = {
                "--model=standard", "--icFile=" + icFile, "--theta0=0", "--eta=0.5", "--steps=1",
                "--out=" + tempDir.resolve("output.txt"), "--seedLoop=1"
        };

        assertThrows(IllegalArgumentException.class, () -> new SimulateCommand().execute(args));
    }

    private static List<String> block(List<String> lines, String marker) {
        int start = lines.indexOf(marker) + 1;
        int end = start;
        while (end < lines.size() && !lines.get(end).startsWith("t=")) {
            end++;
        }
        return lines.subList(start, end);
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