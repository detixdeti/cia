# Graph- und Matrixansicht – wie es funktioniert

Spickzettel für Rückfragen: vom Einlesen der Daten bis zur Darstellung von Graph, Matrix und Teilgraph.

---

## 1. Datengrundlage (Backend, Python/FastAPI)

**Eingabe je Projekt** (Ordner in `fixtures/`):
- `usecases/` – eine Datei pro Use Case, **Dateiname = Kennung** (`UC1.md`, `UC10S1.txt`)
- `src/` – Java-Quellen, **Dateiname = Klassenkennung** (`Buch.java`)
- `tracelinks.txt` – eine Zuordnung pro Zeile: `UC1 -> Buch.java`, `#` leitet Kommentare ein

**Import (`project_loader.py`):**
- Use Cases: Text einlesen; bei Markdown wird die erste Zeile `# UC1: Titel` per Regex als Titel erkannt, Plaintext-Use-Cases (iTrust) haben keinen Titel.
- Klassen: alle `*.java` rekursiv; der **Dateiname ist die Kennung**. Kommt ein Dateiname doppelt vor, ist die Kennung mehrdeutig → Warnung, Links darauf werden ignoriert.
- Trace-Links: jede Zeile per Regex `^(\S+)\s*->\s*(\S+)$` zerlegen und prüfen:
  - Format nicht erkannt → Warnung
  - Use Case oder Klasse existiert nicht → Warnung, Link wird verworfen
  - **Doppelter Link** → wird zusammengefasst (kein zusätzliches Gewicht), Warnung
- Sortierung „natürlich“: `UC2` vor `UC10`.
- Ergebnis über REST: `GET /api/projects/{id}` liefert `useCases`, `classes`, `links`, `warnings` als JSON.
- Die Warnungen erscheinen im Frontend als „Hinweis beim Import“.

**Formal (wie in Kap. 2 der Arbeit):**
- U = Use Cases, C = Klassen, Trace-Links T ⊆ U × C
- Graph G = (U ∪ C, T) ist **bipartit**: Kanten nur zwischen Use Case und Klasse, nie UC–UC oder Klasse–Klasse.
- Matrix: Zeile = Use Case, Spalte = Klasse, Eintrag = 1 genau dann, wenn (u, c) ∈ T.
- **Graph und Matrix sind zwei Darstellungen derselben Relation T.**

---

## 2. Gemeinsames Datenmodell im Frontend (React + TypeScript)

Datei: `cia-fe/src/mapping/mappingModel.ts`

- Jedes Artefakt hat einen **Schlüssel**: `uc:UC1` bzw. `class:Buch.java` (damit Use Cases und Klassen nie kollidieren).
- **Nachbarschaftsliste** (`buildNeighbors`): Aus allen Links wird eine Map `Schlüssel → Menge der Nachbarn` gebaut, **in beide Richtungen** (UC → Klassen und Klasse → UCs).
  - Damit sind beide Navigationsrichtungen dieselbe Operation: Nachbarn nachschlagen.
  - Nachbarn eines Use Case u = C₀(u), Nachbarn einer Klasse c = U(c).
- **Knotengrad** = Anzahl der Nachbarn (wird in der Matrix als Σ angezeigt) – reine Orientierung, **keine Bewertung**.

**Eine zentrale Funktion `computeMappingView`** berechnet aus Projekt + aktuellem Zustand, was angezeigt wird:
- Eingabe: Auswahl (Menge von Schlüsseln), Teilgraph an/aus, „indirekte Nachbarn“ an/aus, „Elemente ohne Zuordnung“ an/aus
- Ausgabe: sichtbare Use Cases, Klassen, Links und für jedes Element einen **Hervorhebungszustand**

**Hervorhebungszustände:**
| Zustand | Bedeutung |
|---|---|
| `selected` | vom Anwender ausgewählt |
| `linked` | direkt über einen Trace-Link mit der Auswahl verbunden (1. Schritt) |
| `indirect` | Nachbar eines verknüpften Elements (2. Schritt), nur wenn eingeschaltet |
| `dimmed` | es ist etwas ausgewählt, das Element hängt aber nicht damit zusammen |
| `normal` | nichts ausgewählt |

**Warum ein gemeinsames Modell?**
- Graph und Matrix bekommen **dasselbe berechnete Objekt** → sie zeigen immer dieselben Daten und dieselbe Auswahl, ohne dass sie sich gegenseitig kennen.
- Der Zustand (Auswahl, Schalter) liegt einmal in `MappingView`; Klick im Graph oder in der Matrix ändert diesen Zustand → beide Ansichten rendern neu.
- Berechnung mit `useMemo`, läuft nur bei Änderungen.

---

## 3. Graph-Ansicht

