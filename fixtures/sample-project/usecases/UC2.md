# UC2: Buch zurueckgeben

Ziel: Ein entliehenes Buch wird zurueckgenommen.

Vorbedingung: Zu dem Exemplar existiert eine offene Ausleihe.

Ablauf:
1. Der Mitarbeiter waehlt die offene Ausleihe aus.
2. Das System setzt das Rueckgabedatum auf den heutigen Tag.
3. Das System stellt das Exemplar in den Bestand zurueck.

Erfolgsbedingung: Die Ausleihe ist abgeschlossen, der verfuegbare Bestand des
Titels ist um eins erhoeht.
