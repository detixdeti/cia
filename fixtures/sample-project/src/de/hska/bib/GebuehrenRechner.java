package de.hska.bib;

/** Berechnet Saeumnisgebuehren. */
public class GebuehrenRechner {

    private static final double SATZ_PRO_TAG = 0.20;
    private static final double HOECHSTBETRAG = 15.00;
    private static final double ERMAESSIGUNG = 0.5;

    public double gebuehr(long tageUeberfaellig) {
        if (tageUeberfaellig <= 0) {
            return 0.0;
        }
        double betrag = tageUeberfaellig * SATZ_PRO_TAG;
        return Math.min(betrag, HOECHSTBETRAG);
    }

    public double gebuehr(long tageUeberfaellig, boolean ermaessigt) {
        double betrag = gebuehr(tageUeberfaellig);
        return ermaessigt ? betrag * (1.0 - ERMAESSIGUNG) : betrag;
    }

    public boolean sperreFaellig(double offeneGebuehren) {
        return offeneGebuehren >= HOECHSTBETRAG;
    }
}
