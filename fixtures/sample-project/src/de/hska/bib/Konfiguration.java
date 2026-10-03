package de.hska.bib;

/**
 * Technische Einstellungen.
 *
 * <p>Diese Klasse hat bewusst keine deklarierte Zuordnung in der Linkdatei,
 * wird aber vom BenachrichtigungService verwendet. Sie zeigt den Befund
 * "nicht zugeordnet": Aus dem Fehlen eines Links folgt nicht, dass die Klasse
 * von Aenderungen unberuehrt bleibt.
 */
public class Konfiguration {

    private final String datenbankUrl;
    private final int zeitlimitSekunden;
    private final String absenderAdresse;

    public Konfiguration(String datenbankUrl, int zeitlimitSekunden, String absenderAdresse) {
        this.datenbankUrl = datenbankUrl;
        this.zeitlimitSekunden = zeitlimitSekunden;
        this.absenderAdresse = absenderAdresse;
    }

    public String getDatenbankUrl() {
        return datenbankUrl;
    }

    public int getZeitlimitSekunden() {
        return zeitlimitSekunden;
    }

    public String getAbsenderAdresse() {
        return absenderAdresse;
    }
}
