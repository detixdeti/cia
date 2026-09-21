# Prototyp zur graphbasierten Change Impact Analysis

Werkzeug zur interaktiven Beurteilung von Anforderungsaenderungen. Es verbindet
Use Cases, Java-Klassen und deklarierte Trace-Links zu einem Graphen und
erlaubt What-If-Analysen in beide Richtungen.

Die Abschnittsverweise in den Quelldateien beziehen sich auf Kapitel 4 der
Ausarbeitung (Konzept).

## Aufbau

    backend/src/cia/
      domain/      Artefakte, Relation T, Baseline, Szenario, Entscheidung
      review/      Abdeckung und offene Faelle, Abschluss
      importing/   Import mit Befunden statt Ausnahmen
      parsing/     Java-Parser (tree-sitter)
      analysis/    Strukturelle Auswahl, ohne LLM-Abhaengigkeit
      llm/         Modellanbindung: Schnittstelle, Mock, Analysepaket, Antwortpruefung
      api/         FastAPI: Import, Upload, Graph, Szenarien, Analyse, Entscheidungen, Protokoll
    backend/tests/ Unit- und Property-Tests
    fixtures/      Synthetisches Beispielprojekt
    frontend/      React + TypeScript, Cytoscape.js

Die Trennung zwischen `analysis/` und einer spaeteren LLM-Anbindung ist
beabsichtigt. Die Kandidatenberechnung folgt allein aus der deklarierten
Relation und ist damit reproduzierbar. Die inhaltliche Beurteilung geschieht in
einem nachgelagerten Schritt und darf die Herkunft der Kandidaten weder
ersetzen noch verdecken.

## Starten mit Docker

    docker compose up

Backend unter <http://localhost:8000/docs>, Frontend unter
<http://localhost:5173>. Der Projektstand `fixtures/sample-project` wird beim
Start importiert. Tests im Container:

    docker compose run --rm backend pytest

## Oberflaeche

Unter <http://localhost:5173>: Graph der Use Cases und Klassen, Auswahl als
Teilgraph, Szenarien anlegen, Modellanalyse, Ist-Soll-Vergleich mit
Entscheidung, Abdeckung und Abschluss. Einen neuen Ausgangsstand laedt man ueber
"Neuer Ausgangsstand" hoch (Use Cases, Java-Dateien oder -Ordner, Link-Datei);
vorher zeigt ein Import-Bericht die Befunde.

Im Docker-Betrieb laeuft der **Demo-Modus** (`CIA_LLM=demo`): Die Antworten des
Modells sind feste Beispiele, jeweils mit "[DEMO]" gekennzeichnet, und ein Banner
weist darauf hin. Sie sind keine Bewertung und duerfen nicht fuer Messungen oder
die Nutzerstudie verwendet werden. Ohne diese Variable antwortet der Mock und
bewertet nichts.

## Backend ohne Docker starten

    cd backend
    source .venv/bin/activate
    CIA_AUTOLOAD_PROJECT=../fixtures/sample-project \
      PYTHONPATH=src uvicorn cia.api.main:app --port 8000

`CIA_AUTOLOAD_PROJECT` importiert beim Start einen Projektstand. Ohne die
Variable legt `POST /api/baselines` mit `{"path": "..."}` einen an. Die
Schnittstelle ist fuer den lokalen Betrieb gedacht: Der Pfad wird ohne
Einschraenkung gelesen. Staende und Szenarien liegen nur im Arbeitsspeicher.
Interaktive Dokumentation unter `/docs`.

Das Protokoll jeder Analyse wird als Datei `protocol/<Szenario-Kennung>.jsonl`
geschrieben, eine Zeile je Eintrag (Umgebungsvariable `CIA_PROTOCOL_DIR`). Es
haelt Ausgangsstand, Auftrag, Modellanfrage, Modellantwort, Zustandswechsel und
Entscheidungen getrennt fest. Der Ordner steht in `.gitignore`, weil er
Studiendaten enthalten kann. Abruf auch per `GET /api/scenarios/{id}/protocol`.

