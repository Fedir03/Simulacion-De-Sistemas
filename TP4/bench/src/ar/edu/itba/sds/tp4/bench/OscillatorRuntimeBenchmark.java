package ar.edu.itba.sds.tp4.bench;

import ar.edu.itba.sds.tp4.engine.oscillator.IntegrationOptions;
import ar.edu.itba.sds.tp4.engine.oscillator.OscillatorStudy;
import ar.edu.itba.sds.tp4.engine.oscillator.Scheme;
import ar.edu.itba.sds.tp4.models.Oscillator;
import java.lang.management.ManagementFactory;
import java.util.*;
import java.util.function.Supplier;

/**
 * Tiempo de cómputo de los 4 esquemas del Sistema 1 con el mismo dt y tf (Oscillator.defaults, IntegrationOptions.defaults).
 * Mide solo Scheme.integrate (incluye el new double[steps+1] interno); el caso alloc mide esa reserva sola como referencia.
 * Una JVM: --warmup rondas descartadas, después --reps + 1 rondas de las que se descarta la primera. Cada ronda recorre los
 * casos en el orden de Collections.shuffle con un Random(--order-seed) compartido; System.gc() antes de cada corrida.
 * Uso: java -Xms2g -Xmx2g -cp tp4.jar;clases OscillatorRuntimeBenchmark [--dt 1e-6] [--reps 10] [--warmup 20] [--order-seed 20261023]
 */
public final class OscillatorRuntimeBenchmark {
    private OscillatorRuntimeBenchmark() { }
    private static final Set<String> OPTIONS = Set.of("dt", "reps", "warmup", "order-seed");
    private static double sink;

    private record Case(String id, Supplier<double[]> run) { }

    public static void main(String[] args) {
        Map<String, String> options = new LinkedHashMap<>();
        for (int i = 0; i < args.length; i += 2) {
            if (!args[i].startsWith("--") || i + 1 >= args.length || !OPTIONS.contains(args[i].substring(2))
                    || options.put(args[i].substring(2), args[i + 1]) != null)
                throw new IllegalArgumentException("Opción inválida o repetida: " + args[i]);
        }
        double dt = Double.parseDouble(options.getOrDefault("dt", "1e-6"));
        int reps = Integer.parseInt(options.getOrDefault("reps", "10"));
        int warmup = Integer.parseInt(options.getOrDefault("warmup", "20"));
        long orderSeed = Long.parseLong(options.getOrDefault("order-seed", "20261023"));
        if (reps < 5 || warmup < 1) throw new IllegalArgumentException("Se piden al menos 5 repeticiones y 1 ronda de calentamiento");

        Oscillator o = Oscillator.defaults();
        IntegrationOptions opt = IntegrationOptions.defaults();
        int steps = OscillatorStudy.steps(o, dt);
        List<Case> cases = new ArrayList<>();
        for (Scheme s : Scheme.values()) cases.add(new Case(s.id(), () -> s.integrate(o, dt, steps, opt)));
        cases.add(new Case("alloc", () -> new double[steps + 1]));

        System.out.printf(Locale.ROOT, "# dt=%s tf=%s steps=%d %s%n# jvm: %s | java %s%n# warmup=%d rondas, reps=%d (+1 descartada), order_seed=%d%n",
                dt, o.finalTime(), steps, opt.describe(), String.join(" ", ManagementFactory.getRuntimeMXBean().getInputArguments()),
                System.getProperty("java.version"), warmup, reps, orderSeed);

        Random random = new Random(orderSeed);
        for (int w = 0; w < warmup; w++) for (Case c : shuffled(cases, random)) time(c);

        Map<String, List<Double>> times = new LinkedHashMap<>();
        for (Case c : cases) times.put(c.id(), new ArrayList<>());
        System.out.println("round,position,case,runtime_s");
        for (int r = 0; r <= reps; r++) {
            List<Case> round = shuffled(cases, random);
            for (int p = 0; p < round.size(); p++) {
                double t = time(round.get(p));
                System.out.printf(Locale.ROOT, "%d,%d,%s,%.9f%s%n", r, p, round.get(p).id(), t, r == 0 ? " # descartada" : "");
                if (r > 0) times.get(round.get(p).id()).add(t);
            }
        }

        System.out.println();
        System.out.println("case,median_s,min_s,max_s,median_us_per_step,ecm");
        String fastest = null;
        double best = Double.POSITIVE_INFINITY;
        for (Case c : cases) {
            List<Double> ts = times.get(c.id());
            Collections.sort(ts);
            int n = ts.size();
            double median = n % 2 == 1 ? ts.get(n / 2) : (ts.get(n / 2 - 1) + ts.get(n / 2)) / 2;
            boolean scheme = !c.id().equals("alloc");
            String ecm = scheme ? Double.toString(OscillatorStudy.ecm(o, dt, c.run().get())) : "-";
            System.out.printf(Locale.ROOT, "%s,%.6f,%.6f,%.6f,%.5f,%s%n", c.id(), median, ts.get(0), ts.get(n - 1), 1e6 * median / steps, ecm);
            if (scheme && median < best) { best = median; fastest = c.id(); }
        }
        System.out.println("# más rápido por mediana: " + fastest + " | sink=" + sink);
    }

    private static List<Case> shuffled(List<Case> cases, Random random) {
        List<Case> order = new ArrayList<>(cases);
        Collections.shuffle(order, random);
        return order;
    }

    private static double time(Case c) {
        System.gc();
        long start = System.nanoTime();
        double[] x = c.run().get();
        double runtime = (System.nanoTime() - start) / 1e9;
        sink += x[x.length - 1];
        return runtime;
    }
}
