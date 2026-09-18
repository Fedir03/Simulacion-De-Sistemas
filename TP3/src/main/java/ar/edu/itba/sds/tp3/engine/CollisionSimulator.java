package ar.edu.itba.sds.tp3.engine;

import ar.edu.itba.sds.tp3.models.*;
import java.io.IOException;
import java.util.*;

/** Dinámica de discos duros con cola de prioridad e invalidación perezosa. */
public final class CollisionSimulator {
    @FunctionalInterface public interface FrameSink {
        void write(double time, long events, int goals, List<Particle> particles) throws IOException;
    }
    public record Result(double time, long events, int goals, double t90) { }
    private final SimulationConfig config;
    private final List<Particle> particles;
    private final List<Obstacle> obstacles;
    private final PriorityQueue<Event> queue = new PriorityQueue<>();
    private double time, limit;
    private long sequence;
    private boolean started;

    public CollisionSimulator(StageGeneration.Stage stage) {
        config = stage.config(); obstacles = stage.obstacles();
        particles = stage.particles().stream().map(Particle::copy).toList();
        if (particles.isEmpty()) throw new IllegalArgumentException("Se requiere al menos una partícula");
    }

    public Result run(double endTime, int outputEvery, FrameSink output) throws IOException {
        return run(endTime, outputEvery, 0, output);
    }

    /** Con outputInterval > 0 escribe los estados en t = k·outputInterval en lugar de cada
     * outputEvery eventos. Son exactos: entre eventos el movimiento es rectilíneo uniforme.
     * Se calculan sobre copias, así la dinámica es idéntica bit a bit con o sin muestreo. */
    public Result run(double endTime, int outputEvery, double outputInterval, FrameSink output) throws IOException {
        if (started) throw new IllegalStateException("Crear un simulador nuevo para cada corrida");
        if (!Double.isFinite(endTime) || endTime < 0 || outputEvery <= 0 || !Double.isFinite(outputInterval) || outputInterval < 0)
            throw new IllegalArgumentException("Tiempo final no negativo y frecuencia positiva requeridos");
        boolean sampled = outputInterval > 0;
        started = true; limit = endTime;
        long events = 0;
        int goals = (int) particles.stream().filter(Particle::used).count();
        double t90 = goals >= Math.ceil(0.9 * particles.size()) ? 0 : Double.NaN;
        output.write(0, 0, goals, particles);
        for (Particle p : particles) predict(p, null);
        double lastOutput = 0;
        long samples = 1;
        while (!queue.isEmpty()) {
            Event e = queue.remove();
            if (!e.valid()) continue;
            // Muestras temporales hasta este evento, antes de resolverlo.
            for (double next = samples * outputInterval; sampled && next <= e.time(); next = ++samples * outputInterval) {
                sample(next, events, goals, output); lastOutput = next;
            }
            advance(e.time());
            events++;
            // A4: guarda el estado de contacto antes de resolver el choque (A5).
            if (!sampled && events % outputEvery == 0) {
                output.write(time, events, goals, particles); lastOutput = time;
            }
            Particle a = e.a();
            switch (e.type()) {
                case VERTICAL_WALL -> {
                    if (Math.abs(a.y() - config.width() / 2) <= config.goalWidth() / 2 && a.markUsed()) goals++;
                    a.setVelocityAfterCollision(-a.vx(), a.vy());
                }
                case HORIZONTAL_WALL -> a.setVelocityAfterCollision(a.vx(), -a.vy());
                case PARTICLE -> bounce(a, e.b());
                case OBSTACLE -> {
                    double dx = a.x() - e.obstacle().x(), dy = a.y() - e.obstacle().y();
                    double factor = 2 * (a.vx() * dx + a.vy() * dy) / (dx * dx + dy * dy);
                    a.setVelocityAfterCollision(a.vx() - factor * dx, a.vy() - factor * dy);
                }
            }
            if (Double.isNaN(t90) && goals >= Math.ceil(0.9 * particles.size())) t90 = time;
            predict(a, null);
            if (e.b() != null) predict(e.b(), a);
            // Limita memoria retenida por eventos obsoletos sin alterar las predicciones válidas.
            if (queue.size() > 8L * particles.size() * (particles.size() + obstacles.size() + 2))
                queue.removeIf(event -> !event.valid());
        }
        for (double next = samples * outputInterval; sampled && next <= limit; next = ++samples * outputInterval) {
            sample(next, events, goals, output); lastOutput = next;
        }
        if (time < limit) advance(limit);
        if (lastOutput != time || !sampled && events % outputEvery != 0) output.write(time, events, goals, particles);
        return new Result(time, events, goals, t90);
    }

