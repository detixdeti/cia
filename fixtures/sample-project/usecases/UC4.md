# UC4: Mahnung erzeugen

Ziel: Fuer ueberfaellige Ausleihen werden Mahnungen erstellt.

Vorbedingung: Es existieren offene Ausleihen, deren Leihfrist ueberschritten ist.

Ablauf:
1. Der Mitarbeiter startet den Mahnlauf zu einem Stichtag.
2. Das System ermittelt alle offenen Ausleihen.
3. Fuer jede ueberfaellige Ausleihe berechnet das System die Saeumnisgebuehr
   und bucht sie auf das Gebuehrenkonto des Mitglieds.
4. Das System erzeugt einen Mahntext mit Mitglied, Titel, Tagen und Betrag.
5. Erreichen die offenen Gebuehren des Mitglieds den Hoechstbetrag, sperrt das
   System das Mitglied.

Erfolgsbedingung: Zu jeder ueberfaelligen Ausleihe liegt ein Mahntext vor und
die Gebuehr ist gebucht. Ein erneuter Mahnlauf ersetzt die Gebuehr, statt sie
doppelt zu buchen.

Regel: Die Gebuehr betraegt 0,20 EUR je Tag und ist auf 15,00 EUR je Ausleihe
begrenzt. Ermaessigte Mitglieder zahlen die Haelfte.
