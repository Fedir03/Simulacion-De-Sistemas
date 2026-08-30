package ar.edu.itba.sds.tp2.engine;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import java.util.stream.Collectors;

/** Orquesta una corrida completa de Vicsek (estándar o votante) y escribe el output en streaming. */
public final class VicsekSimulation {
    private final List<VicsekParticle> initialParticles;
    private final NeighborLookup neighborLookup;
    private final DirectionUpdateStrategy strategy;
    private final String modelName;
    private final double dt;
    private final double v0;
    private final double eta;
    private final int steps;
    private final Random loopRandom;
    private final long seedIC;
    private final long seedLoop;
    private final String theta0Label;

    public VicsekSimulation(List<VicsekParticle> initialParticles,
                             NeighborLookup neighborLookup,
                             DirectionUpdateStrategy strategy,
                             String modelName,
                             double dt,
                             double v0,
                             double eta,
                             int steps,
                             Random loopRandom,
                             long seedIC,
                             long seedLoop,
                             String theta0Label) {
        this.initialParticles = initialParticles;
        this.neighborLookup = neighborLookup;
        this.strategy = strategy;
        this.modelName = modelName;
        this.dt = dt;
        this.v0 = v0;
        this.eta = eta;
        this.steps = steps;
        this.loopRandom = loopRandom;
        this.seedIC = seedIC;
        this.seedLoop = seedLoop;
        this.theta0Label = theta0Label;
    }

    public void run(Path output) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(output)) {
            writeHeader(writer);
            List<VicsekParticle> current = initialParticles;
            writeBlock(writer, 0, current);
            for (int i = 0; i < steps; i++) {
                current = advance(current);
                writeBlock(writer, i + 1, current);
            }
        }
    }

    private void writeHeader(BufferedWriter writer) throws IOException {
        String header = String.join(" ",
                "model=" + modelName,
                "N=" + initialParticles.size(),
                "L=" + neighborLookup.l(),
                "rc=" + neighborLookup.rc(),
                "dt=" + dt,
                "v0=" + v0,
                "eta=" + eta,
                "periodic=" + neighborLookup.periodic(),
                "seedIC=" + seedIC,
                "seedLoop=" + seedLoop,
                "theta0=" + theta0Label
        );
        writer.write(header);
        writer.newLine();
    }

    private void writeBlock(BufferedWriter writer, int t, List<VicsekParticle> particles) throws IOException {
        writer.write("t=" + t);
        writer.newLine();
        for (VicsekParticle p : particles) {
            writer.write(p.id() + " "
                    + p.x() + " "
                    + p.y() + " "
                    + p.theta());
            writer.newLine();
        }
    }

    private List<VicsekParticle> advance(List<VicsekParticle> current) {
        boolean periodic = neighborLookup.periodic();
        double l = neighborLookup.l();

        List<VicsekParticle> updated = current.stream()
                .map(p -> {
                    double x = p.x() + v0 * Math.cos(p.theta()) * dt;
                    double y = p.y() + v0 * Math.sin(p.theta()) * dt;
                    if (periodic) {
                        x = PeriodicBoundary.wrap(x, l);
                        y = PeriodicBoundary.wrap(y, l);
                    }
                    return new VicsekParticle(p.id(), x, y, p.theta());
                })
                .toList();

        Map<Integer, VicsekParticle> byId = updated.stream()
                .collect(Collectors.toMap(VicsekParticle::id, particle -> particle));

        Map<Integer, Set<Integer>> neighborIds = neighborLookup.findNeighbors(updated);

        return updated.stream()
                .map(p -> {
                    List<VicsekParticle> neighborParticles = neighborIds.get(p.id()).stream()
                            .map(byId::get)
                            .toList();
                    double newTheta = strategy.nextAngle(p, neighborParticles, eta, loopRandom);
                    return new VicsekParticle(p.id(), p.x(), p.y(), newTheta);
                })
                .toList();
    }
}