## Tests

    cd backend
    source .venv/bin/activate
    pytest

Die Datei `tests/test_structural_properties.py` prueft die vier in Abschnitt
4.4 genannten Eigenschaften der strukturellen Auswahl ueber zufaellig erzeugte
Relationen:

1. Jede ausgegebene Kandidatenklasse hat mindestens einen Link zu einem
   geaenderten Use Case.
2. Jede ueber einen solchen Link zugeordnete Klasse kommt in der
   Kandidatenmenge vor.
3. Mehrfach vorkommende Links aendern die Menge nicht.
4. Ein zusaetzlicher Use Case im Auftrag verkleinert die Vereinigung nicht.

Diese Monotonie gilt ausdruecklich nicht fuer die inhaltliche Bewertung. Ein
zusaetzlicher Auftrag kann einen zunaechst erwarteten Anpassungsbedarf
aufheben.

## Beispielprojekt

`fixtures/sample-project` ist eine kleine Bibliotheksverwaltung mit sechs Use
Cases, acht Java-Klassen und vierzehn eindeutigen Trace-Links. Sie ersetzt das
noch ausstehende System des Lehrstuhls und ist bewusst nicht das Anmeldebeispiel
aus Kapitel 4, damit ein konstruiertes Erlaeuterungsbeispiel nicht versehentlich
als Befund erscheint.

Die Datenbasis enthaelt absichtlich mehrere Randfaelle:

- `Konfiguration.java` hat keine Zuordnung. Daraus folgt nicht, dass die Klasse
  von Aenderungen unberuehrt bleibt.
- `UC6` hat keine Zuordnung. Eine Aenderung an ihm liefert keine Kandidaten.
- `Katalog.java` haengt nur an `UC5`. Nach dessen Deaktivierung bleibt kein
  aktiver Use Case. Das Werkzeug leitet daraus keine Loeschfreigabe ab.
- `Katalog.suche` ist ueberladen und prueft die Unterscheidung nach Signatur.
- Eine Zeile der Linkdatei ist doppelt deklariert.

## Stand

Das Backend deckt den Ablauf von der Kandidatenauswahl bis zum protokollierten
Abschluss ab, in beiden Richtungen:

- Import und Pruefung (F1), Graph und Teilgraph (F2).
- Szenarien anlegen, auflisten, verwerfen und abschliessen (F3).
- Modellanalyse ueber `POST /api/scenarios/{id}/analyses`: in der
  Anforderungsrichtung je Kandidatenklasse, in der Gegenrichtung je
  Kandidaten-Use-Case (F4, F6). Solange kein echtes Modell angebunden ist,
  antwortet der Mock und bewertet nichts; alles bleibt dann offen.
- Entscheidungen zu Vorschlaegen ueber `POST /api/scenarios/{id}/decisions`:
  annehmen, verwerfen, zurueckstellen (F5).
- Abdeckung (`GET /api/scenarios/{id}/coverage`) mit getrennten Zaehlwerten:
  nicht zugeordnet, nicht verarbeitet, nicht beurteilbar und "kein Bedarf im
  betrachteten Kontext erkennbar". Abschluss ueber `POST .../close`; bestehen
  offene Faelle, muss der Anwender sie bestaetigen und begruenden.
- Protokoll (F7) als Datei je Szenario. Die Oberflaeche meldet ueber
  `POST .../events`, welche Markierungen und Vergleiche sie angezeigt hat.

Die Oberflaeche (Graph, Szenarien, Analyse, Vergleich, Entscheidung, Abdeckung,
Upload) steht und wurde im Browser durchgeklickt, allerdings nur mit dem
Demo-Anbieter. Offen sind ein echter Modellanbieter und die Speicherung von
Staenden, Szenarien und Entscheidungen (bisher nur im Arbeitsspeicher; nur das
Protokoll uebersteht einen Neustart). Nicht umgesetzt ist die
Widerspruchspruefung zwischen Vorschlaegen (Konzept 4.10 und 4.11); sie bleibt
beim Menschen.
