package ar.edu.itba.sds.tp1;

import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class CellIndexMethodTest {

    private static final Path STATIC_100 = Path.of("ArchivosEjemplo", "Static100.txt");
    private static final Path DYNAMIC_100 = Path.of("ArchivosEjemplo", "Dynamic100.txt");

    @Test
    void wallModeMatchesBruteForceOnSampleDataset() throws IOException {
        SimulationInput input = InputReader.read(STATIC_100, DYNAMIC_100);
        double rc = 1.0;
        int m = CellIndexMethod.maxValidM(input.l(), rc, 0.37);

        Map<Integer, Set<Integer>> expected = new BruteForceNeighborFinder()
                .findNeighbors(input.particles(), input.l(), rc, false);
        Map<Integer, Set<Integer>> actual = new CellIndexMethod(m)
                .findNeighbors(input.particles(), input.l(), rc, false);

        assertEquals(expected, actual);
    }

    @Test
    void periodicModeMatchesBruteForceOnSampleDataset() throws IOException {
        SimulationInput input = InputReader.read(STATIC_100, DYNAMIC_100);
        double rc = 1.0;
        int m = CellIndexMethod.maxValidM(input.l(), rc, 0.37);

        Map<Integer, Set<Integer>> expected = new BruteForceNeighborFinder()
                .findNeighbors(input.particles(), input.l(), rc, true);
        Map<Integer, Set<Integer>> actual = new CellIndexMethod(m)
                .findNeighbors(input.particles(), input.l(), rc, true);

        assertEquals(expected, actual);
    }

    /*
     * Regresión del bug de radio: el criterio de M válido de la cátedra es L/M > rc, que asume
     * partículas puntuales. Con radio, dos partículas siguen siendo vecinas (borde a borde)
     * hasta que sus centros están a rc + r1 + r2, así que el corte real es L/M > rc + 2*radioMax
     * (peor caso, porque M es un único valor global). Con el criterio viejo, L=100 rc=6 radio=0.37
     * aceptaba M=16 (100/16=6.25 > 6), pero 6.25 < rc+2*radioMax=6.74: CIM se saltaba pares
     * vecinos reales en esa franja intermedia sin tirar ningún error. No se notó con el dataset
     * de 100 partículas de la cátedra porque ningún par cayó ahí; se detectó generando 200
     * partículas con el mismo radio, donde CIM (M=16) y fuerza bruta dejaron de coincidir. Estos
     * dos tests fijan M al máximo válido con la fórmula corregida (maxValidM) para quedar
     * pegados al borde de esa franja y detectar si el criterio se rompe de nuevo.
     */
    @Test
    void wallModeMatchesBruteForceOnGeneratedDataset() {
        List<Particle> particles = new ParticleGenerator(42).generate(200, 20);
        double rc = 1.0;
        int m = CellIndexMethod.maxValidM(20, rc, ParticleGenerator.DEFAULT_MAX_RADIUS);

        Map<Integer, Set<Integer>> expected = new BruteForceNeighborFinder()
                .findNeighbors(particles, 20, rc, false);
        Map<Integer, Set<Integer>> actual = new CellIndexMethod(m)
                .findNeighbors(particles, 20, rc, false);

        assertEquals(expected, actual);
    }

    @Test
    void periodicModeMatchesBruteForceOnGeneratedDataset() {
        List<Particle> particles = new ParticleGenerator(42).generate(200, 20);
        double rc = 1.0;
        int m = CellIndexMethod.maxValidM(20, rc, ParticleGenerator.DEFAULT_MAX_RADIUS);

        Map<Integer, Set<Integer>> expected = new BruteForceNeighborFinder()
                .findNeighbors(particles, 20, rc, true);
        Map<Integer, Set<Integer>> actual = new CellIndexMethod(m)
                .findNeighbors(particles, 20, rc, true);

        assertEquals(expected, actual);
    }

    @Test
    void findNeighborsThrowsWhenMExceedsMaximum() {
        List<Particle> particles = List.of(
                new Particle(1, 5, 5, 0.26),
                new Particle(2, 10, 10, 0.26)
        );
        int invalidM = CellIndexMethod.maxValidM(20, 1.0, 0.26) + 1;

        assertThrows(IllegalArgumentException.class, () ->
                new CellIndexMethod(invalidM).findNeighbors(particles, 20, 1.0, false));
    }

    @Test
    void findNeighborsThrowsWhenPeriodicViolatesMinimumDomainSize() {
        List<Particle> particles = List.of(
                new Particle(1, 5, 5, 0.26),
                new Particle(2, 10, 10, 0.26)
        );
        double l = 20;
        double rc = 10.0; // rc + 2*rMax = 10.52; L <= 2*10.52 => periodicidad inválida

        assertThrows(IllegalArgumentException.class, () ->
                new BruteForceNeighborFinder().findNeighbors(particles, l, rc, true));
        assertThrows(IllegalArgumentException.class, () ->
                new CellIndexMethod(1).findNeighbors(particles, l, rc, true));
    }

    @Test
    void findNeighborsHandlesParticleExactlyOnDomainBorder() {
        List<Particle> particles = List.of(
                new Particle(1, 20.0, 10.0, 0.26),
                new Particle(2, 10.0, 20.0, 0.26),
                new Particle(3, 10.0, 10.0, 0.26)
        );
        int m = CellIndexMethod.maxValidM(20, 1.0, 0.26);

        assertDoesNotThrow(() -> new CellIndexMethod(m).findNeighbors(particles, 20, 1.0, false));
        assertDoesNotThrow(() -> new CellIndexMethod(m).findNeighbors(particles, 20, 1.0, true));
    }

    @Test
    void maxValidMMatchesKnownCase() {
        assertEquals(13, CellIndexMethod.maxValidM(20, 1.0, 0.26));
    }
}
