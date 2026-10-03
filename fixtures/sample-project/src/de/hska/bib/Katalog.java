package de.hska.bib;

import java.util.ArrayList;
import java.util.List;

/** Der durchsuchbare Bestand der Bibliothek. */
public class Katalog {

    private static final int MINDESTLAENGE_SUCHBEGRIFF = 3;

    private final IsbnPruefer isbnPruefer;
    private final VormerkService vormerkService;
    private final List<Buch> buecher = new ArrayList<>();

    public Katalog(IsbnPruefer isbnPruefer, VormerkService vormerkService) {
        this.isbnPruefer = isbnPruefer;
        this.vormerkService = vormerkService;
    }

    /** Neuzugang: ein neuer Titel oder weitere Exemplare eines vorhandenen Titels. */
    public Buch neuzugang(String isbn, String titel, String autor, int exemplare) {
        if (!isbnPruefer.istGueltig(isbn)) {
            throw new IllegalArgumentException("ISBN ist ungueltig");
        }
        if (exemplare <= 0) {
            throw new IllegalArgumentException("Mindestens ein Exemplar angeben");
        }
        Buch vorhanden = findeIsbn(isbn);
        if (vorhanden != null) {
            vorhanden.exemplareHinzufuegen(exemplare);
            return vorhanden;
        }
        Buch buch = new Buch(isbnPruefer.normalisieren(isbn), titel, autor, exemplare);
        buecher.add(buch);
        return buch;
    }

    public void exemplarAussondern(String isbn) {
        Buch buch = findeIsbn(isbn);
        if (buch == null) {
            throw new IllegalArgumentException("Titel nicht im Bestand");
        }
        // Das letzte Exemplar bleibt, solange Personen auf den Titel warten.
        if (buch.getExemplare() == 1 && vormerkService.hatVormerkungen(buch)) {
            throw new IllegalStateException("Letztes Exemplar eines vorgemerkten Titels");
        }
        buch.aussondern();
        if (buch.getExemplare() == 0) {
            buecher.remove(buch);
        }
    }

    public Buch findeIsbn(String isbn) {
        String gesucht = isbnPruefer.normalisieren(isbn);
        for (Buch b : buecher) {
            if (b.getIsbn().equals(gesucht)) {
                return b;
            }
        }
        return null;
    }

    public List<Buch> suche(String titelFragment) {
        if (titelFragment.trim().length() < MINDESTLAENGE_SUCHBEGRIFF) {
            throw new IllegalArgumentException("Suchbegriff ist zu kurz");
        }
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
