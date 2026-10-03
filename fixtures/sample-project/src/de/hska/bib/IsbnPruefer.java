package de.hska.bib;

/** Prueft ISBN-13-Nummern anhand ihrer Pruefziffer. */
public class IsbnPruefer {

    public String normalisieren(String isbn) {
        return isbn.replace("-", "").replace(" ", "");
    }

    public boolean istGueltig(String isbn) {
        String ziffern = normalisieren(isbn);
        if (ziffern.length() != 13 || !ziffern.chars().allMatch(Character::isDigit)) {
            return false;
        }
        int summe = 0;
        for (int i = 0; i < 12; i++) {
            int ziffer = ziffern.charAt(i) - '0';
            summe += (i % 2 == 0) ? ziffer : ziffer * 3;
        }
        int pruefziffer = (10 - summe % 10) % 10;
        return pruefziffer == ziffern.charAt(12) - '0';
    }
}
