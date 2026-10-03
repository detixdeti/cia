package de.hska.bib;

import java.time.LocalDate;

/** Zahlungen an der Ausleihtheke: Gebuehren begleichen und Mitgliedschaft verlaengern. */
public class KassenService {

    private final GebuehrenKonto konto;
    private final BeitragsRechner beitragsRechner;

    public KassenService(GebuehrenKonto konto, BeitragsRechner beitragsRechner) {
        this.konto = konto;
        this.beitragsRechner = beitragsRechner;
    }

    /** Teilzahlungen sind erlaubt. Gibt eine Quittung zurueck. */
    public String gebuehrenBezahlen(Mitglied mitglied, double betrag) {
        if (betrag <= 0) {
            throw new IllegalArgumentException("Betrag muss positiv sein");
        }
        double offen = konto.offenerBetrag(mitglied);
        if (offen <= 0) {
            throw new IllegalStateException("Keine offenen Gebuehren");
        }
        double rueckgeld = konto.begleichen(mitglied, betrag);
        double nochOffen = konto.offenerBetrag(mitglied);

        // Die Sperre wird erst aufgehoben, wenn alle Gebuehren beglichen sind.
        if (nochOffen <= 0 && mitglied.istGesperrt()) {
            mitglied.entsperren();
        }
        return String.format(
                "Quittung %s: %.2f EUR erhalten, %.2f EUR zurueck, noch offen %.2f EUR",
                mitglied.getNummer(), betrag, rueckgeld, nochOffen);
    }

    public String mitgliedschaftVerlaengern(Mitglied mitglied) {
        if (konto.offenerBetrag(mitglied) > 0) {
            throw new IllegalStateException("Vor der Verlaengerung muessen alle Gebuehren beglichen sein");
        }
        double beitrag = beitragsRechner.jahresbeitrag(mitglied);
        mitglied.mitgliedschaftVerlaengern(1);
        return String.format(
                "Quittung %s: Jahresbeitrag %.2f EUR, Mitgliedschaft gueltig bis %s (%s)",
                mitglied.getNummer(), beitrag, mitglied.getMitgliedschaftBis(), LocalDate.now());
    }
}
