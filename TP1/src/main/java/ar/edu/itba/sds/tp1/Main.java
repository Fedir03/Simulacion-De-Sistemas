package ar.edu.itba.sds.tp1;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * Generates input files in the formats consumed by {@link InputReader}.
 * Usage: java -jar target/tp1.jar [N] [L] [seed] [output-directory]
 */
public final class Main {
    private static final int DEFAULT_N = 100;
    private static final double DEFAULT_L = 20.0;
    private static final long DEFAULT_SEED = 42L;

    private Main() {
    }

    public static void main(String[] args) {
        try {
            int n = args.length >= 1 ? Integer.parseInt(args[0]) : DEFAULT_N;
            double l = args.length >= 2 ? Double.parseDouble(args[1]) : DEFAULT_L;
            long seed = args.length >= 3 ? Long.parseLong(args[2]) : DEFAULT_SEED;
            Path outputDirectory = args.length >= 4 ? Path.of(args[3]) : Path.of("generated");

            if (args.length > 4) {
                printUsage();
                return;
            }

            List<Particle> particles = new ParticleGenerator(seed).generate(n, l);
            Files.createDirectories(outputDirectory);

            Path staticFile = outputDirectory.resolve("Static" + n + ".txt");
            Path dynamicFile = outputDirectory.resolve("Dynamic" + n + ".txt");
            writeStatic(staticFile, n, l, particles);
            writeDynamic(dynamicFile, particles);

            System.out.printf("Generadas %d partículas (L=%.2f, seed=%d).%n", n, l, seed);
            System.out.println("Static:  " + staticFile.toAbsolutePath());
            System.out.println("Dynamic: " + dynamicFile.toAbsolutePath());
        } catch (IllegalArgumentException | IllegalStateException e) {
            System.err.println("Error: " + e.getMessage());
            printUsage();
        } catch (IOException e) {
            System.err.println("No se pudieron escribir los archivos: " + e.getMessage());
        }
    }

    private static void writeStatic(Path file, int n, double l, List<Particle> particles) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(file)) {
            writer.write(n + "\n");
            writer.write(l + "\n");
            for (Particle particle : particles) {
                writer.write(particle.radius() + " 0\n");
            }
        }
    }

    private static void writeDynamic(Path file, List<Particle> particles) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(file)) {
            writer.write("0\n");
            for (Particle particle : particles) {
                writer.write(particle.x() + " " + particle.y() + "\n");
            }
        }
    }

    private static void printUsage() {
        System.err.println("Uso: java -jar target/tp1.jar [N] [L] [seed] [directorio-salida]");
    }
}
