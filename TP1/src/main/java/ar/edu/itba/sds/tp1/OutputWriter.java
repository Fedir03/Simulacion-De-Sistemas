package ar.edu.itba.sds.tp1;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class OutputWriter {

    public static void write(Path out, Map<Integer, Set<Integer>> neighbors) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(out)) {
            List<Integer> ids = new ArrayList<>(neighbors.keySet());
            Collections.sort(ids);
            for (Integer id : ids) {
                List<Integer> sortedNeighbors = new ArrayList<>(neighbors.get(id));
                Collections.sort(sortedNeighbors);

                List<String> fields = new ArrayList<>(sortedNeighbors.size() + 1);
                fields.add(String.valueOf(id));
                for (Integer neighbor : sortedNeighbors) {
                    fields.add(String.valueOf(neighbor));
                }
                writer.write(String.join(",", fields));
                writer.newLine();
            }
        }
    }
}
