package ar.edu.itba.sds.tp1;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class OutputWriter {

    public static void write(Path out, Map<Integer, Set<Integer>> neighbors) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(out)) {
            for (Map.Entry<Integer, Set<Integer>> entry : neighbors.entrySet()) {
                List<String> fields = new ArrayList<>(entry.getValue().size() + 1);
                fields.add(String.valueOf(entry.getKey()));
                for (Integer neighbor : entry.getValue()) {
                    fields.add(String.valueOf(neighbor));
                }
                writer.write(String.join(",", fields));
                writer.newLine();
            }
        }
    }
}
