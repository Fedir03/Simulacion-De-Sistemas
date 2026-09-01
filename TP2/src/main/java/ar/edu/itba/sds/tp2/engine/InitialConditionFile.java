package ar.edu.itba.sds.tp2.engine;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Lee y escribe una condición inicial (posiciones + ángulos) a un archivo de texto, para que
 * varias corridas de {@code simulate} puedan arrancar del mismo estado exacto sin depender de
 * que dos generaciones separadas a partir del mismo seedIC coincidan bit a bit.
 *
 * <p>Formato: una cabecera {@code N=<n> L=<l> seedIC=<seedIC>}, seguida de {@code t=0} y N líneas
 * {@code id x y theta} — un subconjunto del formato que escribe {@link VicsekSimulation}, sin los
 * campos que no aplican todavía a una condición inicial suelta (model/rc/dt/v0/eta/seedLoop).
 */
public final class InitialConditionFile {

    private static final Set<String> REQUIRED_FIELDS = Set.of("N", "L", "seedIC");

    private InitialConditionFile() {
    }

    public record Data(int n, double l, long seedIC, List<VicsekParticle> particles) {
    }

    public static void write(Path out, int n, double l, long seedIC, List<VicsekParticle> particles)
            throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(out)) {
            writer.write("N=" + n + " L=" + l + " seedIC=" + seedIC);
            writer.newLine();
            writer.write("t=0");
            writer.newLine();
            for (VicsekParticle p : particles) {
                writer.write(p.id() + " " + p.x() + " " + p.y() + " " + p.theta());
                writer.newLine();
            }
        }
    }

    public static Data read(Path in) throws IOException {
        try (BufferedReader reader = Files.newBufferedReader(in, StandardCharsets.UTF_8)) {
            String headerLine = reader.readLine();
            if (headerLine == null) {
                throw new IllegalArgumentException(in + ": el archivo esta vacio");
            }
            Map<String, String> fields = parseHeaderTokens(headerLine);
            int n = parseInt("N", fields.get("N"));
            if (n <= 0) {
                throw new IllegalArgumentException("linea 1: N debe ser positivo");
            }
            double l = parseDouble("L", fields.get("L"));
            long seedIC = parseLong("seedIC", fields.get("seedIC"));

            String marker = reader.readLine();
            if (marker == null || !marker.trim().equals("t=0")) {
                throw new IllegalArgumentException(
                        "linea 2: se esperaba el marcador 't=0', se leyo: " + marker);
            }

            List<VicsekParticle> particles = new ArrayList<>(n);
            for (int i = 0; i < n; i++) {
                String line = reader.readLine();
                if (line == null) {
                    throw new IllegalArgumentException("se esperaban " + n
                            + " particulas y se encontraron " + i);
                }
                String[] parts = line.trim().split("\\s+");
                if (parts.length != 4) {
                    throw new IllegalArgumentException(
                            "linea " + (i + 3) + ": se esperaba 'id x y theta'");
                }
                particles.add(new VicsekParticle(
                        parseInt("id", parts[0]),
                        parseDouble("x", parts[1]),
                        parseDouble("y", parts[2]),
                        parseDouble("theta", parts[3])));
            }
            return new Data(n, l, seedIC, particles);
        }
    }

    private static Map<String, String> parseHeaderTokens(String line) {
        Map<String, String> fields = new HashMap<>();
        for (String token : line.replace("﻿", "").trim().split("\\s+")) {
            int eq = token.indexOf('=');
            if (eq <= 0 || eq == token.length() - 1) {
                throw new IllegalArgumentException("linea 1: campo de cabecera invalido: " + token);
            }
            fields.put(token.substring(0, eq), token.substring(eq + 1));
        }
        for (String required : REQUIRED_FIELDS) {
            if (!fields.containsKey(required)) {
                throw new IllegalArgumentException(
                        "linea 1: falta el campo obligatorio en la cabecera: " + required);
            }
        }
        return fields;
    }

    private static int parseInt(String field, String value) {
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("valor entero invalido para " + field + ": " + value);
        }
    }

    private static long parseLong(String field, String value) {
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("valor entero invalido para " + field + ": " + value);
        }
    }

    private static double parseDouble(String field, String value) {
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("valor numerico invalido para " + field + ": " + value);
        }
    }
}
