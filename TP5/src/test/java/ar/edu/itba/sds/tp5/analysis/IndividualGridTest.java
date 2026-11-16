package ar.edu.itba.sds.tp5.analysis;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;

class IndividualGridTest {
    @TempDir Path out;

    @Test void selectedEventMatchesFullGridExactly() throws Exception {
        Path full = out.resolve("full.txt"), selected = out.resolve("selected.txt");
        AnalysisMain.execute(new String[] {"grid", "--layer", "a", "--p1-values", "2,3",
                "--p2-values", "0.5", "--out", full.toString()});
        AnalysisMain.execute(new String[] {"grid", "--layer", "a", "--p1-values", "2,3",
                "--p2-values", "0.5", "--event", "3", "--out", selected.toString()});
        List<String> expected = Files.readAllLines(full).stream().filter(s -> !s.startsWith("#"))
                .filter(s -> s.split(" ")[2].equals("3")).toList();
        List<String> actual = Files.readAllLines(selected).stream().filter(s -> !s.startsWith("#")).toList();
        assertEquals(2, actual.size());
        assertEquals(expected, actual);
    }

    @Test void rejectsMissingEvent() {
        assertThrows(IllegalArgumentException.class, () -> AnalysisMain.execute(new String[] {
                "grid", "--layer", "a", "--p1-values", "3", "--p2-values", "0.5",
                "--event", "999", "--out", out.resolve("missing.txt").toString()}));
    }

    @Test void explicitPairsDoNotGenerateCartesianCombinations() throws Exception {
        Path pairs = out.resolve("pairs.txt"), selected = out.resolve("selected.txt");
        Files.writeString(pairs, "# p1 p2\n2 0.4\n3 0.5\n");
        AnalysisMain.execute(new String[] {"grid", "--layer", "a", "--pairs-file", pairs.toString(),
                "--event", "3", "--out", selected.toString()});
        List<String[]> rows = Files.readAllLines(selected).stream().filter(s -> !s.startsWith("#"))
                .map(s -> s.split(" ")).toList();
        assertEquals(2, rows.size());
        assertEquals(List.of("2.0 0.4", "3.0 0.5"), rows.stream().map(r -> r[0]+" "+r[1]).toList());
    }
}
