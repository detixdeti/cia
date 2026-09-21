"""Protokoll der Analyse fuer die spaetere Auswertung (F7, Konzept 4.13).

Das Protokoll ist eine Liste von Eintraegen, die nur angehaengt wird. Jeder
Eintrag hat eine Art (``kind``), einen Zeitpunkt und seine Daten. Eingabe,
Ausgabe und Entscheidung stehen in getrennten Eintraegen:

- ``scenario_created``   Ausgangsstand und Aenderungsauftrag
- ``state_changed``      Zustandswechsel des Szenarios (mit Zeitpunkt)
- ``model_request``      Eingabe: Prompt, Vorlagenversion, Anbieter, Einstellungen
- ``model_response``     Ausgabe: Rohantwort, gepruefte Antwort, Zeitpunkte
- ``class_not_processed``  Klasse, fuer die kein Paket gebaut werden konnte
- ``analysis_finished``  Ende eines Laufs mit den Aenderungen ohne Zuordnung
- ``analysis_aborted``   Lauf durch unerwarteten Fehler abgebrochen
- ``decision``           Entscheidung des Anwenders
- ``scenario_closed``    Abschluss mit den damals offenen Faellen
- ``ui_event``           Was die Oberflaeche dem Anwender angezeigt hat

In der Gegenrichtung tragen Anfrage und Antwort ``use_case_id`` statt
``class_id``.

Ist ein Verzeichnis angegeben, wird jeder Eintrag zusaetzlich als Zeile in die
Datei ``<Szenario-Kennung>.jsonl`` geschrieben. Die Datei uebersteht einen
Neustart, der Arbeitsspeicher nicht. Ohne Verzeichnis bleibt das Protokoll im
Arbeitsspeicher (fuer Tests).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi.encoders import jsonable_encoder

from ..llm.backward import CodeChangeRun
from ..llm.run import AnalysisRun, AnyRun


class Protocol:
    def __init__(self, directory: Path | None = None) -> None:
        self._directory = directory
        self._records: dict[str, list[dict]] = {}
        if directory is not None:
            directory.mkdir(parents=True, exist_ok=True)

    def record(self, scenario_id: str, kind: str, data: object) -> dict:
        records = self._records.setdefault(scenario_id, [])
        entry = {
            "seq": len(records) + 1,
            "time": datetime.now(timezone.utc).isoformat(),
            "scenario_id": scenario_id,
            "kind": kind,
            # Wandelt Dataclasses, Enums und Zeitpunkte in einfaches JSON um.
            "data": jsonable_encoder(data),
        }
        records.append(entry)

        if self._directory is not None:
            with open(self._directory / f"{scenario_id}.jsonl", "a", encoding="utf-8") as file:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def records(self, scenario_id: str) -> list[dict]:
        return list(self._records.get(scenario_id, []))

    def record_run(self, run: AnyRun) -> None:
        """Haelt einen Analyselauf fest, getrennt nach Eingabe und Ausgabe."""
        if isinstance(run, CodeChangeRun):
            self._record_code_change_run(run)
        else:
            self._record_class_run(run)

    def _record_class_run(self, run: AnalysisRun) -> None:
        scenario_id = run.scenario_id
        for result in run.results:
            if result.analysis is None:
                self.record(
                    scenario_id,
                    "class_not_processed",
                    {
                        "run_id": run.run_id,
                        "class_id": result.class_id,
                        "reason": result.not_processed_reason,
                    },
                )
                continue

            analysis = result.analysis
            self.record(
                scenario_id,
                "model_request",
                {
                    "run_id": run.run_id,
                    "class_id": result.class_id,
                    "provider": analysis.provider_name,
                    "settings": run.provider_settings,
                    "prompt_version": analysis.prompt_version,
                    "prompt": analysis.prompt,
                    "requested_at": analysis.requested_at,
                },
            )
            self.record(
                scenario_id,
                "model_response",
                {
                    "run_id": run.run_id,
                    "class_id": result.class_id,
                    "finished_at": analysis.finished_at,
                    "raw_response": analysis.raw_response,
                    "answer": analysis.answer,
                },
            )

        self.record(
            scenario_id,
            "analysis_finished",
            {
                "run_id": run.run_id,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "unresolved": run.unresolved,
            },
        )

    def _record_code_change_run(self, run: CodeChangeRun) -> None:
        """Wie ``_record_class_run``, aber je Use Case statt je Klasse."""
        scenario_id = run.scenario_id
        for analysis in run.results:
            self.record(
                scenario_id,
                "model_request",
                {
                    "run_id": run.run_id,
                    "use_case_id": analysis.use_case_id,
                    "provider": analysis.provider_name,
                    "settings": run.provider_settings,
                    "prompt_version": analysis.prompt_version,
                    "prompt": analysis.prompt,
                    "requested_at": analysis.requested_at,
                },
            )
            self.record(
                scenario_id,
                "model_response",
                {
                    "run_id": run.run_id,
                    "use_case_id": analysis.use_case_id,
                    "finished_at": analysis.finished_at,
                    "raw_response": analysis.raw_response,
                    "answer": analysis.answer,
                },
            )

        self.record(
            scenario_id,
            "analysis_finished",
            {
                "run_id": run.run_id,
                "started_at": run.started_at,
                "finished_at": run.finished_at,
                "unassignable_class_ids": run.unassignable_class_ids,
            },
        )
