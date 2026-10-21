package ar.edu.itba.sds.tp4.io;

import ar.edu.itba.sds.tp4.Main;
import ar.edu.itba.sds.tp4.engine.billiard.BilliardSimulator;
import ar.edu.itba.sds.tp4.models.BilliardConfig;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class BilliardFilesTest {
    @TempDir Path temp;

    private Path run(String name, String... options) throws IOException {
        Path dir = temp.resolve(name);
        String[] args = new String[options.length + 3];
        args[0] = "billiard";
        System.arraycopy(options, 0, args, 1, options.length);
        args[args.length - 2] = "--out";
        args[args.length - 1] = dir.toString();
        Main.execute(args);
        return dir;
    }

    private static List<String> lines(Path file) throws IOException { return Files.readAllLines(file); }

    private static List<String> data(Path file) throws IOException {
        return lines(file).stream().filter(l -> !l.startsWith("#")).toList();
    }

    /** Todo menos el pie, que trae el tiempo de ejecución. */
    private static List<String> withoutFooter(Path file) throws IOException {
        List<String> l = lines(file);
        assertTrue(l.getLast().startsWith("# fin "), l.getLast());
        return l.subList(0, l.size() - 1);
    }

    @Test void observablesHaveHeaderOneRowPerDt2AndFooter() throws IOException {
        Path dir = run("a", "--n", "50", "--seed", "3", "--x0", "0.24", "--tf", "1");
        assertFalse(Files.exists(dir.resolve(BilliardFiles.DYNAMIC)));
        List<String> all = lines(dir.resolve(BilliardFiles.OBSERVABLES));
        assertTrue(all.getFirst().startsWith("# format=tp4-billiard-v1 N=50 seed=3 x0=0.24 dt=1.0E-4 dt2=0.04 tf=1.0"), all.getFirst());
        assertTrue(all.getFirst().endsWith("neighbors=cim M=29"));
        List<String> rows = data(dir.resolve(BilliardFiles.OBSERVABLES));
        assertEquals("t E_tot E_cin E_el Nu", rows.getFirst());
        assertEquals(26, rows.size() - 1); // t = 0, 0.04, ..., 1
        for (int i = 1; i < rows.size(); i++) {
            String[] c = rows.get(i).split(" ");
            assertEquals(5, c.length);
            assertEquals((i - 1) * 0.04, Double.parseDouble(c[0]), 1e-12);
            assertEquals(Double.parseDouble(c[1]), Double.parseDouble(c[2]) + Double.parseDouble(c[3]), 1e-15);
            Integer.parseInt(c[4]);
        }
        String[] first = rows.get(1).split(" ");
        assertEquals("0.000000000", first[0]);
        assertEquals(0.625, Double.parseDouble(first[1]), 1e-12); // 50 · ½ · 0.025 · 1², sin contactos en t = 0
        assertEquals("0.0", first[3]);
        assertEquals("0", first[4]);
        assertTrue(all.getLast().startsWith("# fin estado=completa t=1.000000000 pasos=10000 Nu="), all.getLast());
    }

    @Test void dynamicHasObstaclesAndNLinesPerFrame() throws IOException {
        Path dir = run("d", "--n", "20", "--x0", "0.3", "--tf", "0.2", "--dynamic", "yes");
        List<String> all = withoutFooter(dir.resolve(BilliardFiles.DYNAMIC));
        assertTrue(all.contains("# obstacle -0.3 0.0 0.0175"));
        assertTrue(all.contains("# obstacle 0.3 0.0 0.0175"));
        List<String> rows = all.stream().filter(l -> !l.startsWith("#")).toList();
        assertEquals(6 * 21, rows.size()); // 6 cuadros × (cabecera + 20 partículas)
        for (int f = 0; f < 6; f++) {
            assertTrue(rows.get(f * 21).startsWith("t=" + String.format(java.util.Locale.ROOT, "%.9f", f * 0.04) + " Nu="));
            for (int i = 1; i <= 20; i++) {
                String[] c = rows.get(f * 21 + i).split(" ");
                assertEquals(String.valueOf(i), c[0]);
                assertTrue(c[5].equals("0") || c[5].equals("1"));
                if (f == 0) assertEquals(1, Math.hypot(Double.parseDouble(c[3]), Double.parseDouble(c[4])), 1e-12);
            }
        }
    }

    @Test void sameSeedSameFilesOtherSeedOther() throws IOException {
        Path a = run("s1", "--n", "100", "--seed", "9", "--tf", "0.4", "--dynamic", "yes");
        Path b = run("s2", "--n", "100", "--seed", "9", "--tf", "0.4", "--dynamic", "yes");
        Path c = run("s3", "--n", "100", "--seed", "10", "--tf", "0.4");
        for (String f : List.of(BilliardFiles.OBSERVABLES, BilliardFiles.DYNAMIC))
            assertEquals(withoutFooter(a.resolve(f)), withoutFooter(b.resolve(f)), f);
        assertNotEquals(data(a.resolve(BilliardFiles.OBSERVABLES)), data(c.resolve(BilliardFiles.OBSERVABLES)));
    }

    @Test void longerRunReproducesShorterOneExactly() throws IOException {
        // 2.1.a (Q15): alargar un dt es volver a correrlo con tf mayor; los primeros cuadros tienen que ser idénticos
        Path shortRun = run("t1", "--n", "300", "--x0", "none", "--tf", "0.4", "--dynamic", "yes");
        Path longRun = run("t2", "--n", "300", "--x0", "none", "--tf", "0.8", "--dynamic", "yes");
        for (String f : List.of(BilliardFiles.OBSERVABLES, BilliardFiles.DYNAMIC)) {
            List<String> s = data(shortRun.resolve(f)), l = data(longRun.resolve(f));
            assertTrue(l.size() > s.size());
            assertEquals(s, l.subList(0, s.size()), f);
        }
    }

    @Test void divergenceIsWrittenInTheFooter() throws IOException {
        BilliardConfig c = BilliardConfig.of(1, 1, BilliardConfig.NO_OBSTACLES, 1e-2, 0.01, 1);
        BilliardSimulator sim = new BilliardSimulator(c, new double[]{0}, new double[]{0}, new double[]{100}, new double[]{0},
                BilliardSimulator.defaultFinder(c));
        Path dir = temp.resolve("div");
        try (BilliardFiles files = new BilliardFiles(dir, c, "cim", false)) {
            files.footer(sim.run(files), 0);
        }
        List<String> l = lines(dir.resolve(BilliardFiles.OBSERVABLES));
        assertEquals(2, data(dir.resolve(BilliardFiles.OBSERVABLES)).size()); // columnas + t = 0
        assertTrue(l.getLast().startsWith("# fin estado=divergio t=0.010000000 pasos=1 "), l.getLast());
    }

    @Test void invalidOptionsFailWithClearMessage() {
        assertThrows(IllegalArgumentException.class, () -> run("e1", "--dt", "3e-3"));
        assertThrows(IllegalArgumentException.class, () -> run("e2", "--x0", "0.6"));
        assertThrows(IllegalArgumentException.class, () -> run("e3", "--until", "t90"));
        assertThrows(IllegalArgumentException.class, () -> run("e4", "--dynamic", "si"));
        assertThrows(IllegalArgumentException.class, () -> run("e5", "--velocidad", "2"));
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class, () -> run("e6", "--n", "800"));
        assertTrue(e.getMessage().contains("N imposible"), e.getMessage());
    }
}
