package de.hska.bib;

import java.time.LocalDate;

/** Erinnert Mitglieder kurz vor Ablauf der Leihfrist. */
public class ErinnerungService {

    private static final int TAGE_VOR_FAELLIGKEIT = 3;

    private final AusleihService ausleihService;
    private final BenachrichtigungService benachrichtigung;

    public ErinnerungService(AusleihService ausleihService, BenachrichtigungService benachrichtigung) {
        this.ausleihService = ausleihService;
        this.benachrichtigung = benachrichtigung;
    }

    /** Liefert die Anzahl der versendeten Erinnerungen. */
    public int erinnerungenVersenden(LocalDate heute) {
        int versendet = 0;
        for (Ausleihe a : ausleihService.alleOffenen()) {
            if (a.faelligAm().equals(heute.plusDays(TAGE_VOR_FAELLIGKEIT))) {
                boolean ok = benachrichtigung.senden(
                        a.getMitglied(),
                        "Erinnerung: Rueckgabe in " + TAGE_VOR_FAELLIGKEIT + " Tagen",
                        String.format("%s ist am %s faellig.", a.getBuch().getTitel(), a.faelligAm()));
                if (ok) {
                    versendet++;
                }
            }
        }
        return versendet;
    }
}
