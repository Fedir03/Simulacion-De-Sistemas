package ar.edu.itba.sds.tp1.command;

import java.util.Arrays;
import java.util.Locale;

/** Utilidades compartidas por los comandos benchmark-m y benchmark-n: parseo de args y estadística. */
final class BenchmarkSupport {

    private BenchmarkSupport() {
    }

    record BenchmarkStats(double meanMs, double stdDevMs) {
        static BenchmarkStats of(double[] samplesMs) {
            double mean = Arrays.stream(samplesMs).average().orElse(0.0);
            double variance = samplesMs.length > 1
                    ? Arrays.stream(samplesMs).map(v -> (v - mean) * (v - mean)).sum() / (samplesMs.length - 1)
                    : 0.0;
            return new BenchmarkStats(mean, Math.sqrt(variance));
        }
    }

    static String formatMs(double value) {
        return String.format(Locale.US, "%.6f", value);
    }

    static int parseInt(String label, String value) {
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("valor entero invalido para " + label + ": " + value);
        }
    }

    static double parseDouble(String label, String value) {
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("valor numerico invalido para " + label + ": " + value);
        }
    }

    static long parseLong(String label, String value) {
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("valor entero invalido para " + label + ": " + value);
        }
    }

    static boolean parseBoolean(String label, String value) {
        if (value.equalsIgnoreCase("true")) {
            return true;
        }
        if (value.equalsIgnoreCase("false")) {
            return false;
        }
        throw new IllegalArgumentException(
                "valor booleano invalido para " + label + ": " + value + " (se espera 'true' o 'false')");
    }
}
