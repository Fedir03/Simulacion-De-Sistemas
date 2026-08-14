package ar.edu.itba.sds.tp1;

import ar.edu.itba.sds.tp1.command.BenchmarkMCommand;
import ar.edu.itba.sds.tp1.command.BenchmarkNCommand;
import ar.edu.itba.sds.tp1.command.Command;
import ar.edu.itba.sds.tp1.command.GenerateCommand;

import java.io.IOException;
import java.util.Arrays;
import java.util.Map;

public final class Main {
    private static final Map<String, Command> COMMANDS = Map.of(
            "generate", new GenerateCommand(),
            "benchmark-m", new BenchmarkMCommand(),
            "benchmark-n", new BenchmarkNCommand()
    );

    private Main() {
    }

    public static void main(String[] args) {
        if (args.length == 0) {
            printUsage();
            System.exit(1);
            return;
        }

        Command command = COMMANDS.get(args[0]);
        if (command == null) {
            System.err.println("Comando desconocido: " + args[0]);
            printUsage();
            System.exit(1);
            return;
        }

        String[] rest = Arrays.copyOfRange(args, 1, args.length);
        try {
            command.execute(rest);
        } catch (IllegalArgumentException | IllegalStateException e) {
            System.err.println("Error: " + e.getMessage());
            printUsage();
            System.exit(1);
        } catch (IOException e) {
            System.err.println("Error de E/S: " + e.getMessage());
            System.exit(1);
        }
    }

    private static void printUsage() {
        System.err.println("Uso: java -jar target/tp1.jar <comando> [opciones]");
        System.err.println("Comandos disponibles:");
        System.err.println("  generate [N] [L] [seed] [directorio-salida]  Genera partículas de entrada");
        System.err.println("  benchmark-m n l radiusMin radiusMax rc periodic repetitions seed outputCsv"
                + "  Fuerza bruta vs CIM barriendo M, N fijo");
        System.err.println("  benchmark-n l0 radiusMin radiusMax rc periodic modo repetitions seed outputCsv Ns"
                + "  CIM con M óptima, barriendo N (modo=libre|fija)");
    }
}
