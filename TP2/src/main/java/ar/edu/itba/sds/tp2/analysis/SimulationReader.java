package ar.edu.itba.sds.tp2.analysis;

import ar.edu.itba.sds.tp2.engine.VicsekParticle;

import java.io.BufferedReader;
import java.io.Closeable;
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
 * Lee en streaming el archivo de texto que escribe el motor (formato documentado en
 * TP2/README.md). Devuelve un cuadro por vez: nunca carga la trayectoria entera, que para
 * una corrida larga son millones de particulas.
 *
 * <p>Es la contraparte Java de stream_simulation() en TP2/scripts/simulation_io.py.
 */
public final class SimulationReader implements Closeable {

    private static final Set<String> REQUIRED_FIELDS = Set.of(
            "model", "N", "L", "rc", "dt", "v0", "eta", "periodic", "seedIC", "seedLoop");
    private static final String DEFAULT_THETA0 = "random";

    private final BufferedReader reader;
    private final RunHeader header;
    private int lineNumber;
    private int lastStep = -1;

    private SimulationReader(BufferedReader reader, RunHeader header, int lineNumber) {
        this.reader = reader;
        this.header = header;
        this.lineNumber = lineNumber;
    }

    public static SimulationReader open(Path path) throws IOException {
        BufferedReader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8);
        try {
            String first = reader.readLine();
            if (first == null) {
                throw new IllegalArgumentException(path + ": el archivo esta vacio");
            }
            return new SimulationReader(reader, parseHeader(first), 1);
        } catch (RuntimeException | IOException e) {
            reader.close();
            throw e;
        }
    }

    public RunHeader header() {
        return header;
    }

    /** Siguiente bloque de tiempo, o null si se termino el archivo. */
    public Frame next() throws IOException {
        String marker = nextNonBlankLine();
        if (marker == null) {
            return null;
        }
        if (!marker.startsWith("t=")) {
            throw new IllegalArgumentException(
                    "linea " + lineNumber + ": se esperaba un marcador t=<entero>, se leyo: " + marker);
        }
        int step = parseInt("t", marker.substring(2));
        if (step <= lastStep) {
            throw new IllegalArgumentException(
                    "linea " + lineNumber + ": los tiempos deben estar en orden creciente");
        }
        lastStep = step;

        List<VicsekParticle> particles = new ArrayList<>(header.n());
        for (int i = 0; i < header.n(); i++) {
            String line = reader.readLine();
            lineNumber++;
            if (line == null || line.startsWith("t=")) {
                throw new IllegalArgumentException("bloque t=" + step + ": se esperaban "
                        + header.n() + " particulas y se encontraron " + i);
            }
            String[] parts = line.trim().split("\\s+");
            if (parts.length != 4) {
                throw new IllegalArgumentException(
                        "linea " + lineNumber + ": se esperaba 'id x y theta'");
            }
            particles.add(new VicsekParticle(
                    parseInt("id", parts[0]),
                    parseDouble("x", parts[1]),
                    parseDouble("y", parts[2]),
                    parseDouble("theta", parts[3])));
        }
        return new Frame(step, particles);
    }

    private String nextNonBlankLine() throws IOException {
        String line;
        while ((line = reader.readLine()) != null) {
            lineNumber++;
            String trimmed = line.trim();
            if (!trimmed.isEmpty()) {
                return trimmed;
            }
        }
        return null;
    }

    static RunHeader parseHeader(String line) {
        Map<String, String> fields = new HashMap<>();
        // el motor puede escribir un BOM al principio del archivo
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

        int n = parseInt("N", fields.get("N"));
        if (n <= 0) {
            throw new IllegalArgumentException("linea 1: N debe ser positivo");
        }
        String periodic = fields.get("periodic").toLowerCase();
        if (!periodic.equals("true") && !periodic.equals("false")) {
            throw new IllegalArgumentException("linea 1: periodic debe ser true o false");
        }

        return new RunHeader(
                fields.get("model"),
                n,
                parseDouble("L", fields.get("L")),
                parseDouble("rc", fields.get("rc")),
                parseDouble("dt", fields.get("dt")),
                parseDouble("v0", fields.get("v0")),
                parseDouble("eta", fields.get("eta")),
                periodic.equals("true"),
                parseLong("seedIC", fields.get("seedIC")),
                parseLong("seedLoop", fields.get("seedLoop")),
                // theta0 es opcional: las corridas anteriores al flag --theta0 no lo traen
                fields.getOrDefault("theta0", DEFAULT_THETA0));
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

    @Override
    public void close() throws IOException {
        reader.close();
    }
}
