package de.hska.bib;

import java.util.LinkedHashMap;
import java.util.Map;

/** Offene Gebuehren je Mitglied. Saeumnisgebuehren werden je Ausleihe gefuehrt. */
public class GebuehrenKonto {

    // Schluessel ist die Ausleihe-Id
    private final Map<String, Posten> posten = new LinkedHashMap<>();

    /** Legt die Gebuehr einer Ausleihe fest. Ein erneuter Mahnlauf ersetzt den bisherigen Betrag. */
    public void saeumnisgebuehrFestlegen(Ausleihe ausleihe, double betrag) {
        posten.put(ausleihe.getId(), new Posten(ausleihe.getMitglied(), betrag));
    }

    public double offenerBetrag(Mitglied mitglied) {
        double summe = 0;
        for (Posten p : posten.values()) {
            if (p.mitglied == mitglied) {
                summe += p.offen;
            }
        }
        return summe;
    }

    public double offeneSumme() {
        double summe = 0;
        for (Posten p : posten.values()) {
            summe += p.offen;
        }
        return summe;
    }

    /** Verrechnet eine Zahlung mit den aeltesten Posten zuerst und liefert den nicht verbrauchten Rest. */
    public double begleichen(Mitglied mitglied, double betrag) {
        double rest = betrag;
        for (Posten p : posten.values()) {
            if (p.mitglied == mitglied && p.offen > 0 && rest > 0) {
                double verrechnet = Math.min(p.offen, rest);
                p.offen -= verrechnet;
                rest -= verrechnet;
            }
        }
        return rest;
    }

    private static class Posten {
        private final Mitglied mitglied;
        private double offen;

        Posten(Mitglied mitglied, double betrag) {
            this.mitglied = mitglied;
            this.offen = betrag;
        }
    }
}
