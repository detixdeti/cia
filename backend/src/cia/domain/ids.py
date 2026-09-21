"""Typisierte Kennungen.

Konzept Abschnitt 4.2 verlangt, Identitaet, Version und Position als getrennte
Merkmale zu fuehren. Nackte Zeichenketten wuerden diese Unterscheidung
verwischen, weil sich eine Use-Case-Kennung dann versehentlich dort einsetzen
laesst, wo eine Klassenkennung erwartet wird. Die folgenden Typen sind zur
Laufzeit weiterhin Zeichenketten, werden vom Typpruefer aber unterschieden.
"""

from __future__ import annotations

from typing import NewType

#: Stabile Kennung eines Use Cases, z. B. ``UC1``. Sie ueberdauert Aenderungen
#: an Bezeichnung und Text (Konzept 4.2).
UseCaseId = NewType("UseCaseId", str)

#: Kennung einer Klasse. Im bereitgestellten Beispielsystem reicht der
#: Dateiname aus (Konzept 4.2); der Typ erlaubt spaeter voll qualifizierte
#: Namen, ohne die Aufrufstellen zu aendern.
ClassId = NewType("ClassId", str)

#: Kennung eines importierten Projektstands. Alle Artefakte eines Imports
#: teilen sich genau eine solche Kennung.
BaselineId = NewType("BaselineId", str)

#: Kennung eines Szenarios. Ein Szenario verweist auf genau eine Baseline und
#: veraendert diese nie.
ScenarioId = NewType("ScenarioId", str)
