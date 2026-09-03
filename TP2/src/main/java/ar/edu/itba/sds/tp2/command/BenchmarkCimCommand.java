package ar.edu.itba.sds.tp2.command;

import ar.edu.itba.sds.tp1.CellIndexMethod;
import ar.edu.itba.sds.tp2.analysis.Frame;
import ar.edu.itba.sds.tp2.analysis.RunHeader;
import ar.edu.itba.sds.tp2.analysis.SimulationReader;
import ar.edu.itba.sds.tp2.engine.NeighborLookup;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Mide cuanto tarda el Cell Index Method dentro de las simulaciones de TP2 (punto g).
 * Uso: java -jar target/tp2.jar benchmark-cim --in=&lt;a.txt,b.txt,...&gt; --out=&lt;csv&gt; [--warmup=50]
 *
 * <p>Cronometra {@code findNeighbors} sobre cada cuadro de una corrida ya hecha, o sea sobre
 * las configuraciones que realmente aparecen en la simulacion (agrupadas), no sobre
 * posiciones uniformes al azar como en el benchmark de TP1. Esa es justamente la
 * comparacion que pide el enunciado.
 *
 * <p>Emite el mismo esquema de CSV que `benchmark-n` de TP1 (N,L,M,meanMs,stdDevMs) para que
 * TP1/scripts/plot_benchmark.py pueda superponer las dos curvas sin cambios.
 */
public final class BenchmarkCimCommand implements Command {

    private static final int DEFAULT_WARMUP = 50;

    @Override
    public void execute(String[] args) throws IOException {
        Map<String, String> flags = CommandSupport.parseFlags(args);
        List<Path> inputs = parsePaths(CommandSupport.require(flags, "in"));
        Path out = Path.of(CommandSupport.require(flags, "out"));
        int warmup = CommandSupport.parseInt("warmup",
                CommandSupport.optional(flags, "warmup", String.valueOf(DEFAULT_WARMUP)));
        if (warmup < 0) {
            throw new IllegalArgumentException("warmup no puede ser negativo: " + warmup);
        }

        if (out.getParent() != null) {
            Files.createDirectories(out.getParent());
        }
        try (BufferedWriter writer = Files.newBufferedWriter(out)) {
            writer.write("N,L,M,meanMs,stdDevMs,frames");
            writer.newLine();
            for (Path input : inputs) {
                Measurement measurement = measure(input, warmup);
                writer.write(String.join(",",
                        String.valueOf(measurement.n),
                        format(measurement.l),
                        String.valueOf(measurement.m),
                        format(measurement.meanMs),
                        format(measurement.stdDevMs),
                        String.valueOf(measurement.frames)));
                writer.newLine();
                System.out.printf("  N=%-6d L=%-9s M=%-4d %8s ms +/- %-8s (%d cuadros)%n",
                        measurement.n, format(measurement.l), measurement.m,
                        format(measurement.meanMs), format(measurement.stdDevMs), measurement.frames);
            }
        }
        System.out.printf("benchmark-cim: %d corridas medidas (warmup=%d) output=%s%n",
                inputs.size(), warmup, out.toAbsolutePath());
    }

    private record Measurement(int n, double l, int m, double meanMs, double stdDevMs, int frames) {}

    private static Measurement measure(Path input, int warmup) throws IOException {
        List<Double> timesMs = new ArrayList<>();
        int m;
        RunHeader header;
        try (SimulationReader reader = SimulationReader.open(input)) {
            header = reader.header();
            m = CellIndexMethod.maxValidM(header.l(), header.rc(), 0.0);
            NeighborLookup lookup = new NeighborLookup(
                    new CellIndexMethod(m), header.l(), header.rc(), header.periodic());

            int index = 0;
            Frame frame;
            while ((frame = reader.next()) != null) {
                // las primeras llamadas miden el JIT calentando, no el algoritmo
                long start = System.nanoTime();
                Map<Integer, ?> neighbors = lookup.findNeighbors(frame.particles());
                long elapsed = System.nanoTime() - start;
                if (neighbors.isEmpty()) {
                    throw new IllegalStateException("el CIM no devolvio vecinos para " + input);
                }
                if (index++ >= warmup) {
                    timesMs.add(elapsed / 1_000_000.0);
                }
            }
        }
        if (timesMs.isEmpty()) {
            throw new IllegalArgumentException(input + ": no quedan cuadros despues del warmup de "
                    + warmup + "; usar una corrida mas larga o bajar --warmup");
        }

        double mean = timesMs.stream().mapToDouble(Double::doubleValue).average().orElseThrow();
        double variance = timesMs.size() < 2 ? 0.0
                : timesMs.stream().mapToDouble(t -> (t - mean) * (t - mean)).sum() / (timesMs.size() - 1);
        return new Measurement(header.n(), header.l(), m, mean, Math.sqrt(variance), timesMs.size());
    }

    private static List<Path> parsePaths(String value) {
        List<Path> paths = new ArrayList<>();
        for (String token : value.split(",")) {
            String trimmed = token.trim();
            if (!trimmed.isEmpty()) {
                paths.add(Path.of(trimmed));
            }
        }
        if (paths.isEmpty()) {
            throw new IllegalArgumentException("--in no puede estar vacio");
        }
        return paths;
    }

    private static String format(double value) {
        return String.format(java.util.Locale.ROOT, "%.6f", value);
    }
}
