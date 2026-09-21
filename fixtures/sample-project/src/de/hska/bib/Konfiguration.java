package de.hska.bib;

/**
 * Technische Einstellungen.
 *
 * <p>Diese Klasse hat bewusst keine deklarierte Zuordnung in der Linkdatei.
 * Sie dient als Testfall fuer den Befund "nicht zugeordnet" aus Konzept 4.13:
 * Aus dem Fehlen eines Links folgt nicht, dass die Klasse von Aenderungen
 * unberuehrt bleibt.
 */
public class Konfiguration {

    private final String datenbankUrl;
    private final int zeitlimitSekunden;

    public Konfiguration(String datenbankUrl, int zeitlimitSekunden) {
        this.datenbankUrl = datenbankUrl;
        this.zeitlimitSekunden = zeitlimitSekunden;
    }

    public String getDatenbankUrl() {
        return datenbankUrl;
    }

    public int getZeitlimitSekunden() {
        return zeitlimitSekunden;
    }
}
