package de.hska.bib;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

/** Fachlogik fuer Ausleihe, Rueckgabe und Verlaengerung. */
public class AusleihService {

    private static final int MAX_OFFENE_AUSLEIHEN = 10;

    private final VormerkService vormerkService;
    private final List<Ausleihe> ausleihen = new ArrayList<>();

    public AusleihService(VormerkService vormerkService) {
        this.vormerkService = vormerkService;
    }

    public Ausleihe ausleihen(Mitglied mitglied, Buch buch) {
        LocalDate heute = LocalDate.now();
        if (mitglied.istGesperrt()) {
            throw new IllegalStateException("Mitglied ist gesperrt");
        }
        if (!mitglied.istMitgliedschaftGueltig(heute)) {
            throw new IllegalStateException("Mitgliedschaft ist abgelaufen");
        }
        if (offeneAusleihen(mitglied).size() >= MAX_OFFENE_AUSLEIHEN) {
            throw new IllegalStateException("Hoechstzahl offener Ausleihen erreicht");
        }

        // Ein fuer das Mitglied zurueckgelegtes Exemplar liegt nicht mehr im freien Bestand.
        Vormerkung bereitgestellt = vormerkService.bereitgestellteVormerkung(mitglied, buch);
        if (bereitgestellt != null) {
            vormerkService.abgeholt(bereitgestellt);
        } else {
            if (!buch.istVerfuegbar()) {
                throw new IllegalStateException("Kein Exemplar verfuegbar");
            }
            buch.entnehmen();
        }

        Ausleihe ausleihe = new Ausleihe(naechsteId(), mitglied, buch, heute);
        ausleihen.add(ausleihe);
        return ausleihe;
    }

    public void zurueckgeben(Ausleihe ausleihe) {
        if (!ausleihe.istOffen()) {
            throw new IllegalStateException("Ausleihe ist bereits abgeschlossen");
        }
        ausleihe.abschliessen(LocalDate.now());
        // Ist der Titel vorgemerkt, wird das Exemplar fuer die naechste Person zurueckgelegt.
        boolean zurueckgelegt = vormerkService.exemplarZurueckgegeben(ausleihe.getBuch(), LocalDate.now());
        if (!zurueckgelegt) {
            ausleihe.getBuch().zurueckstellen();
        }
    }

    public void verlaengern(Ausleihe ausleihe) {
        LocalDate heute = LocalDate.now();
        if (!ausleihe.kannVerlaengertWerden(heute)) {
            throw new IllegalStateException("Ausleihe kann nicht mehr verlaengert werden");
        }
        if (vormerkService.hatVormerkungen(ausleihe.getBuch())) {
            throw new IllegalStateException("Titel ist vorgemerkt und kann nicht verlaengert werden");
        }
        ausleihe.verlaengern();
    }

    public List<Ausleihe> offeneAusleihen(Mitglied mitglied) {
        List<Ausleihe> treffer = new ArrayList<>();
        for (Ausleihe a : ausleihen) {
            if (a.istOffen() && a.getMitglied().getNummer().equals(mitglied.getNummer())) {
                treffer.add(a);
            }
        }
        return treffer;
    }

    public List<Ausleihe> alleOffenen() {
        List<Ausleihe> treffer = new ArrayList<>();
        for (Ausleihe a : ausleihen) {
            if (a.istOffen()) {
                treffer.add(a);
            }
        }
        return treffer;
    }

    public List<Ausleihe> alleAusleihen() {
        return new ArrayList<>(ausleihen);
    }

    private String naechsteId() {
        return "A" + (ausleihen.size() + 1);
    }
}
