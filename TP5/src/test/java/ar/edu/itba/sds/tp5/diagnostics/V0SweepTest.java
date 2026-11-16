package ar.edu.itba.sds.tp5.diagnostics;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertEquals;

import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class V0SweepTest {
    @Test
    void onlySpeedsAboveDesiredAreInvalid() {
        assertTrue(V0Sweep.exceedsDesired(1.01, 1.0));
        assertFalse(V0Sweep.exceedsDesired(0.99, 1.0));
        assertFalse(V0Sweep.exceedsDesired(1.0, 1.0));
        assertFalse(V0Sweep.exceedsDesired(1.0 + 1e-12, 1.0));
    }

    @Test
    void continuesPastContactsAndSpeedCrossingsAndRecordsValidity(@TempDir Path out) throws Exception {
        V0Sweep.main(new String[] { "--out", out.toString(), "--max", "5" });
        var rows = Files.readAllLines(out.resolve("sweep.csv"));
        assertEquals(9, rows.size()); // cabecera + 2, 3, 4 y 5 cuadros para A y B
        for (String row : rows.subList(1, rows.size())) {
            String[] fields = row.split(",", -1);
            assertTrue(fields[1].equals("A") || fields[1].equals("B"));
            assertEquals(fields[6].isEmpty() && fields[7].isEmpty(), Boolean.parseBoolean(fields[8]));
        }
        assertTrue(rows.get(1).split(",", -1)[6].contains("18"));
        assertEquals("false", rows.get(1).split(",", -1)[8]);
        assertTrue(rows.get(7).startsWith("5,A,"));
        assertTrue(rows.get(8).startsWith("5,B,"));
        assertTrue(Files.exists(out.resolve("B/v0_5/ecm.txt")));
    }
}
