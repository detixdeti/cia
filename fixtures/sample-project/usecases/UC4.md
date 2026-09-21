# UC4: Mahnung erzeugen

Ziel: Fuer ueberfaellige Ausleihen werden Mahnungen erstellt.

Vorbedingung: Es existieren offene Ausleihen, deren Leihfrist ueberschritten ist.

Ablauf:
1. Der Mitarbeiter startet den Mahnlauf zu einem Stichtag.
2. Das System ermittelt alle offenen Ausleihen.
3. Fuer jede ueberfaellige Ausleihe berechnet das System die Saeumnisgebuehr.
4. Das System erzeugt einen Mahntext mit Mitglied, Titel, Tagen und Betrag.
5. Erreicht die Gebuehr den Hoechstbetrag, sperrt das System das Mitglied.

Erfolgsbedingung: Zu jeder ueberfaelligen Ausleihe liegt ein Mahntext vor.

Regel: Die Leihfrist betraegt 28 Tage. Die Gebuehr betraegt 0,20 EUR je Tag und
ist auf 15,00 EUR begrenzt.
