package de.hska.bib;

import java.time.YearMonth;

/** Kennzahlen eines Monats. */
public class Monatsstatistik {

    private final YearMonth monat;
    private final int ausleihen;
    private final int rueckgaben;
    private final int ueberfaellig;
    private final double offeneGebuehren;

    public Monatsstatistik(YearMonth monat, int ausleihen, int rueckgaben, int ueberfaellig, double offeneGebuehren) {
        this.monat = monat;
        this.ausleihen = ausleihen;
        this.rueckgaben = rueckgaben;
        this.ueberfaellig = ueberfaellig;
        this.offeneGebuehren = offeneGebuehren;
    }

    public YearMonth getMonat() {
        return monat;
    }

    public int getAusleihen() {
        return ausleihen;
    }

    public int getRueckgaben() {
        return rueckgaben;
    }

    public int getUeberfaellig() {
        return ueberfaellig;
    }

    public double getOffeneGebuehren() {
        return offeneGebuehren;
    }

    public String alsText() {
        return String.format(
                "%s: %d Ausleihen, %d Rueckgaben, %d ueberfaellig, %.2f EUR offene Gebuehren",
                monat, ausleihen, rueckgaben, ueberfaellig, offeneGebuehren);
    }
}
