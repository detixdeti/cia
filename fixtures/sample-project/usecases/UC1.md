# UC1: Buch ausleihen

Ziel: Ein Mitglied leiht ein verfuegbares Buch aus.

Vorbedingung: Das Mitglied ist angemeldet und nicht gesperrt. Vom gewuenschten
Titel ist mindestens ein Exemplar verfuegbar.

Ablauf:
1. Der Mitarbeiter waehlt das Mitglied aus.
2. Der Mitarbeiter waehlt den Titel aus.
3. Das System prueft, ob das Mitglied gesperrt ist.
4. Das System prueft, ob das Mitglied die Hoechstzahl offener Ausleihen erreicht hat.
5. Das System entnimmt ein Exemplar aus dem Bestand.
6. Das System legt eine Ausleihe mit dem heutigen Datum an.

Erfolgsbedingung: Eine offene Ausleihe ist angelegt, der verfuegbare Bestand
des Titels ist um eins verringert.

Regel: Ein Mitglied darf hoechstens zehn Titel gleichzeitig entliehen haben.