Datei: `cia-fe/src/mapping/TraceGraph.tsx` · Bibliothek: **React Flow** (`@xyflow/react` v12)

**Layout – bewusst selbst berechnet, kein Force-Layout:**
- Use Cases in der **linken Spalte** (x = 0), Klassen in der **rechten Spalte** (x = 520).
- Zeilenabstand 58 px, Knoten 260 × 44 px; Reihenfolge = sortierte Reihenfolge aus dem Import.
- Die kürzere Spalte wird vertikal zentriert; ist der Graph zu hoch (> 16 Zeilen), beginnen beide Spalten oben.
- **Begründung:** Bei Force-Layouts (z. B. ForceAtlas2) haben Positionen keine fachliche Bedeutung, wirken aber so (Nähe = Abhängigkeit?). Das zweispaltige Layout bildet die bipartite Struktur direkt ab und vermeidet diese Fehldeutung. Außerdem ist es stabil: Elemente springen nicht bei jeder Änderung.

**Knoten (eigene Komponente `ArtifactNode`):**
- Farbiger Balken links = **Artefakttyp** (violett = Use Case, türkis = Klasse).
- Rahmen/Hintergrund = **Hervorhebungszustand** (Typ und Zustand sind getrennt codiert).
- Ausgewählt: farbiger Rahmen + Hintergrund; verknüpft: farbiger Rahmen; indirekt: gestrichelt; abgedunkelt: 30 % Deckkraft.
- **Ohne Zuordnung**: gestrichelter Rahmen + Beschriftung „keine Zuordnung“ (bewusst „keine Entwarnung“: fehlender Link heißt nicht „nicht betroffen“).
- Zustände haben immer auch eine **Textbeschriftung**, nicht nur Farbe.

**Kanten:**
- Bézier-Kurve von der rechten Seite des Use Case zur linken Seite der Klasse.
- Stil je Zustand: an der Auswahl hängend = Primärfarbe, dicker, im Vordergrund; indirekt = gestrichelt; abgedunkelt = fast transparent.

**Ansicht (Viewport):**
- Ändert sich die Menge der sichtbaren Knoten (z. B. Teilgraph an/aus), wird der Graph **von oben** eingepasst – höchstens 16 Zeilen, damit die Schrift lesbar bleibt; der Rest ist per Scrollen erreichbar.
- Mausrad = scrollen (`panOnScroll`), Zoom über die Buttons oder Pinch; „Einpassen“ zeigt alles.
- Wird die Fläche schmaler (Detailpanel geht auf), wird der Zoom so angepasst, dass beide Spalten sichtbar bleiben, ohne die aktuelle Zeile zu verlieren.

**Interaktion:**
- Klick = auswählen, erneuter Klick = abwählen
- **Umschalt + Klick** = Mehrfachauswahl (zur Auswahl hinzufügen/entfernen)
- **Doppelklick** = Teilgraph um diesen Knoten öffnen
- Klick ins Leere = Auswahl aufheben
- Suche (MUI Autocomplete, gruppiert nach Use Cases/Klassen): wählt das Element aus und zoomt hin

---

## 4. Matrix-Ansicht

Datei: `cia-fe/src/mapping/TraceMatrix.tsx`

**Aufbau:**
- Zeilen = Use Cases, Spalten = Klassen, Zelle = **gefülltes Quadrat**, wenn ein Trace-Link existiert, sonst ein kleiner Punkt.
- Klassennamen in der Kopfzeile **senkrecht** (CSS `writing-mode: vertical-rl`, um 180° gedreht), damit viele Spalten passen.
- **Σ-Spalte und Σ-Zeile** = Knotengrad (Anzahl der Links je Use Case bzw. Klasse) – bezieht sich immer auf alle Links, auch wenn gefiltert ist.
- Kopfzeile und erste Spalte sind **fixiert** (`position: sticky`) – beim Scrollen bleiben Namen sichtbar.

**Technische Entscheidung:**
- Bewusst eine **einfache HTML-Tabelle** statt MUI-Tabellenkomponenten: iTrust hat 131 × 226 ≈ 30 000 Zellen; schwere Komponenten pro Zelle wären zu langsam. Styling läuft über CSS-Klassen am Container.
- Fixierte Kopfzellen brauchen einen deckenden Hintergrund (sonst scheinen Zellen beim Scrollen durch): die Hervorhebungsfarbe wird deshalb als Verlauf über die Hintergrundfarbe gelegt, abgedunkelt wird nur die Schriftfarbe.

**Hervorhebung (gleiche Zustände wie im Graph):**
- Ausgewählte Zeile/Spalte: kräftig eingefärbt; verknüpfte: leicht eingefärbt; nicht zugehörige: graue Schrift.
- Zellen in der Zeile/Spalte der Auswahl: Link-Quadrat in Primärfarbe mit Ring.

