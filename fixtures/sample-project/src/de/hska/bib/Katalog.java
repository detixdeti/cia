package de.hska.bib;

import java.util.ArrayList;
import java.util.List;

/** Durchsuchbarer Bestand. */
public class Katalog {

    private final List<Buch> buecher = new ArrayList<>();

    public void aufnehmen(Buch buch) {
        buecher.add(buch);
    }

    public List<Buch> suche(String titelFragment) {
        List<Buch> treffer = new ArrayList<>();
        for (Buch b : buecher) {
            if (b.getTitel().toLowerCase().contains(titelFragment.toLowerCase())) {
                treffer.add(b);
            }
        }
        return treffer;
    }

    public List<Buch> suche(String titelFragment, String autorFragment) {
        List<Buch> treffer = new ArrayList<>();
        for (Buch b : suche(titelFragment)) {
            if (b.getAutor().toLowerCase().contains(autorFragment.toLowerCase())) {
                treffer.add(b);
            }
        }
        return treffer;
    }

    public List<Buch> nurVerfuegbare(List<Buch> eingabe) {
        List<Buch> treffer = new ArrayList<>();
        for (Buch b : eingabe) {
            if (b.istVerfuegbar()) {
                treffer.add(b);
            }
        }
        return treffer;
    }
}
