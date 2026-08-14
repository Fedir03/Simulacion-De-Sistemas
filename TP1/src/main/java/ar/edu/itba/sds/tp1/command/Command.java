package ar.edu.itba.sds.tp1.command;

import java.io.IOException;

public interface Command {
    void execute(String[] args) throws IOException;
}
