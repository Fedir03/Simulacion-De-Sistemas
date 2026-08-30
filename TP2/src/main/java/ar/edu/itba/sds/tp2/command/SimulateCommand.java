package ar.edu.itba.sds.tp2.command;

import ar.edu.itba.sds.tp1.CellIndexMethod;
import ar.edu.itba.sds.tp2.engine.DirectionUpdateStrategy;
import ar.edu.itba.sds.tp2.engine.InitialConditionGenerator;
import ar.edu.itba.sds.tp2.engine.NeighborLookup;
import ar.edu.itba.sds.tp2.engine.VicsekParticle;
import ar.edu.itba.sds.tp2.engine.VicsekSimulation;
import ar.edu.itba.sds.tp2.engine.StandardModel;
import ar.edu.itba.sds.tp2.engine.VoterModel;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Corre una simulación completa de Vicsek.
 * Uso: java -jar target/tp2.jar simulate --model=voter|standard --n=&lt;int&gt; --eta=&lt;double&gt;
 *      --steps=&lt;int&gt; --out=&lt;archivo&gt; --seedIC=&lt;long|auto&gt; --seedLoop=&lt;long|auto&gt;
 *      [--l=10.0] [--rc=1.0] [--dt=1.0] [--v0=0.03] [--periodic=true|false]
 *      [--theta0=random|&lt;radianes&gt;]
 */
public final class SimulateCommand implements Command {

    @Override
    public void execute(String[] args) throws IOException {
        Map<String, String> flags = CommandSupport.parseFlags(args);

        String model = CommandSupport.require(flags, "model");
        int n = CommandSupport.parseInt("n", CommandSupport.require(flags, "n"));
        double eta = CommandSupport.parseDouble("eta", CommandSupport.require(flags, "eta"));
        int steps = CommandSupport.parseInt("steps", CommandSupport.require(flags, "steps"));
        Path out = Path.of(CommandSupport.require(flags, "out"));
        long seedIC = CommandSupport.resolveSeed(CommandSupport.require(flags, "seedIC"));
        long seedLoop = CommandSupport.resolveSeed(CommandSupport.require(flags, "seedLoop"));
        double l = CommandSupport.parseDouble("l", CommandSupport.optional(flags, "l", "10.0"));
        double rc = CommandSupport.parseDouble("rc", CommandSupport.optional(flags, "rc", "1.0"));
        double dt = CommandSupport.parseDouble("dt", CommandSupport.optional(flags, "dt", "1.0"));
        double v0 = CommandSupport.parseDouble("v0", CommandSupport.optional(flags, "v0", "0.03"));
        boolean periodic = CommandSupport.parseBoolean("periodic", CommandSupport.optional(flags, "periodic", "true"));
        String theta0Label = CommandSupport.optional(flags, "theta0", "random");
        Double theta0 = resolveTheta0(theta0Label);

        DirectionUpdateStrategy strategy = resolveStrategy(model);

        List<VicsekParticle> initial = InitialConditionGenerator.generate(n, l, new Random(seedIC), theta0);
        int m = CellIndexMethod.maxValidM(l, rc, 0.0);
        NeighborLookup neighborLookup = new NeighborLookup(new CellIndexMethod(m), l, rc, periodic);

        VicsekSimulation simulation = new VicsekSimulation(
                initial, neighborLookup, strategy, model,
                dt, v0, eta, steps, new Random(seedLoop), seedIC, seedLoop, theta0Label);
        simulation.run(out);

        System.out.printf("modelo=%s N=%d L=%s eta=%s steps=%d seedIC=%d seedLoop=%d theta0=%s output=%s%n",
                model, n, l, eta, steps, seedIC, seedLoop, theta0Label, out.toAbsolutePath());
    }

    /** null => cada particula arranca con un angulo al azar; si no, el angulo fijo (en radianes) para todas. */
    private static Double resolveTheta0(String value) {
        if (value.equalsIgnoreCase("random")) {
            return null;
        }
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException(
                    "valor invalido para theta0: " + value + " (se espera 'random' o un angulo en radianes)");
        }
    }

    private static DirectionUpdateStrategy resolveStrategy(String model) {
        return switch (model) {
            case "voter" -> new VoterModel();
            case "standard" -> new StandardModel(true);
            default -> throw new IllegalArgumentException(
                    "Modelo desconocido: '" + model + "'. Valores válidos: voter, standard");
        };
    }
}
