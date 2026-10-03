package de.hska.bib;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/** Verwaltet Vormerkungen und stellt zurueckgegebene Exemplare bereit. */
public class VormerkService {

    private static final int MAX_VORMERKUNGEN_JE_MITGLIED = 5;

    private final BenachrichtigungService benachrichtigung;
    private final List<Vormerkung> vormerkungen = new ArrayList<>();

    public VormerkService(BenachrichtigungService benachrichtigung) {
        this.benachrichtigung = benachrichtigung;
    }

    public Vormerkung vormerken(Mitglied mitglied, Buch buch) {
        if (mitglied.istGesperrt()) {
            throw new IllegalStateException("Mitglied ist gesperrt");
        }
        if (buch.istVerfuegbar()) {
            throw new IllegalStateException("Titel ist verfuegbar und kann direkt ausgeliehen werden");
        }
        if (offeneVormerkungen(mitglied) >= MAX_VORMERKUNGEN_JE_MITGLIED) {
            throw new IllegalStateException("Hoechstzahl an Vormerkungen erreicht");
        }
        for (Vormerkung v : vormerkungen) {
            if (v.getBuch() == buch && v.getMitglied() == mitglied && !v.istBereitgestellt()) {
                throw new IllegalStateException("Titel ist bereits vorgemerkt");
            }
        }
        Vormerkung vormerkung = new Vormerkung(mitglied, buch, LocalDate.now());
        vormerkungen.add(vormerkung);
        return vormerkung;
    }

    public void stornieren(Vormerkung vormerkung) {
        vormerkungen.remove(vormerkung);
        if (vormerkung.istBereitgestellt()) {
            vormerkung.getBuch().zurueckstellen();
        }
    }

    public boolean hatVormerkungen(Buch buch) {
        return naechsteWartende(buch) != null;
    }

    /** Liefert true, wenn das Exemplar fuer eine wartende Person zurueckgelegt wurde. */
    public boolean exemplarZurueckgegeben(Buch buch, LocalDate heute) {
        Vormerkung naechste = naechsteWartende(buch);
        if (naechste == null) {
            return false;
        }
        naechste.bereitstellen(heute);
        benachrichtigung.senden(
                naechste.getMitglied(),
                "Ihre Vormerkung ist abholbereit",
                String.format("%s liegt bis %s fuer Sie bereit.", buch.getTitel(), naechste.getAbholbarBis()));
        return true;
    }

    public Vormerkung bereitgestellteVormerkung(Mitglied mitglied, Buch buch) {
        for (Vormerkung v : vormerkungen) {
            if (v.getBuch() == buch && v.getMitglied() == mitglied && v.istBereitgestellt()) {
                return v;
            }
        }
        return null;
    }

    public void abgeholt(Vormerkung vormerkung) {
        vormerkung.abholen();
        vormerkungen.remove(vormerkung);
    }

    /** Nicht abgeholte Exemplare gehen an die naechste Person oder zurueck in den Bestand. */
    public void abgelaufeneAufloesen(LocalDate heute) {
        for (Vormerkung v : new ArrayList<>(vormerkungen)) {
            if (v.istAbgelaufen(heute)) {
                vormerkungen.remove(v);
                if (!exemplarZurueckgegeben(v.getBuch(), heute)) {
                    v.getBuch().zurueckstellen();
                }
            }
        }
    }

    private Vormerkung naechsteWartende(Buch buch) {
        for (Vormerkung v : vormerkungen) {
            if (v.getBuch() == buch && !v.istBereitgestellt()) {
                return v;
            }
        }
        return null;
    }

    private int offeneVormerkungen(Mitglied mitglied) {
        int anzahl = 0;
        for (Vormerkung v : vormerkungen) {
            if (v.getMitglied() == mitglied) {
                anzahl++;
            }
        }
        return anzahl;
    }
}
