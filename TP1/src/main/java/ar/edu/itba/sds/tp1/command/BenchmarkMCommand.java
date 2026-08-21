package ar.edu.itba.sds.tp1.command;

import ar.edu.itba.sds.tp1.BruteForceNeighborFinder;
import ar.edu.itba.sds.tp1.CellIndexMethod;
import ar.edu.itba.sds.tp1.Particle;
import ar.edu.itba.sds.tp1.ParticleGenerator;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Compara fuerza bruta vs Cell Index Method para N fijo, barriendo M desde 2 hasta la M maxima valida.
 * Usage: java -jar target/tp1.jar benchmark-m n l radiusMin radiusMax rc periodic repetitions seed outputCsv
 */
public final class BenchmarkMCommand implements Command {
    private static final int EXPECTED_ARGS = 9;

    @Override
    public void execute(String[] args) throws IOException {
        if (args.length != EXPECTED_ARGS) {
            throw new IllegalArgumentException(
                    "benchmark-m espera " + EXPECTED_ARGS + " argumentos: "
                            + "n l radiusMin radiusMax rc periodic repetitions seed outputCsv");
        }

        int n = BenchmarkSupport.parseInt("n", args[0]);
        double l = BenchmarkSupport.parseDouble("l", args[1]);
        double radiusMin = BenchmarkSupport.parseDouble("radiusMin", args[2]);
        double radiusMax = BenchmarkSupport.parseDouble("radiusMax", args[3]);
        double rc = BenchmarkSupport.parseDouble("rc", args[4]);
        boolean periodic = BenchmarkSupport.parseBoolean("periodic", args[5]);
        int repetitions = BenchmarkSupport.parseInt("repetitions", args[6]);
        long seed = BenchmarkSupport.parseLong("seed", args[7]);
        Path outputCsv = Path.of(args[8]);

        int maxM = CellIndexMethod.maxValidM(l, rc, radiusMax);
        if (maxM < 2) {
            throw new IllegalArgumentException(
                    "No hay ninguna M >= 2 valida para N/L/rc dados (maxM=" + maxM
                            + "); ajustar N, L o rc.");
        }

        double[] bruteTimesMs = new double[repetitions];
        Map<Integer, double[]> cimTimesMsByM = new LinkedHashMap<>();
        for (int m = 2; m <= maxM; m++) {
            cimTimesMsByM.put(m, new double[repetitions]);
        }

        BruteForceNeighborFinder bruteForce = new BruteForceNeighborFinder();
        for (int r = 0; r < repetitions; r++) {
            List<Particle> particles = new ParticleGenerator(seed + r, radiusMin, radiusMax).generate(n, l);

            bruteTimesMs[r] = timeMs(() -> bruteForce.findNeighbors(particles, l, rc, periodic));

            for (int m = 2; m <= maxM; m++) {
                CellIndexMethod cim = new CellIndexMethod(m);
                cimTimesMsByM.get(m)[r] = timeMs(() -> cim.findNeighbors(particles, l, rc, periodic));
            }
        }

        writeCsv(outputCsv, n, bruteTimesMs, cimTimesMsByM);

        System.out.printf("benchmark-m: N=%d L=%s rc=%s repeticiones=%d M=[2,%d] output=%s%n",
                n, l, rc, repetitions, maxM, outputCsv);
    }

    private static double timeMs(Runnable action) {
        long start = System.nanoTime();
        action.run();
        return (System.nanoTime() - start) / 1_000_000.0;
    }

    private static void writeCsv(
            Path outputCsv, int n, double[] bruteTimesMs, Map<Integer, double[]> cimTimesMsByM) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(outputCsv)) {
            writer.write("method,M,N,meanMs,stdDevMs");
            writer.newLine();

            BenchmarkSupport.BenchmarkStats bruteStats = BenchmarkSupport.BenchmarkStats.of(bruteTimesMs);
            writer.write(String.join(",", "brute", "1", String.valueOf(n),
                    BenchmarkSupport.formatMs(bruteStats.meanMs()), BenchmarkSupport.formatMs(bruteStats.stdDevMs())));
            writer.newLine();

            for (Map.Entry<Integer, double[]> entry : cimTimesMsByM.entrySet()) {
                BenchmarkSupport.BenchmarkStats cimStats = BenchmarkSupport.BenchmarkStats.of(entry.getValue());
                writer.write(String.join(",", "cim", String.valueOf(entry.getKey()), String.valueOf(n),
                        BenchmarkSupport.formatMs(cimStats.meanMs()), BenchmarkSupport.formatMs(cimStats.stdDevMs())));
                writer.newLine();
            }
        }
    }
}
