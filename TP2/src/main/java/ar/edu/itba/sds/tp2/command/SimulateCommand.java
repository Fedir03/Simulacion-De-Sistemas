package ar.edu.itba.sds.tp2.command;

import ar.edu.itba.sds.tp1.CellIndexMethod;
import ar.edu.itba.sds.tp2.engine.DirectionUpdateStrategy;
import ar.edu.itba.sds.tp2.engine.InitialConditionFile;
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
 * Uso: java -jar target/tp2.jar simulate --model=voter|standard --eta=&lt;double&gt;
 *      --steps=&lt;int&gt; --out=&lt;archivo&gt; --seedLoop=&lt;long|auto&gt;
 *      (--n=&lt;int&gt; --seedIC=&lt;long|auto&gt; | --icFile=&lt;archivo&gt;)
 *      [--l=10.0] [--rc=1.0] [--dt=1.0] [--v0=0.03] [--periodic=true|false]
 *      [--theta0=random|&lt;radianes&gt;]
 *
 * <p>{@code --icFile} lee la condición inicial de un archivo generado con {@code generate-ic} en
 * vez de generarla desde {@code --n}/--seedIC}: es mutuamente excluyente con {@code --n},
 * {@code --seedIC}, {@code --l} y {@code --theta0}, que quedan determinados por el archivo.
 */
public final class SimulateCommand implements Command {

    private static final List<String> IC_FILE_EXCLUSIVE_FLAGS = List.of("n", "seedIC", "l", "theta0");

    @Override
    public void execute(String[] args) throws IOException {
        Map<String, String> flags = CommandSupport.parseFlags(args);

        String model = CommandSupport.require(flags, "model");
        double eta = CommandSupport.parseDouble("eta", CommandSupport.require(flags, "eta"));
        int steps = CommandSupport.parseInt("steps", CommandSupport.require(flags, "steps"));
        Path out = Path.of(CommandSupport.require(flags, "out"));
        long seedLoop = CommandSupport.resolveSeed(CommandSupport.require(flags, "seedLoop"));
        double rc = CommandSupport.parseDouble("rc", CommandSupport.optional(flags, "rc", "1.0"));
        double dt = CommandSupport.parseDouble("dt", CommandSupport.optional(flags, "dt", "1.0"));
        double v0 = CommandSupport.parseDouble("v0", CommandSupport.optional(flags, "v0", "0.03"));
        boolean periodic = CommandSupport.parseBoolean("periodic", CommandSupport.optional(flags, "periodic", "true"));

        DirectionUpdateStrategy strategy = resolveStrategy(model);

        int n;
        double l;
        long seedIC;
        String theta0Label;
        List<VicsekParticle> initial;

        if (flags.containsKey("icFile")) {
            for (String exclusive : IC_FILE_EXCLUSIVE_FLAGS) {
                if (flags.containsKey(exclusive)) {
                    throw new IllegalArgumentException("--icFile no se puede combinar con --" + exclusive);
                }
            }
            InitialConditionFile.Data ic = InitialConditionFile.read(Path.of(flags.get("icFile")));
            n = ic.n();
            l = ic.l();
            seedIC = ic.seedIC();
            theta0Label = "random";
            initial = ic.particles();
        } else {
            n = CommandSupport.parseInt("n", CommandSupport.require(flags, "n"));
            l = CommandSupport.parseDouble("l", CommandSupport.optional(flags, "l", "10.0"));
            seedIC = CommandSupport.resolveSeed(CommandSupport.require(flags, "seedIC"));
            theta0Label = CommandSupport.optional(flags, "theta0", "random");
            Double theta0 = resolveTheta0(theta0Label);
            initial = InitialConditionGenerator.generate(n, l, new Random(seedIC), theta0);
        }

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
