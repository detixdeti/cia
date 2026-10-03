package de.hska.bib;

import java.time.YearMonth;

/** Erstellt die Monatsstatistik fuer die Bibliotheksleitung. */
public class StatistikService {

    private final AusleihService ausleihService;
    private final GebuehrenKonto konto;

    public StatistikService(AusleihService ausleihService, GebuehrenKonto konto) {
        this.ausleihService = ausleihService;
        this.konto = konto;
    }

    public Monatsstatistik monatsstatistik(YearMonth monat) {
        int ausleihen = 0;
        int rueckgaben = 0;
        int ueberfaellig = 0;
        for (Ausleihe a : ausleihService.alleAusleihen()) {
            if (YearMonth.from(a.getBeginn()).equals(monat)) {
                ausleihen++;
            }
            if (a.getRueckgabe() != null && YearMonth.from(a.getRueckgabe()).equals(monat)) {
                rueckgaben++;
            }
            if (a.tageUeberfaellig(monat.atEndOfMonth()) > 0) {
                ueberfaellig++;
            }
        }
        return new Monatsstatistik(monat, ausleihen, rueckgaben, ueberfaellig, konto.offeneSumme());
    }
}
