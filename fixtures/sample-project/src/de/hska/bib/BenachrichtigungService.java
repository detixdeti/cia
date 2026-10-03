package de.hska.bib;

import java.util.ArrayList;
import java.util.List;

/** Versendet E-Mails an Mitglieder. In dieser Version werden sie nur gesammelt. */
public class BenachrichtigungService {

    private final Konfiguration konfiguration;
    private final List<String> versendet = new ArrayList<>();

    public BenachrichtigungService(Konfiguration konfiguration) {
        this.konfiguration = konfiguration;
    }

    /** Liefert false, wenn das Mitglied keine E-Mail-Adresse hinterlegt hat. */
    public boolean senden(Mitglied mitglied, String betreff, String text) {
        if (!mitglied.hatEmail()) {
            return false;
        }
        versendet.add(String.format(
                "Von: %s | An: %s | %s | %s", konfiguration.getAbsenderAdresse(), mitglied.getEmail(), betreff, text));
        return true;
    }

    public List<String> getVersendet() {
        return new ArrayList<>(versendet);
    }
}
