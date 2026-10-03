# UC2: Buch zurueckgeben

Ziel: Ein entliehenes Buch wird zurueckgenommen.

Vorbedingung: Zu dem Exemplar existiert eine offene Ausleihe.

Ablauf:
1. Der Mitarbeiter waehlt die offene Ausleihe aus.
2. Das System setzt das Rueckgabedatum auf den heutigen Tag.
3. Ist der Titel vorgemerkt, legt das System das Exemplar fuer die naechste
   wartende Person zurueck (siehe UC9).
4. Andernfalls stellt das System das Exemplar in den Bestand zurueck.

Erfolgsbedingung: Die Ausleihe ist abgeschlossen. Das Exemplar ist wieder
verfuegbar oder fuer eine Vormerkung zurueckgelegt.
