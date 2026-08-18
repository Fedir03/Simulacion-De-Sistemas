package ar.edu.itba.sds.tp2.engine;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class PeriodicBoundaryTest {

    private static final double L = 10.0;
    private static final double DELTA = 1e-9;

    @Test
    void withinNormalRange() {
        assertEquals(5.0, PeriodicBoundary.wrap(5.0, L), DELTA);
    }

    @Test
    void atUpperBoundary() {
        assertEquals(0.0, PeriodicBoundary.wrap(10.0, L), DELTA);
    }

    @Test
    void atLowerBoundary() {
        assertEquals(0.0, PeriodicBoundary.wrap(0.0, L), DELTA);
    }

    @Test
    void pastOneLap() {
        assertEquals(5.0, PeriodicBoundary.wrap(15.0, L), DELTA);
    }

    @Test
    void negativeLessThanOneLap() {
        assertEquals(7.0, PeriodicBoundary.wrap(-3.0, L), DELTA);
    }

    @Test
    void negativeMoreThanOneLap() {
        assertEquals(7.0, PeriodicBoundary.wrap(-23.0, L), DELTA);
        assertEquals(PeriodicBoundary.wrap(-3.0, L), PeriodicBoundary.wrap(-23.0, L), DELTA);
    }
}