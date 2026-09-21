package de.hska.bib;

import java.time.LocalDate;

/** Ein angemeldetes Mitglied der Bibliothek. */
public class Mitglied {

    private final String nummer;
    private String name;
    private LocalDate beitritt;
    private boolean gesperrt;

    public Mitglied(String nummer, String name) {
        this.nummer = nummer;
        this.name = name;
        this.beitritt = LocalDate.now();
        this.gesperrt = false;
    }

    public String getNummer() {
        return nummer;
    }

    public String getName() {
        return name;
    }

    public void umbenennen(String name) {
        this.name = name;
    }

    public boolean istGesperrt() {
        return gesperrt;
    }

    public void sperren() {
        this.gesperrt = true;
    }

    public void entsperren() {
        this.gesperrt = false;
    }
}