**Interaktion:**
- Klick auf Zeilen- oder Spaltenkopf = Use Case bzw. Klasse auswählen (Umschalt = Mehrfachauswahl)
- Klick auf eine Zelle = Use Case der Zeile auswählen
- Suche scrollt Zeile/Spalte in die Mitte (nicht hinter die fixierten Köpfe)

---

## 5. Teilgraph

- Button **„Teilgraph“** (nur aktiv, wenn etwas ausgewählt ist) oder Doppelklick auf einen Knoten.
- Sichtbar bleiben: **Auswahl + direkt verknüpfte Elemente** – also alles, was nicht `dimmed` ist.
  - Use Case gewählt → Use Case + seine Klassen (C₀(u))
  - Klasse gewählt → Klasse + ihre Use Cases (U(c))
- Optional **„Indirekte Nachbarn“**: zusätzlich der zweite Schritt, z. B. bei einem Use Case die *anderen* Use Cases, die dieselben Klassen nutzen.
  - Werden **gestrichelt** dargestellt – bewusst: Eine gemeinsame Klasse bedeutet nur einen Graphpfad (Erreichbarkeit), **keine fachliche Abhängigkeit** (Unterscheidung Erreichbarkeit vs. Betroffenheit aus Kap. 2.4).
  - Keine unbeschränkte transitive Ausbreitung – sonst würden zentrale Klassen (z. B. `AuthDAO` in iTrust mit 32 Use Cases) fast den ganzen Graph markieren.
- Der Teilgraph gilt **gleichzeitig für die Matrix** (gleiches Modell) – sie zeigt dann nur die betroffenen Zeilen und Spalten.
- „Gesamtgraph“ bzw. Klick ins Leere führt zurück.
- Mehrfachauswahl + Teilgraph = Vereinigung der Nachbarschaften mehrerer Elemente.

---

## 6. Filter „Elemente ohne Zuordnung“

- Standardmäßig an: Use Cases/Klassen ohne Link werden gezeigt (gestrichelt, „keine Zuordnung“).
- Ausgeschaltet: sie verschwinden aus Graph und Matrix – hilfreich bei großen Projekten (iTrust: 139 von 226 Klassen ohne Link).
- Ein ausgewähltes Element bleibt immer sichtbar.

---

## 7. Detailansicht (rechts)

- **Use Case:** Titel und vollständiger Text.
- **Klasse:** Quelltext mit Zeilennummern (`GET /api/projects/{id}/classes/{klasse}`).
- Das Panel ist in der Breite ziehbar, die Breite wird gespeichert.

---

## 8. Technologie-Stack (kurz)

| Bereich | Technik |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| Java-Parsing | tree-sitter (Methoden/Felder mit Zeilenbereichen, robust auch bei nicht kompilierendem Code) |
| Frontend | React 19, TypeScript, Vite |
| UI | MUI (Material UI), heller/dunkler Modus |
| Graph | React Flow (`@xyflow/react`) mit eigenem Spalten-Layout |
| Matrix | eigene HTML-Tabelle |
| Betrieb | Docker Compose: Backend-Container + nginx-Container (liefert Frontend aus, leitet `/api` ans Backend weiter) |

---

## 9. Mögliche Rückfragen – kurze Antworten

- **Warum React Flow und nicht D3/Cytoscape?** React Flow passt direkt zu React (Knoten sind React-Komponenten mit MUI-Styling), bringt Zoom/Pan/Kanten mit, und das Layout kann ich vollständig selbst bestimmen.
- **Warum kein automatisches Graph-Layout?** Positionen sollen keine Bedeutung vortäuschen; zwei Spalten bilden die bipartite Relation exakt ab und bleiben stabil.
- **Wie bleiben Graph und Matrix synchron?** Ein gemeinsamer Zustand in einer Elternkomponente, eine Berechnungsfunktion, beide Ansichten bekommen dasselbe Ergebnis.
- **Was passiert mit doppelten oder fehlerhaften Links?** Doppelte werden zusammengefasst, unbekannte Kennungen verworfen – beides wird als Importhinweis angezeigt.
- **Warum sind indirekte Nachbarn gestrichelt?** Weil ein gemeinsamer Nachbar nur Erreichbarkeit zeigt, nicht, dass eine Änderung tatsächlich weiterwirkt.
- **Skaliert das?** Getestet mit iTrust (131 Use Cases, 226 Klassen, 286 Links): Graph mit Scrollen und Teilgraph, Matrix als leichte HTML-Tabelle mit fixierten Köpfen.
- **Bedeutet ein fehlender Link, dass eine Klasse nicht betroffen ist?** Nein – deshalb die Kennzeichnung „keine Zuordnung (keine Entwarnung)“.