    /** Escribe el estado en t ≥ time sin modificar las partículas: redondear posiciones
     * intermedias cambiaría la trayectoria de un sistema caótico. */
    private void sample(double t, long events, int goals, FrameSink output) throws IOException {
        double dt = t - time;
        List<Particle> moved = new ArrayList<>(particles.size());
        for (Particle p : particles) { Particle q = p.copy(); q.move(dt); moved.add(q); }
        output.write(t, events, goals, moved);
    }

    private void advance(double next) {
        double dt = next - time;
        for (Particle p : particles) p.move(dt);
        time = next;
    }

    private void predict(Particle p, Particle skip) {
        add(wallTime(p.x(), p.vx(), p.radius(), config.length()), Event.Type.VERTICAL_WALL, p, null, null);
        add(wallTime(p.y(), p.vy(), p.radius(), config.width()), Event.Type.HORIZONTAL_WALL, p, null, null);
        for (Particle b : particles) if (b != p && b != skip)
            add(collisionTime(b.x() - p.x(), b.y() - p.y(), b.vx() - p.vx(), b.vy() - p.vy(), p.radius() + b.radius()),
                    Event.Type.PARTICLE, p, b, null);
        for (Obstacle o : obstacles)
            add(collisionTime(o.x() - p.x(), o.y() - p.y(), -p.vx(), -p.vy(), p.radius() + o.radius()),
                    Event.Type.OBSTACLE, p, null, o);
    }

    private void add(double dt, Event.Type type, Particle a, Particle b, Obstacle o) {
        // Contactos inmediatos son necesarios para resolver las dos paredes en una esquina.
        if (Double.isFinite(dt) && dt >= -1e-10 && time + Math.max(0, dt) <= limit)
            queue.add(new Event(time + Math.max(0, dt), type, a, b, o, sequence++));
    }

    static double wallTime(double position, double velocity, double radius, double size) {
        if (velocity == 0) return Double.POSITIVE_INFINITY;
        return ((velocity > 0 ? size - radius : radius) - position) / velocity;
    }

    static double collisionTime(double dx, double dy, double dvx, double dvy, double sigma) {
        double vr = dx * dvx + dy * dvy;
        double vv = dvx * dvx + dvy * dvy;
        double gap = dx * dx + dy * dy - sigma * sigma;
        double discriminant = vr * vr - vv * gap;
        if (vr >= 0 || vv == 0 || discriminant <= 0) return Double.POSITIVE_INFINITY;
        // Raíz menor racionalizada para evitar cancelación cerca del contacto.
        return gap / (-vr + Math.sqrt(discriminant));
    }

    static void bounce(Particle a, Particle b) {
        double dx = b.x() - a.x(), dy = b.y() - a.y();
        double vr = (b.vx() - a.vx()) * dx + (b.vy() - a.vy()) * dy;
        double impulse = 2 * a.mass() * b.mass() * vr / ((a.mass() + b.mass()) * (dx * dx + dy * dy));
        a.setVelocityAfterCollision(a.vx() + impulse * dx / a.mass(), a.vy() + impulse * dy / a.mass());
        b.setVelocityAfterCollision(b.vx() - impulse * dx / b.mass(), b.vy() - impulse * dy / b.mass());
    }
}
