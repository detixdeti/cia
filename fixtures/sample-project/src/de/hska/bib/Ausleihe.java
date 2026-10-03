package de.hska.bib;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

/** Eine laufende oder abgeschlossene Ausleihe. */
public class Ausleihe {

    private static final int LEIHFRIST_TAGE = 28;
    private static final int VERLAENGERUNG_TAGE = 14;
    private static final int MAX_VERLAENGERUNGEN = 2;

    private final String id;
    private final Mitglied mitglied;
    private final Buch buch;
    private final LocalDate beginn;
    private LocalDate faelligAm;
    private int verlaengerungen;
    private LocalDate rueckgabe;

    public Ausleihe(String id, Mitglied mitglied, Buch buch, LocalDate beginn) {
        this.id = id;
        this.mitglied = mitglied;
        this.buch = buch;
        this.beginn = beginn;
        this.faelligAm = beginn.plusDays(LEIHFRIST_TAGE);
        this.verlaengerungen = 0;
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

    public LocalDate getBeginn() {
        return beginn;
    }

    public LocalDate getRueckgabe() {
        return rueckgabe;
    }

    public LocalDate faelligAm() {
        return faelligAm;
    }

    public boolean istOffen() {
        return rueckgabe == null;
    }

    public void abschliessen(LocalDate datum) {
        this.rueckgabe = datum;
    }

    public boolean kannVerlaengertWerden(LocalDate heute) {
        return istOffen() && verlaengerungen < MAX_VERLAENGERUNGEN && !heute.isAfter(faelligAm);
    }

    public void verlaengern() {
        faelligAm = faelligAm.plusDays(VERLAENGERUNG_TAGE);
        verlaengerungen++;
    }

    public int getVerlaengerungen() {
        return verlaengerungen;
    }

    public long tageUeberfaellig(LocalDate stichtag) {
        if (!istOffen() || !stichtag.isAfter(faelligAm)) {
            return 0;
        }
        return ChronoUnit.DAYS.between(faelligAm, stichtag);
    }
}
