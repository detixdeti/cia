package de.hska.bib;

/** Ein Titel im Bestand. */
public class Buch {

    private final String isbn;
    private final String titel;
    private final String autor;
    private int verfuegbareExemplare;

    public Buch(String isbn, String titel, String autor, int exemplare) {
        this.isbn = isbn;
        this.titel = titel;
        this.autor = autor;
        this.verfuegbareExemplare = exemplare;
    }

    public String getIsbn() {
        return isbn;
    }

    public String getTitel() {
        return titel;
    }

    public String getAutor() {
        return autor;
    }

    public boolean istVerfuegbar() {
        return verfuegbareExemplare > 0;
    }

    public void entnehmen() {
        if (verfuegbareExemplare <= 0) {
            throw new IllegalStateException("Kein Exemplar verfuegbar");
        }
        verfuegbareExemplare--;
    }

    public void zurueckstellen() {
        verfuegbareExemplare++;
    }
}
