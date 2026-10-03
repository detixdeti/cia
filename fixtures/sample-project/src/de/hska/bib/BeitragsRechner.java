package de.hska.bib;

/** Berechnet den Jahresbeitrag fuer die Mitgliedschaft. */
public class BeitragsRechner {

    private static final double JAHRESBEITRAG = 12.00;
    private static final double ERMAESSIGUNG = 0.5;

    public double jahresbeitrag(Mitglied mitglied) {
        return mitglied.istErmaessigt() ? JAHRESBEITRAG * (1.0 - ERMAESSIGUNG) : JAHRESBEITRAG;
    }
}
