package ar.edu.itba.sds.tp1.command;

import ar.edu.itba.sds.tp1.CellIndexMethod;
import ar.edu.itba.sds.tp1.Particle;
import ar.edu.itba.sds.tp1.ParticleGenerator;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Mide el tiempo de Cell Index Method con la M optima para cada N, en densidad libre (L fijo)
 * o densidad fija (L = l0 * sqrt(N / N0)).
 * Usage: java -jar target/tp1.jar benchmark-n l0 radiusMin radiusMax rc periodic modo repetitions seed outputCsv Ns
 */
public final class BenchmarkNCommand implements Command {
    private static final int EXPECTED_ARGS = 10;

    @Override
    public void execute(String[] args) throws IOException {
        if (args.length != EXPECTED_ARGS) {
            throw new IllegalArgumentException(
                    "benchmark-n espera " + EXPECTED_ARGS + " argumentos: "
                            + "l0 radiusMin radiusMax rc periodic modo repetitions seed outputCsv Ns");
        }

        double l0 = BenchmarkSupport.parseDouble("l0", args[0]);
        double radiusMin = BenchmarkSupport.parseDouble("radiusMin", args[1]);
        double radiusMax = BenchmarkSupport.parseDouble("radiusMax", args[2]);
        double rc = BenchmarkSupport.parseDouble("rc", args[3]);
        boolean periodic = BenchmarkSupport.parseBoolean("periodic", args[4]);
        String modo = args[5];
        if (!modo.equals("libre") && !modo.equals("fija")) {
            throw new IllegalArgumentException("modo invalido: " + modo + " (se espera 'libre' o 'fija')");
        }
        int repetitions = BenchmarkSupport.parseInt("repetitions", args[6]);
        long seed = BenchmarkSupport.parseLong("seed", args[7]);
        Path outputCsv = Path.of(args[8]);
        List<Integer> ns = parseNs(args[9]);

        int n0 = ns.get(0);

        try (BufferedWriter writer = Files.newBufferedWriter(outputCsv)) {
            writer.write("N,L,M,meanMs,stdDevMs");
            writer.newLine();

            for (int n : ns) {
                double l = modo.equals("fija") ? l0 * Math.sqrt(n / (double) n0) : l0;
                int m = CellIndexMethod.maxValidM(l, rc, radiusMax);

                double[] timesMs = new double[repetitions];
                for (int r = 0; r < repetitions; r++) {
                    List<Particle> particles = new ParticleGenerator(seed + r, radiusMin, radiusMax).generate(n, l);
                    CellIndexMethod cim = new CellIndexMethod(m);
                    timesMs[r] = timeMs(() -> cim.findNeighbors(particles, l, rc, periodic));
                }

                BenchmarkSupport.BenchmarkStats stats = BenchmarkSupport.BenchmarkStats.of(timesMs);
                writer.write(String.join(",", String.valueOf(n), BenchmarkSupport.formatMs(l), String.valueOf(m),
                        BenchmarkSupport.formatMs(stats.meanMs()), BenchmarkSupport.formatMs(stats.stdDevMs())));
                writer.newLine();
            }
        }

        System.out.printf("benchmark-n: modo=%s puntos=%d repeticiones=%d output=%s%n",
                modo, ns.size(), repetitions, outputCsv);
    }

    private static List<Integer> parseNs(String value) {
        String[] parts = value.split(",");
        List<Integer> ns = new ArrayList<>(parts.length);
        for (String part : parts) {
            ns.add(BenchmarkSupport.parseInt("Ns", part.trim()));
        }
        if (ns.isEmpty()) {
            throw new IllegalArgumentException("Ns no puede estar vacio");
        }
        return ns;
    }

    private static double timeMs(Runnable action) {
        long start = System.nanoTime();
        action.run();
        return (System.nanoTime() - start) / 1_000_000.0;
    }
}
