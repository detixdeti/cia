package de.hska.bib;

import java.time.LocalDate;

/** Ein angemeldetes Mitglied der Bibliothek. */
public class Mitglied {

    private final String nummer;
    private String name;
    private String email;
    private final boolean ermaessigt;
    private final LocalDate beitritt;
    private LocalDate mitgliedschaftBis;
    private boolean gesperrt;

    public Mitglied(String nummer, String name, String email, boolean ermaessigt) {
        this.nummer = nummer;
        this.name = name;
        this.email = email;
        this.ermaessigt = ermaessigt;
        this.beitritt = LocalDate.now();
        this.mitgliedschaftBis = beitritt.plusYears(1);
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

    public String getEmail() {
        return email;
    }

    public boolean hatEmail() {
        return email != null && !email.isBlank();
    }

    public boolean istErmaessigt() {
        return ermaessigt;
    }

    public LocalDate getMitgliedschaftBis() {
        return mitgliedschaftBis;
    }

    public boolean istMitgliedschaftGueltig(LocalDate stichtag) {
        return !stichtag.isAfter(mitgliedschaftBis);
    }

    public void mitgliedschaftVerlaengern(int jahre) {
        LocalDate basis = mitgliedschaftBis.isBefore(LocalDate.now()) ? LocalDate.now() : mitgliedschaftBis;
        mitgliedschaftBis = basis.plusYears(jahre);
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
