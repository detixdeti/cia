package de.hska.bib;

import java.util.LinkedHashMap;
import java.util.Map;

/** Nimmt neue Mitglieder auf und findet bestehende. */
public class MitgliederVerwaltung {

    private final Map<String, Mitglied> mitglieder = new LinkedHashMap<>();

    public Mitglied anlegen(String nummer, String name, String email, boolean ermaessigt) {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("Name fehlt");
        }
        if (mitglieder.containsKey(nummer)) {
            throw new IllegalStateException("Mitgliedsnummer ist bereits vergeben");
        }
        if (email != null && !email.isBlank() && !email.contains("@")) {
            throw new IllegalArgumentException("E-Mail-Adresse ist ungueltig");
        }
        Mitglied mitglied = new Mitglied(nummer, name, email, ermaessigt);
        mitglieder.put(nummer, mitglied);
        return mitglied;
    }

    public Mitglied finden(String nummer) {
        return mitglieder.get(nummer);
    }
}
