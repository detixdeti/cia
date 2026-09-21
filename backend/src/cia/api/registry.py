"""Haltung der importierten Staende und Szenarien im Arbeitsspeicher.

Ein Import ist nach seiner Ablage unveraenderlich (Konzept 4.2). Die Ablage
selbst ist fluechtig; nach einem Neustart sind Staende und Szenarien weg.
TODO: Persistenz festlegen, sobald die Szenarioverwaltung (F3) umgesetzt wird.
"""

from __future__ import annotations

from pathlib import Path

from ..domain.decision import Decision
from ..domain.ids import BaselineId, ScenarioId
from ..domain.scenario import Scenario
from ..importing.project import ImportReport
from ..llm.run import AnyRun
from ..review.coverage import Closure
from .protocol import Protocol


class Registry:
    def __init__(self, protocol_dir: Path | None = None) -> None:
        self._reports: dict[BaselineId, ImportReport] = {}
        self._scenarios: dict[ScenarioId, Scenario] = {}
        self._runs: dict[ScenarioId, list[AnyRun]] = {}
        self._decisions: dict[ScenarioId, list[Decision]] = {}
        self._closures: dict[ScenarioId, Closure] = {}
        self.protocol = Protocol(protocol_dir)

    def add_report(self, report: ImportReport) -> None:
        self._reports[report.baseline.id] = report

    def report(self, baseline_id: str) -> ImportReport | None:
        return self._reports.get(BaselineId(baseline_id))

    def reports(self) -> list[ImportReport]:
        return sorted(self._reports.values(), key=lambda r: r.baseline.imported_at)

    def add_scenario(self, scenario: Scenario) -> None:
        self._scenarios[scenario.id] = scenario

    def scenario(self, scenario_id: str) -> Scenario | None:
        return self._scenarios.get(ScenarioId(scenario_id))

    def scenarios_of(self, baseline_id: str) -> list[Scenario]:
        found = [s for s in self._scenarios.values() if s.baseline_id == baseline_id]
        return sorted(found, key=lambda s: s.created_at)

    def add_run(self, run: AnyRun) -> None:
        """Legt einen Analyselauf ab. Fruehere Laeufe bleiben erhalten."""
        self._runs.setdefault(run.scenario_id, []).append(run)

    def runs(self, scenario_id: str) -> list[AnyRun]:
        return list(self._runs.get(ScenarioId(scenario_id), []))

    def latest_run(self, scenario_id: str) -> AnyRun | None:
        runs = self.runs(scenario_id)
        return runs[-1] if runs else None

    def add_closure(self, closure: Closure, scenario_id: str) -> None:
        self._closures[ScenarioId(scenario_id)] = closure

    def closure(self, scenario_id: str) -> Closure | None:
        return self._closures.get(ScenarioId(scenario_id))

    def add_decision(self, decision: Decision) -> None:
        """Haengt eine Entscheidung an. Fruehere bleiben erhalten."""
        self._decisions.setdefault(decision.scenario_id, []).append(decision)

    def decisions(self, scenario_id: str) -> list[Decision]:
        return list(self._decisions.get(ScenarioId(scenario_id), []))
