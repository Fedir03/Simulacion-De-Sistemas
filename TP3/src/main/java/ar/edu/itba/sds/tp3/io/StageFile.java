package ar.edu.itba.sds.tp3.io;

import ar.edu.itba.sds.tp3.engine.*;
import ar.edu.itba.sds.tp3.models.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Formato versionado compartido por condiciones iniciales y trayectorias. */
public final class StageFile {
    private StageFile() { }
    public static BufferedWriter writer(Path path) throws IOException {
        Path parent = path.toAbsolutePath().getParent();
        Files.createDirectories(parent);
        return Files.newBufferedWriter(path);
    }
    public static void header(BufferedWriter w, StageGeneration.Stage s) throws IOException {
        SimulationConfig c = s.config();
        w.write("format=tp3-v1 N=" + s.particles().size() + " K=" + s.obstacles().size()
                + " L=" + c.length() + " W=" + c.width() + " d=" + c.goalWidth()
                + " r=" + c.radius() + " m=" + c.mass() + " v0=" + c.speed() + " seedIC=" + s.seed());
        w.newLine();
        for (Obstacle o : s.obstacles()) { w.write("obstacle " + o.x() + " " + o.y() + " " + o.radius()); w.newLine(); }
    }
    public static void frame(BufferedWriter w, double time, long events, int goals, List<Particle> particles) throws IOException {
        w.write("t=" + time + " events=" + events + " Ng=" + goals + " Fu=" + (double) goals / particles.size()); w.newLine();
        for (Particle p : particles) {
            w.write(p.id() + " " + p.x() + " " + p.y() + " " + p.vx() + " " + p.vy()
                    + " " + p.radius() + " " + p.mass() + " " + (p.used() ? "255 0 0" : "0 0 255"));
            w.newLine();
        }
    }
    /** Cabecera del registro de eventos: una línea por colisión válida, en orden. */
    public static void eventHeader(BufferedWriter w) throws IOException {
        w.write("# format=tp3-events-v1 columnas: t evento tipo a b gol"); w.newLine();
        w.write("# tipo: P partícula-partícula (b = id), O obstáculo (b = índice en la cabecera), V pared vertical, H pared horizontal (b = -1)");
        w.newLine();
    }
    public static void event(BufferedWriter w, double time, long index, Event.Type type, int a, int other, boolean goal) throws IOException {
        w.write(time + " " + index + " " + type.name().charAt(0) + " " + a + " " + other + " " + (goal ? 1 : 0)); w.newLine();
    }
    public static void write(Path path, StageGeneration.Stage stage) throws IOException {
        try (BufferedWriter w = writer(path)) {
            header(w, stage);
            frame(w, 0, 0, (int) stage.particles().stream().filter(Particle::used).count(), stage.particles());
        }
    }
    private static Map<String, String> fields(String line) {
        if (line == null) throw new IllegalArgumentException("Archivo incompleto");
        Map<String, String> result = new HashMap<>();
        for (String token : line.trim().split("\\s+")) {
            String[] pair = token.split("=", -1);
            if (pair.length != 2 || result.put(pair[0], pair[1]) != null) throw new IllegalArgumentException("Cabecera inválida");
        }
        return result;
    }
    public static StageGeneration.Stage read(Path path) throws IOException {
        try (BufferedReader reader = Files.newBufferedReader(path)) {
            Map<String, String> h = fields(reader.readLine());
            if (!"tp3-v1".equals(h.get("format"))) throw new IllegalArgumentException("Formato no soportado");
            SimulationConfig c = new SimulationConfig(number(h, "L"), number(h, "W"), number(h, "d"), number(h, "r"), number(h, "m"), number(h, "v0"));
            int n = Integer.parseInt(h.get("N")), k = Integer.parseInt(h.get("K"));
            if (n <= 0 || k < 0) throw new IllegalArgumentException("N o K inválidos");
            List<Obstacle> obstacles = new ArrayList<>();
            for (int i = 0; i < k; i++) {
                String[] v = tokens(reader.readLine(), 4);
                if (!v[0].equals("obstacle")) throw new IllegalArgumentException("Se esperaba obstacle");
                obstacles.add(new Obstacle(Double.parseDouble(v[1]), Double.parseDouble(v[2]), Double.parseDouble(v[3])));
            }
            Map<String, String> marker = fields(reader.readLine());
            if (number(marker, "t") != 0) throw new IllegalArgumentException("La condición inicial debe tener t=0");
            List<Particle> particles = new ArrayList<>();
            for (int i = 0; i < n; i++) {
                String[] v = tokens(reader.readLine(), 10);
                Particle p = new Particle(Integer.parseInt(v[0]), Double.parseDouble(v[1]), Double.parseDouble(v[2]),
                        Double.parseDouble(v[3]), Double.parseDouble(v[4]), Double.parseDouble(v[5]), Double.parseDouble(v[6]));
                if (v[7].equals("255") && v[8].equals("0") && v[9].equals("0")) p.markUsed();
                else if (!(v[7].equals("0") && v[8].equals("0") && v[9].equals("255"))) throw new IllegalArgumentException("Color inválido");
                particles.add(p);
            }
            if (reader.readLine() != null) throw new IllegalArgumentException("Se esperaba una sola condición inicial");
            return new StageGeneration.Stage(c, Long.parseLong(h.get("seedIC")), particles, obstacles);
        } catch (NullPointerException | NumberFormatException e) {
            throw new IllegalArgumentException("Archivo de condición inicial inválido: " + path, e);
        }
    }
    private static double number(Map<String, String> h, String key) { return Double.parseDouble(h.get(key)); }
    private static String[] tokens(String line, int count) {
        if (line == null) throw new IllegalArgumentException("Archivo incompleto");
        String[] v = line.trim().split("\\s+");
        if (v.length != count) throw new IllegalArgumentException("Se esperaban " + count + " columnas: " + line);
        return v;
    }
    /** Escribe obstáculos en el formato de competencia: una línea x y radio por obstáculo. */
    public static void writeObstacles(Path path, List<Obstacle> obstacles) throws IOException {
        try (BufferedWriter w = writer(path)) {
            for (Obstacle o : obstacles) { w.write(o.x() + " " + o.y() + " " + o.radius()); w.newLine(); }
        }
    }
    public static List<Obstacle> readObstacles(Path path) throws IOException {
        List<Obstacle> result = new ArrayList<>();
        for (String line : Files.readAllLines(path)) {
            line = line.split("#", 2)[0].trim();
            if (line.isEmpty()) continue;
            String[] v = tokens(line, 3);
            result.add(new Obstacle(Double.parseDouble(v[0]), Double.parseDouble(v[1]), Double.parseDouble(v[2])));
        }
        return List.copyOf(result);
    }
}
