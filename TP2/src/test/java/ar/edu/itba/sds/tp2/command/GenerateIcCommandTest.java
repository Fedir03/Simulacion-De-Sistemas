package ar.edu.itba.sds.tp2.command;

import ar.edu.itba.sds.tp2.engine.InitialConditionFile;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;

class GenerateIcCommandTest {

    @Test
    void writesFileReadableByInitialConditionFile(@TempDir Path tempDir) throws IOException {
        Path out = tempDir.resolve("ic.txt");
        String[] args = {
                "--n=6",
                "--l=12.5",
                "--seedIC=7",
                "--out=" + out
        };

        new GenerateIcCommand().execute(args);

        InitialConditionFile.Data data = InitialConditionFile.read(out);
        assertEquals(6, data.n());
        assertEquals(12.5, data.l());
        assertEquals(7L, data.seedIC());
        assertEquals(6, data.particles().size());
    }

    @Test
    void defaultsLTo10(@TempDir Path tempDir) throws IOException {
        Path out = tempDir.resolve("ic.txt");
        String[] args = {
                "--n=3",
                "--seedIC=1",
                "--out=" + out
        };

        new GenerateIcCommand().execute(args);

        assertEquals(10.0, InitialConditionFile.read(out).l());
    }
}
