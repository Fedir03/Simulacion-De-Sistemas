package ar.edu.itba.sds.tp2.command;

import ar.edu.itba.sds.tp2.engine.InitialConditionFile;
import ar.edu.itba.sds.tp2.engine.InitialConditionGenerator;
import ar.edu.itba.sds.tp2.engine.VicsekParticle;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Genera una condición inicial (posiciones + ángulos al azar) y la escribe a un archivo, para que
 * varias corridas de {@code simulate} la lean con {@code --icFile} y arranquen del mismo estado
 * exacto en vez de confiar en que dos generaciones separadas a partir del mismo seedIC coincidan.
 * Uso: java -jar target/tp2.jar generate-ic --n=&lt;int&gt; --seedIC=&lt;long|auto&gt; --out=&lt;archivo&gt;
 *      [--l=10.0]
 */
public final class GenerateIcCommand implements Command {

    @Override
    public void execute(String[] args) throws IOException {
        Map<String, String> flags = CommandSupport.parseFlags(args);

        int n = CommandSupport.parseInt("n", CommandSupport.require(flags, "n"));
        double l = CommandSupport.parseDouble("l", CommandSupport.optional(flags, "l", "10.0"));
        long seedIC = CommandSupport.resolveSeed(CommandSupport.require(flags, "seedIC"));
        Path out = Path.of(CommandSupport.require(flags, "out"));

        List<VicsekParticle> particles = InitialConditionGenerator.generate(n, l, new Random(seedIC), null);
        InitialConditionFile.write(out, n, l, seedIC, particles);

        System.out.printf("N=%d L=%s seedIC=%d output=%s%n", n, l, seedIC, out.toAbsolutePath());
    }
}
