# UC8: Titel vormerken

Ziel: Ein Mitglied reserviert einen Titel, von dem kein Exemplar verfuegbar ist.

Vorbedingung: Das Mitglied ist nicht gesperrt.

Ablauf:
1. Das Mitglied waehlt einen Titel aus.
2. Das System prueft, dass aktuell kein Exemplar verfuegbar ist.
3. Das System prueft, dass das Mitglied den Titel nicht bereits vorgemerkt hat.
4. Das System prueft die Hoechstzahl an Vormerkungen des Mitglieds.
5. Das System reiht die Vormerkung hinter bestehenden Vormerkungen ein.

Erfolgsbedingung: Die Vormerkung ist angelegt. Wer zuerst vormerkt, erhaelt
das naechste zurueckgegebene Exemplar.

Regeln: Ein Mitglied darf hoechstens fuenf Vormerkungen gleichzeitig haben.
Verfuegbare Titel koennen nicht vorgemerkt werden, sie werden direkt ausgeliehen.

Erweiterung: Das Mitglied kann eine Vormerkung jederzeit stornieren. Ein bereits
zurueckgelegtes Exemplar geht dann in den Bestand zurueck.
