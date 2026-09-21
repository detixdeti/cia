package de.hska.bib;

import java.time.LocalDate;

/** Eine laufende oder abgeschlossene Ausleihe. */
public class Ausleihe {

    private static final int LEIHFRIST_TAGE = 28;

    private final String id;
    private final Mitglied mitglied;
    private final Buch buch;
    private final LocalDate beginn;
    private LocalDate rueckgabe;

    public Ausleihe(String id, Mitglied mitglied, Buch buch, LocalDate beginn) {
        this.id = id;
        this.mitglied = mitglied;
        this.buch = buch;
        this.beginn = beginn;
        this.rueckgabe = null;
    }

    public String getId() {
        return id;
    }

    public Mitglied getMitglied() {
        return mitglied;
    }

    public Buch getBuch() {
        return buch;
    }

    public LocalDate faelligAm() {
        return beginn.plusDays(LEIHFRIST_TAGE);
    }

    public boolean istOffen() {
        return rueckgabe == null;
    }

    public void abschliessen(LocalDate datum) {
        this.rueckgabe = datum;
    }

    public long tageUeberfaellig(LocalDate stichtag) {
        if (!istOffen()) {
            return 0;
        }
        LocalDate faellig = faelligAm();
        if (!stichtag.isAfter(faellig)) {
            return 0;
        }
        return java.time.temporal.ChronoUnit.DAYS.between(faellig, stichtag);
    }
}
