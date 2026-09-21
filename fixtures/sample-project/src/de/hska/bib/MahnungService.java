package de.hska.bib;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/** Erzeugt Mahnungen fuer ueberfaellige Ausleihen. */
public class MahnungService {

    private final AusleihService ausleihService;
    private final GebuehrenRechner rechner;

    public MahnungService(AusleihService ausleihService, GebuehrenRechner rechner) {
        this.ausleihService = ausleihService;
        this.rechner = rechner;
    }

    public List<String> mahnungenErzeugen(LocalDate stichtag) {
        List<String> mahnungen = new ArrayList<>();
        for (Ausleihe a : ausleihService.alleOffenen()) {
            long tage = a.tageUeberfaellig(stichtag);
            if (tage > 0) {
                double betrag = rechner.gebuehr(tage);
                mahnungen.add(text(a, tage, betrag));
                if (rechner.sperreFaellig(betrag)) {
                    a.getMitglied().sperren();
                }
            }
        }
        return mahnungen;
    }

    private String text(Ausleihe ausleihe, long tage, double betrag) {
        return String.format(
                "Mahnung fuer %s: %s ist seit %d Tagen ueberfaellig, Gebuehr %.2f EUR",
                ausleihe.getMitglied().getName(),
                ausleihe.getBuch().getTitel(),
                tage,
                betrag);
    }
}
