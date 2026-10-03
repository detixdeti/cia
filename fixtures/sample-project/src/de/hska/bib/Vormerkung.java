package de.hska.bib;

import java.time.LocalDate;

/** Ein Mitglied wartet auf ein Exemplar eines Titels. */
public class Vormerkung {

    private static final int ABHOLFRIST_TAGE = 7;

    private final Mitglied mitglied;
    private final Buch buch;
    private final LocalDate angelegtAm;
    private LocalDate abholbarBis;
    private boolean abgeholt;

    public Vormerkung(Mitglied mitglied, Buch buch, LocalDate angelegtAm) {
        this.mitglied = mitglied;
        this.buch = buch;
        this.angelegtAm = angelegtAm;
    }

    public Mitglied getMitglied() {
        return mitglied;
    }

    public Buch getBuch() {
        return buch;
    }

    public LocalDate getAngelegtAm() {
        return angelegtAm;
    }

    public LocalDate getAbholbarBis() {
        return abholbarBis;
    }

    public boolean istBereitgestellt() {
        return abholbarBis != null && !abgeholt;
    }

    public boolean istAbgelaufen(LocalDate heute) {
        return istBereitgestellt() && heute.isAfter(abholbarBis);
    }

    public void bereitstellen(LocalDate heute) {
        this.abholbarBis = heute.plusDays(ABHOLFRIST_TAGE);
    }

    public void abholen() {
        this.abgeholt = true;
    }
}
