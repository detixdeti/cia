package de.hska.bib;

/** Ein Titel im Bestand mit seinen Exemplaren. */
public class Buch {

    private final String isbn;
    private final String titel;
    private final String autor;
    private int exemplare;
    private int verfuegbareExemplare;

    public Buch(String isbn, String titel, String autor, int exemplare) {
        this.isbn = isbn;
        this.titel = titel;
        this.autor = autor;
        this.exemplare = exemplare;
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

    public int getExemplare() {
        return exemplare;
    }

    public int getVerfuegbareExemplare() {
        return verfuegbareExemplare;
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

    public void exemplareHinzufuegen(int anzahl) {
        exemplare += anzahl;
        verfuegbareExemplare += anzahl;
    }

    /** Nimmt ein verfuegbares Exemplar dauerhaft aus dem Bestand. */
    public void aussondern() {
        if (verfuegbareExemplare <= 0) {
            throw new IllegalStateException("Nur ein verfuegbares Exemplar kann ausgesondert werden");
        }
        exemplare--;
        verfuegbareExemplare--;
    }
}
