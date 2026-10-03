# UC1: Buch ausleihen

Ziel: Ein Mitglied leiht ein verfuegbares Buch aus.

Vorbedingung: Das Mitglied ist nicht gesperrt und seine Mitgliedschaft ist gueltig.
Vom gewuenschten Titel ist mindestens ein Exemplar verfuegbar oder fuer das
Mitglied zurueckgelegt.

Ablauf:
1. Der Mitarbeiter waehlt das Mitglied aus.
2. Der Mitarbeiter waehlt den Titel aus.
3. Das System prueft, ob das Mitglied gesperrt ist.
4. Das System prueft, ob die Mitgliedschaft noch gueltig ist.
5. Das System prueft, ob das Mitglied die Hoechstzahl offener Ausleihen erreicht hat.
6. Liegt fuer das Mitglied eine bereitgestellte Vormerkung vor, gibt das System
   das zurueckgelegte Exemplar aus. Sonst entnimmt es ein Exemplar aus dem Bestand.
7. Das System legt eine Ausleihe mit dem heutigen Datum an.

Erfolgsbedingung: Eine offene Ausleihe ist angelegt.

Regeln: Ein Mitglied darf hoechstens zehn Titel gleichzeitig entliehen haben.
Die Leihfrist betraegt 28 Tage.
