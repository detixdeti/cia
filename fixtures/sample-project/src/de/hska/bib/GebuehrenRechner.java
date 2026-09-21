package de.hska.bib;

/** Berechnet Saeumnisgebuehren. */
public class GebuehrenRechner {

    private static final double SATZ_PRO_TAG = 0.20;
    private static final double HOECHSTBETRAG = 15.00;

    public double gebuehr(long tageUeberfaellig) {
        if (tageUeberfaellig <= 0) {
            return 0.0;
        }
        double betrag = tageUeberfaellig * SATZ_PRO_TAG;
        return Math.min(betrag, HOECHSTBETRAG);
    }

    public double gebuehr(long tageUeberfaellig, double rabatt) {
        double betrag = gebuehr(tageUeberfaellig);
        return betrag * (1.0 - rabatt);
    }

    public boolean sperreFaellig(double offeneGebuehren) {
        return offeneGebuehren >= HOECHSTBETRAG;
    }
}
