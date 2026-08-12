package ar.edu.itba.sds.tp1;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public class InputReader {

    // PowerShell on Windows writes UTF-8 files with a BOM that trim() does not strip
    private static String stripBom(String line) {
        return line.startsWith("﻿") ? line.substring(1) : line;
    }

    public static SimulationInput read(Path staticPath, Path dynamicPath) throws IOException {
        List<String> staticLines = Files.readAllLines(staticPath);
        int n = Integer.parseInt(stripBom(staticLines.get(0)).trim());
        double l = Double.parseDouble(staticLines.get(1).trim());

        double[] radii = new double[n];
        for (int i = 0; i < n; i++) {
            String[] parts = staticLines.get(i + 2).trim().split("\\s+");
            radii[i] = Double.parseDouble(parts[0]);
        }

        List<String> dynamicLines = Files.readAllLines(dynamicPath);

        List<Particle> particles = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            String[] parts = dynamicLines.get(i + 1).trim().split("\\s+");
            double x = Double.parseDouble(parts[0]);
            double y = Double.parseDouble(parts[1]);
            particles.add(new Particle(i + 1, x, y, radii[i]));
        }

        return new SimulationInput(n, l, particles);
    }
}