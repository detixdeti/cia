"""Ein Analyselauf ueber alle Kandidatenklassen eines Szenarios.

Ablauf (Konzept 4.5): Die Kandidaten kommen aus ``analysis/``. Fuer jede
Kandidatenklasse wird ein Paket gebaut und das Modell gefragt. Wo kein Paket
gebaut werden kann, bleibt die Klasse als "nicht verarbeitet" stehen.

Der Lauf sammelt alles, was offen bleibt, statt daran abzubrechen (Konzept 4.12):
Klassen ohne Paket, Klassen ohne Antwort und Aenderungen ohne Zuordnung.
Bisher gibt es nur die Anforderungsrichtung.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from ..analysis.structural import UnresolvedChange, select_forward
from ..domain.baseline import Baseline
from ..domain.ids import BaselineId, ClassId, ScenarioId
from ..domain.scenario import Scenario
from .analyze import ClassAnalysis, analyze_class
from .backward import CodeChangeRun
from .package import PROMPT_VERSION, PackageProblem, build_class_package
from .provider import LlmProvider


@dataclass(frozen=True, slots=True)
class ClassResult:
    """Ergebnis fuer eine Kandidatenklasse.

    Entweder ist ``analysis`` gesetzt (das Modell wurde gefragt) oder
    ``not_processed_reason`` (es konnte kein Paket gebaut werden). Nie beides.
    """

    class_id: ClassId
    not_processed_reason: str | None
    analysis: ClassAnalysis | None


@dataclass(frozen=True, slots=True)
class AnalysisRun:
    #: Jede Anfrage bekommt eine eigene Kennung, damit eine neue Antwort nicht
    #: mit einer frueheren verwechselt wird (Konzept 4.10).
    run_id: str
    scenario_id: ScenarioId
    baseline_id: BaselineId
    started_at: datetime
    finished_at: datetime
    provider_name: str
    provider_settings: dict[str, str | int | float]
    prompt_version: str
    results: tuple[ClassResult, ...]
    #: Aenderungen ohne Zuordnung. Sie haben keine Kandidaten, sind aber nicht
    #: wirkungslos (Konzept 4.3).
    unresolved: tuple[UnresolvedChange, ...]


#: Ein Analyselauf, je nach Richtung des Szenarios.
AnyRun = AnalysisRun | CodeChangeRun


def run_forward_analysis(
    baseline: Baseline, scenario: Scenario, provider: LlmProvider
) -> AnalysisRun:
    started_at = datetime.now(timezone.utc)
    selection = select_forward(baseline, scenario)

    results: list[ClassResult] = []
    for candidate in selection.candidates:
        package = build_class_package(baseline, scenario, candidate)
        if isinstance(package, PackageProblem):
            results.append(ClassResult(candidate.class_id, package.reason, None))
        else:
            results.append(ClassResult(candidate.class_id, None, analyze_class(provider, package)))

    return AnalysisRun(
        run_id=uuid.uuid4().hex[:12],
        scenario_id=scenario.id,
        baseline_id=baseline.id,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        provider_name=provider.name,
        provider_settings=dict(provider.settings),
        prompt_version=PROMPT_VERSION,
        results=tuple(results),
        unresolved=selection.unresolved,
    )
