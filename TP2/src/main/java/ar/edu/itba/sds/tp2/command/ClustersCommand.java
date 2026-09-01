package ar.edu.itba.sds.tp2.command;

import ar.edu.itba.sds.tp1.CellIndexMethod;
import ar.edu.itba.sds.tp2.analysis.ClusterAnalysis;
import ar.edu.itba.sds.tp2.analysis.ClusterStats;
import ar.edu.itba.sds.tp2.analysis.Frame;
import ar.edu.itba.sds.tp2.analysis.RunHeader;
import ar.edu.itba.sds.tp2.analysis.SimulationReader;
import ar.edu.itba.sds.tp2.engine.NeighborLookup;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

/**
 * Calcula la fraccion de particulas en la componente gigante (S) a lo largo de una corrida.
 * Uso: java -jar target/tp2.jar clusters --in=&lt;corrida.txt&gt; --out=&lt;S.csv&gt; [--stride=1]
 *      [--members=&lt;miembros.txt&gt;]
 *
 * <p>Lee el archivo de texto que produjo el motor: no lo invoca ni depende de el.
 */
public final class ClustersCommand implements Command {

    @Override
    public void execute(String[] args) throws IOException {
        Map<String, String> flags = CommandSupport.parseFlags(args);

        Path in = Path.of(CommandSupport.require(flags, "in"));
        Path out = Path.of(CommandSupport.require(flags, "out"));
        int stride = CommandSupport.parseInt("stride", CommandSupport.optional(flags, "stride", "1"));
        String membersFlag = CommandSupport.optional(flags, "members", "");
        Path members = membersFlag.isEmpty() ? null : Path.of(membersFlag);
        if (stride <= 0) {
            throw new IllegalArgumentException("stride debe ser un entero positivo: " + stride);
        }

        int analyzed = 0;
        double lastS = 0.0;
        if (out.getParent() != null) {
            Files.createDirectories(out.getParent());
        }
        if (members != null && members.getParent() != null) {
            Files.createDirectories(members.getParent());
        }

        try (SimulationReader reader = SimulationReader.open(in);
             BufferedWriter writer = Files.newBufferedWriter(out);
             BufferedWriter membersWriter = members == null
                     ? null : Files.newBufferedWriter(members)) {

            RunHeader header = reader.header();
            NeighborLookup lookup = new NeighborLookup(
                    new CellIndexMethod(CellIndexMethod.maxValidM(header.l(), header.rc(), 0.0)),
                    header.l(), header.rc(), header.periodic());

            writeHeader(writer, header);

            Frame frame;
            while ((frame = reader.next()) != null) {
                if (frame.step() % stride != 0) {
                    continue;
                }
                ClusterStats stats = ClusterAnalysis.of(frame.particles(), lookup);
                writer.write(frame.step() + "," + stats.s());
                writer.newLine();
                if (membersWriter != null) {
                    writeMembers(membersWriter, frame.step(), stats);
                }
                lastS = stats.s();
                analyzed++;
            }
        }

        System.out.printf("clusters: %d cuadros analizados (stride=%d) S(final)=%.4f output=%s%n",
                analyzed, stride, lastS, out.toAbsolutePath());
    }

    /**
     * Una linea por cuadro: el paso y despues los ids del cluster mas grande, separados por
     * espacios. Lo consume animate.py para resaltar esas particulas.
     */
    private static void writeMembers(BufferedWriter writer, int step, ClusterStats stats)
            throws IOException {
        StringBuilder line = new StringBuilder().append(step);
        for (Integer id : stats.sortedMembers()) {
            line.append(' ').append(id);
        }
        writer.write(line.toString());
        writer.newLine();
    }

    /**
     * Misma forma que los CSV de v_a: la cabecera de la corrida como comentario y despues
     * las columnas, para que los graficadores de Python los lean igual.
     */
    private static void writeHeader(BufferedWriter writer, RunHeader header) throws IOException {
        writer.write("# " + String.join(" ",
                "model=" + header.model(),
                "N=" + header.n(),
                "L=" + header.l(),
                "rc=" + header.rc(),
                "dt=" + header.dt(),
                "v0=" + header.v0(),
                "eta=" + header.eta(),
                "periodic=" + header.periodic(),
                "seedIC=" + header.seedIC(),
                "seedLoop=" + header.seedLoop(),
                "theta0=" + header.theta0()));
        writer.newLine();
        writer.write("t,S");
        writer.newLine();
    }
}
