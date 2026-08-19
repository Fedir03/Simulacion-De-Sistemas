package ar.edu.itba.sds.tp2.command;

import java.util.HashMap;
import java.util.Map;

/** Utilidades compartidas por los comandos de TP2: parseo de flags --clave=valor. */
final class CommandSupport {

    private CommandSupport() {
    }

    static Map<String, String> parseFlags(String[] args) {
        Map<String, String> flags = new HashMap<>();
        for (String arg : args) {
            if (!arg.startsWith("--") || !arg.contains("=")) {
                throw new IllegalArgumentException("argumento invalido: " + arg + " (se espera --clave=valor)");
            }
            int eq = arg.indexOf('=');
            String key = arg.substring(2, eq);
            String value = arg.substring(eq + 1);
            flags.put(key, value);
        }
        return flags;
    }

    static String require(Map<String, String> flags, String key) {
        String value = flags.get(key);
        if (value == null) {
            throw new IllegalArgumentException("falta el flag obligatorio --" + key);
        }
        return value;
    }

    static String optional(Map<String, String> flags, String key, String defaultValue) {
        return flags.getOrDefault(key, defaultValue);
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

    static long resolveSeed(String value) {
        if (value.equalsIgnoreCase("auto")) {
            return System.nanoTime();
        }
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("semilla invalida: " + value + " (se espera un entero o 'auto')");
        }
    }
}