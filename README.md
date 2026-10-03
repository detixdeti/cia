# Change Impact Analysis – Prototyp

Prototyp zur Masterarbeit „Entwicklung eines interaktiven Ansatzes zur graphbasierten
Change Impact Analysis von Softwareanforderungen“.

- `cia-be/` – Backend (Python, FastAPI)
- `cia-fe/` – Frontend (React, TypeScript, MUI, React Flow)
- `fixtures/` – Beispielprojekte (Use Cases, Java-Quellen, `tracelinks.txt`)

## Starten

```bash
docker compose up --build
```

Danach ist die Anwendung unter http://localhost:3000 erreichbar,
die API-Dokumentation unter http://localhost:8000/docs.

Szenarien und Analyseergebnisse liegen in einer SQLite-Datei im Docker-Volume `cia-data`
und bleiben bei einem Neustart erhalten. `docker compose down -v` löscht sie.

## Sprachmodell austauschen

Alle Modelleinstellungen stehen in `.env` und werden nur in
`cia-be/app/llm_client.py` verwendet. Für ein anderes Modell reicht es, `LLM_MODEL`
(und ggf. `LLM_PROVIDER`) zu ändern. Jeder OpenAI-kompatible Endpunkt funktioniert über `LLM_BASE_URL`.

Kostenlose Modelle sind oft überlastet (HTTP 429). Der Client wiederholt solche Aufrufe
automatisch (`LLM_MAX_ATTEMPTS`), die Oberfläche zeigt die Wartezeit an.

## Entwicklung ohne Docker

```bash
# Backend
cd cia-be
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
set -a && . ../.env && set +a
.venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend (leitet /api an localhost:8000 weiter)
cd cia-fe
npm install
npm run dev
```

Formatieren und prüfen:

```bash
cd cia-be && .venv/bin/ruff check app && .venv/bin/ruff format app   # Python
cd cia-fe && npm run format && npx tsc -b                              # TypeScript
```

## Projektformat

Ein Projekt ist ein Ordner in `fixtures/` mit:

- `tracelinks.txt` – eine Zuordnung pro Zeile: `UC1 -> Buch.java`, `#` leitet Kommentare ein
- `usecases/` – eine Datei pro Use Case, der Dateiname ist die Kennung (`UC1.md`, `UC10S1.txt`)
- `src/` – Java-Quellen, der Dateiname ist die Kennung der Klasse
