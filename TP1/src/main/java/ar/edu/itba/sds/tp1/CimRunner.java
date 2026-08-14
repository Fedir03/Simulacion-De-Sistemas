package ar.edu.itba.sds.tp1;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;
import java.util.Set;

public class CimRunner {

    private static final String USAGE =
            "Uso: java -cp target/classes ar.edu.itba.sds.tp1.CimRunner "
                    + "<static> <dynamic> [--rc=1.0] [--m=<int>] [--periodic] [--out=output.txt]";

    private static final double DEFAULT_RC = 1.0;
    private static final String DEFAULT_OUT = "output.txt";

    public static void main(String[] args) {
        try {
            run(args);
        } catch (IllegalArgumentException | IOException e) {
            System.err.println("Error: " + e.getMessage());
            System.err.println(USAGE);
            System.exit(1);
        }
    }

    private static void run(String[] args) throws IOException {
        Path staticPath = null;
        Path dynamicPath = null;
        double rc = DEFAULT_RC;
        Integer m = null;
        boolean periodic = false;
        Path out = Path.of(DEFAULT_OUT);

        for (String arg : args) {
            if (arg.startsWith("--rc=")) {
                rc = parseDouble(arg, arg.substring("--rc=".length()));
            } else if (arg.startsWith("--m=")) {
                m = parseInt(arg, arg.substring("--m=".length()));
            } else if (arg.equals("--periodic")) {
                periodic = true;
            } else if (arg.startsWith("--out=")) {
                out = Path.of(arg.substring("--out=".length()));
            } else if (arg.startsWith("--")) {
                throw new IllegalArgumentException("opcion desconocida: " + arg);
            } else if (staticPath == null) {
                staticPath = Path.of(arg);
            } else if (dynamicPath == null) {
                dynamicPath = Path.of(arg);
            } else {
                throw new IllegalArgumentException("argumento posicional de mas: " + arg);
            }
        }

        if (staticPath == null || dynamicPath == null) {
            throw new IllegalArgumentException("faltan las rutas de los archivos static y dynamic");
        }

        SimulationInput input = InputReader.read(staticPath, dynamicPath);

        if (m == null) {
            double rMax = 0;
            for (Particle p : input.particles()) {
                rMax = Math.max(rMax, p.radius());
            }
            m = CellIndexMethod.maxValidM(input.l(), rc, rMax);
        }

        long start = System.nanoTime();
        Map<Integer, Set<Integer>> neighbors = new CellIndexMethod(m)
                .findNeighbors(input.particles(), input.l(), rc, periodic);
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;

        OutputWriter.write(out, neighbors);

        System.out.printf("N=%d L=%.4f rc=%.4f M=%d contorno=%s tiempo=%dms output=%s%n",
                input.n(), input.l(), rc, m, periodic ? "periodico" : "paredes", elapsedMs, out);
    }

    private static double parseDouble(String arg, String value) {
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("valor numerico invalido en " + arg);
        }
    }

    private static int parseInt(String arg, String value) {
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("valor entero invalido en " + arg);
        }
    }
}
