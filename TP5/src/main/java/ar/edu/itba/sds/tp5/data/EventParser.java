package ar.edu.itba.sds.tp5.data;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Lee los eventos de elusion_1_contra_1.txt y LEEME_elusion1contra1.txt. */
public final class EventParser {
    public static final String DATA_FILE = "elusion_1_contra_1.txt";
    public static final String README_FILE = "LEEME_elusion1contra1.txt";

    /** El LEEME deja sin identificar al peatón izquierdo del evento 2; es el ID 1000 (distancia mínima con el 25 = 0,88 m). */
    private static final String UNKNOWN_ID = "V?";
    private static final int UNKNOWN_ID_VALUE = 1000;

    private static final Pattern FRAMERATE = Pattern.compile("#\\s*framerate:\\s*([0-9.]+)\\s*fps");
    private static final Pattern EVENT = Pattern.compile(
            "prueba\\s+(\\d+):\\s+sale izquierda\\s+(\\S+),\\s+sale derecha\\s+(\\S+),\\s+cuadros\\s+(\\d+)-(\\d+),\\s+distancia minima\\s+([0-9.]+)");

    private EventParser() { }

    public static List<PedestrianEvent> parse(Path dataDir) throws IOException {
        return parse(Files.readAllLines(dataDir.resolve(DATA_FILE), StandardCharsets.ISO_8859_1),
                Files.readAllLines(dataDir.resolve(README_FILE), StandardCharsets.ISO_8859_1));
    }

    static List<PedestrianEvent> parse(List<String> dataLines, List<String> readmeLines) {
        Double framerate = null;
        Map<Integer, TreeMap<Integer, double[]>> rows = new HashMap<>();
        for (String line : dataLines) {
            String text = line.strip();
            if (text.isEmpty()) continue;
            if (text.startsWith("#")) {
                Matcher m = FRAMERATE.matcher(text);
                if (m.find()) framerate = Double.parseDouble(m.group(1));
                continue;
            }
            String[] p = text.split("\\s+");
            if (p.length != 5) throw new IllegalArgumentException("Fila inválida: " + line);
            int id = Integer.parseInt(p[0]), frame = Integer.parseInt(p[1]);
            double[] position = { Double.parseDouble(p[2]), Double.parseDouble(p[3]) };
            if (rows.computeIfAbsent(id, k -> new TreeMap<>()).put(frame, position) != null)
                throw new IllegalArgumentException("Frame repetido: ID " + id + ", frame " + frame);
        }
        if (framerate == null) throw new IllegalArgumentException("Falta el framerate en el encabezado");

        double dtExp = 1.0 / framerate;
        List<PedestrianEvent> events = new ArrayList<>();
        for (String line : readmeLines) {
            Matcher m = EVENT.matcher(line);
            if (!m.find()) continue;
            int from = Integer.parseInt(m.group(4)), to = Integer.parseInt(m.group(5));
            events.add(PedestrianEvent.of(Integer.parseInt(m.group(1)),
                    clip(rows, id(m.group(2)), from, to), clip(rows, id(m.group(3)), from, to),
                    dtExp, Double.parseDouble(m.group(6))));
        }
        if (events.isEmpty()) throw new IllegalArgumentException("El LEEME no tiene eventos");
        return events;
    }

    private static int id(String text) {
        return text.equals(UNKNOWN_ID) ? UNKNOWN_ID_VALUE : Integer.parseInt(text);
    }

    /** Filas del ID dentro de los cuadros del evento: el archivo también trae lo que hace fuera de esa ventana. */
    private static Trajectory clip(Map<Integer, TreeMap<Integer, double[]>> rows, int id, int from, int to) {
        TreeMap<Integer, double[]> all = rows.get(id);
        if (all == null) throw new IllegalArgumentException("El archivo no tiene el ID " + id);
        Map<Integer, double[]> window = all.subMap(from, true, to, true);
        int[] frames = new int[window.size()];
        double[] x = new double[frames.length], y = new double[frames.length];
        int k = 0;
        for (Map.Entry<Integer, double[]> e : window.entrySet()) {
            frames[k] = e.getKey();
            x[k] = e.getValue()[0];
            y[k++] = e.getValue()[1];
        }
        return new Trajectory(id, frames, x, y);
    }
}
