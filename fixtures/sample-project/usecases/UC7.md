# UC7: Ausleihe verlaengern

Ziel: Ein Mitglied behaelt ein entliehenes Buch laenger.

Vorbedingung: Die Ausleihe ist offen und noch nicht ueberfaellig.

Ablauf:
1. Das Mitglied oder der Mitarbeiter waehlt die offene Ausleihe aus.
2. Das System prueft, ob die Hoechstzahl an Verlaengerungen erreicht ist.
3. Das System prueft, ob der Titel von einer anderen Person vorgemerkt ist.
4. Das System verschiebt das Faelligkeitsdatum.

Erfolgsbedingung: Das Faelligkeitsdatum liegt 14 Tage spaeter.

Regeln: Eine Ausleihe kann hoechstens zweimal verlaengert werden. Vorgemerkte
Titel koennen nicht verlaengert werden. Ueberfaellige Ausleihen koennen nicht
verlaengert werden.
