package ar.edu.itba.sds.tp2.analysis;

/** Cabecera de una corrida, tal como la escribe VicsekSimulation en la primera linea. */
public record RunHeader(String model,
                        int n,
                        double l,
                        double rc,
                        double dt,
                        double v0,
                        double eta,
                        boolean periodic,
                        long seedIC,
                        long seedLoop,
                        String theta0) {

    public double density() {
        return n / (l * l);
    }
}
