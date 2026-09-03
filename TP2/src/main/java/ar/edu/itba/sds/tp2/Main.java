package ar.edu.itba.sds.tp2;

import ar.edu.itba.sds.tp2.command.BenchmarkCimCommand;
import ar.edu.itba.sds.tp2.command.ClustersCommand;
import ar.edu.itba.sds.tp2.command.Command;
import ar.edu.itba.sds.tp2.command.SimulateCommand;

import java.io.IOException;
import java.util.Arrays;
import java.util.Map;

public final class Main {
    private static final Map<String, Command> COMMANDS = Map.of(
            "simulate", new SimulateCommand(),
            "clusters", new ClustersCommand(),
            "benchmark-cim", new BenchmarkCimCommand()
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
        System.err.println("Uso: java -jar target/tp2.jar <comando> [opciones]");
        System.err.println("Comandos disponibles:");
        System.err.println("  simulate --model=voter|standard --n=<int> --eta=<double> --steps=<int> --out=<archivo>");
        System.err.println("           --seedIC=<long|auto> --seedLoop=<long|auto>");
        System.err.println("           [--l=10.0] [--rc=1.0] [--dt=1.0] [--v0=0.03] [--periodic=true|false]");
        System.err.println("           [--theta0=random|<radianes>]");
        System.err.println("  clusters --in=<corrida.txt> --out=<S.csv> [--stride=1] [--members=<archivo>]");
        System.err.println("  benchmark-cim --in=<a.txt,b.txt,...> --out=<csv> [--warmup=50]");
    }
}