package ar.edu.itba.sds.tp3.models;

/** Predicción absoluta con desempate estable por orden de inserción. */
public record Event(double time, Type type, Particle a, Particle b, Obstacle obstacle,
                    long countA, long countB, long sequence) implements Comparable<Event> {
    public enum Type { PARTICLE, OBSTACLE, VERTICAL_WALL, HORIZONTAL_WALL }
    public Event(double time, Type type, Particle a, Particle b, Obstacle obstacle, long sequence) {
        this(time, type, a, b, obstacle, a.collisions(), b == null ? -1 : b.collisions(), sequence);
    }
    public boolean valid() {
        return a.collisions() == countA && (b == null || b.collisions() == countB);
    }
    @Override public int compareTo(Event other) {
        int order = Double.compare(time, other.time);
        return order == 0 ? Long.compare(sequence, other.sequence) : order;
    }
}
