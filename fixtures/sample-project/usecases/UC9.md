# UC9: Vorgemerktes Exemplar bereitstellen

Ziel: Ein zurueckgegebenes Exemplar wird fuer die naechste wartende Person
zurueckgelegt.

Ausloeser: Ein vorgemerkter Titel wird zurueckgegeben (UC2).

Ablauf:
1. Das System ermittelt die aelteste noch wartende Vormerkung des Titels.
2. Das System legt das Exemplar fuer diese Person zurueck.
3. Das System benachrichtigt die Person per E-Mail mit dem Abholdatum.

Erfolgsbedingung: Das Exemplar ist zurueckgelegt und die Person ist informiert.

Regel: Das Exemplar liegt sieben Tage zur Abholung bereit.

Erweiterung: Wird das Exemplar nicht rechtzeitig abgeholt, verfaellt die
Vormerkung. Das Exemplar geht an die naechste wartende Person oder zurueck in
den Bestand.
