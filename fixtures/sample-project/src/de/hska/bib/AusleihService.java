package de.hska.bib;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/** Fachlogik fuer Ausleihe und Rueckgabe. */
public class AusleihService {

    private static final int MAX_OFFENE_AUSLEIHEN = 10;

    private final List<Ausleihe> ausleihen = new ArrayList<>();

    public Ausleihe ausleihen(Mitglied mitglied, Buch buch) {
        if (mitglied.istGesperrt()) {
            throw new IllegalStateException("Mitglied ist gesperrt");
        }
        if (offeneAusleihen(mitglied).size() >= MAX_OFFENE_AUSLEIHEN) {
            throw new IllegalStateException("Hoechstzahl offener Ausleihen erreicht");
        }
        if (!buch.istVerfuegbar()) {
            throw new IllegalStateException("Kein Exemplar verfuegbar");
        }
        buch.entnehmen();
        Ausleihe ausleihe = new Ausleihe(naechsteId(), mitglied, buch, LocalDate.now());
        ausleihen.add(ausleihe);
        return ausleihe;
    }

    public void zurueckgeben(Ausleihe ausleihe) {
        if (!ausleihe.istOffen()) {
            throw new IllegalStateException("Ausleihe ist bereits abgeschlossen");
        }
        ausleihe.abschliessen(LocalDate.now());
        ausleihe.getBuch().zurueckstellen();
    }

    public List<Ausleihe> offeneAusleihen(Mitglied mitglied) {
        List<Ausleihe> treffer = new ArrayList<>();
        for (Ausleihe a : ausleihen) {
            if (a.istOffen() && a.getMitglied().getNummer().equals(mitglied.getNummer())) {
                treffer.add(a);
            }
        }
        return treffer;
    }

    public List<Ausleihe> alleOffenen() {
        List<Ausleihe> treffer = new ArrayList<>();
        for (Ausleihe a : ausleihen) {
            if (a.istOffen()) {
                treffer.add(a);
            }
        }
        return treffer;
    }

    private String naechsteId() {
        return "A" + (ausleihen.size() + 1);
    }
}
