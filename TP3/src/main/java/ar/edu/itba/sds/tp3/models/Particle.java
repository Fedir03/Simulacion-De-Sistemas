package ar.edu.itba.sds.tp3.models;

/** Disco móvil. El contador permite invalidar predicciones anteriores a un choque. */
public final class Particle {
    private final int id;
    private final double radius, mass;
    private double x, y, vx, vy;
    private boolean used;
    private long collisions;

    public Particle(int id, double x, double y, double vx, double vy, double radius, double mass) {
        if (id < 0 || !Double.isFinite(x) || !Double.isFinite(y)
                || !Double.isFinite(vx) || !Double.isFinite(vy)
                || !Double.isFinite(radius) || radius <= 0 || !Double.isFinite(mass) || mass <= 0)
            throw new IllegalArgumentException("Partícula inválida");
        this.id = id; this.x = x; this.y = y; this.vx = vx; this.vy = vy;
        this.radius = radius; this.mass = mass;
    }

    public int id() { return id; }
    public double x() { return x; }
    public double y() { return y; }
    public double vx() { return vx; }
    public double vy() { return vy; }
    public double radius() { return radius; }
    public double mass() { return mass; }
    public boolean used() { return used; }
    public long collisions() { return collisions; }
    public boolean markUsed() { boolean fresh = !used; used = true; return fresh; }
    public void move(double dt) { x += vx * dt; y += vy * dt; }
    public void setVelocityAfterCollision(double vx, double vy) {
        this.vx = vx; this.vy = vy; collisions++;
    }
    public Particle copy() {
        Particle p = new Particle(id, x, y, vx, vy, radius, mass);
        p.used = used;
        return p;
    }
}
