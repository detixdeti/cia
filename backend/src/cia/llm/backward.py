"""Gegenrichtung: Codeaenderung gegen die verknuepften Use Cases pruefen (F6).

Umsetzung von Konzept Abschnitt 4.7. Die Kandidaten-Use-Cases kommen aus
``analysis/`` (Relation T, rueckwaerts). Fuer jeden wird das Modell gefragt, ob
die Codeaenderung ihn moeglicherweise nicht mehr erfuellt.

Der Aufbau folgt der Anforderungsrichtung: Paket, Prompt, Antwortpruefung,
Modellaufruf, Lauf. Ein Unterschied: Hier gibt es pro Use Case genau eine
Einschaetzung, nicht eine Liste von Eintraegen pro Methode.

Wichtig (Konzept 4.7): Eine Abweichung kann heissen, dass der Code falsch ist.
Das Werkzeug behandelt einen geaenderten Anforderungstext deshalb nie als
bevorzugte Loesung. Der Textvorschlag ist optional, und ueber die Frage, ob die
Codeaenderung gewollt ist, entscheidet der Anwender.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from ..analysis.structural import UseCaseCandidate, select_backward
from ..domain.artifacts import MethodSignature
from ..domain.baseline import Baseline
from ..domain.ids import BaselineId, ClassId, ScenarioId, UseCaseId
from ..domain.scenario import Scenario
from .answer import AnswerState, as_text, load_json, read_text_list
from .provider import LlmError, LlmProvider

#: Version der Prompt-Vorlage dieser Richtung (Konzept 4.5). Bei jeder Aenderung
#: am Text unten hochzaehlen.
#: TODO: Aufbau und Umfang des Prompts am Prototyp erproben.
BACKWARD_PROMPT_VERSION = "v1-entwurf"


class DeviationStatus(str, Enum):
    """Einschaetzung des Modells zu einem Use Case (Konzept 4.7)."""

    POSSIBLE_DEVIATION = "possible_deviation"
    #: Nur "im gegebenen Kontext nicht erkennbar", keine Garantie.
    NO_DEVIATION_VISIBLE = "no_deviation_visible"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class AssessmentProblem(str, Enum):
    #: Eine moegliche Abweichung ohne betroffene Stelle oder Begruendung.
    INCOMPLETE = "incomplete"


# --- Paket ------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CodeChangeInPackage:
    class_id: ClassId
    #: Gesetzt, wenn nur eine Methode geaendert wurde.
    signature: MethodSignature | None
    before: str
    after: str


@dataclass(frozen=True, slots=True)
class UseCasePackage:
    scenario_id: ScenarioId
    baseline_id: BaselineId
    use_case_id: UseCaseId
    title: str
    text: str
    #: Die relevanten Aenderungen: alle an Klassen, die diesem Use Case
    #: zugeordnet sind. Konzept 4.4: Der Use Case wird einmal angezeigt, aber
    #: gegen die Gesamtheit dieser Aenderungen geprueft.
    changes: tuple[CodeChangeInPackage, ...]


def build_use_case_package(
    baseline: Baseline, scenario: Scenario, candidate: UseCaseCandidate
) -> UseCasePackage:
    use_case = baseline.use_cases[candidate.use_case_id]
    changes = tuple(
        CodeChangeInPackage(c.class_id, c.signature, c.before, c.after)
        for c in scenario.code_changes
        if c.class_id in candidate.triggering_class_ids
    )
    return UseCasePackage(
        scenario_id=scenario.id,
        baseline_id=baseline.id,
        use_case_id=candidate.use_case_id,
        title=use_case.title,
        text=use_case.text,
        changes=changes,
    )


# --- Prompt -----------------------------------------------------------------

_ANWEISUNG = """\
Du pruefst, ob eine Codeaenderung einen Use Case moeglicherweise nicht mehr
erfuellt.

Regeln:
- Beurteile das beschriebene Verhalten, nicht den Umfang des Textunterschieds.
  Eine Umbenennung ist keine Abweichung. Eine kleine Aenderung an einer
  Bedingung kann eine sein.
- Die Codeaenderung kann ein Fehler sein. Ob sie fachlich gewollt ist,
  entscheidet der Anwender, nicht du. Schlage einen neuen Use-Case-Text nur vor,
  wenn die Aenderung gewollt sein koennte. Sonst setze "proposed_text" auf null.
- Reicht der gegebene Kontext nicht aus, antworte mit "insufficient_information"
  und nenne den fehlenden Kontext. Rate nicht.
- "no_deviation_visible" heisst nur: Im gegebenen Kontext ist keine Abweichung
  erkennbar. Das ist keine Garantie, dass der Use Case erfuellt bleibt.
- Antworte ausschliesslich mit JSON im folgenden Format."""

_ANTWORTFORMAT = """\
{
  "status": "possible_deviation" | "no_deviation_visible" | "insufficient_information",
  "affected_passage": "betroffener Ablaufschritt oder betroffene Erfolgsbedingung",
  "reason": "kurze Begruendung: welches Verhalten aendert sich",
  "proposed_text": "vorgeschlagener neuer Use-Case-Text oder null",
  "assumptions": ["Annahmen, die du getroffen hast"],
  "missing_context": ["Angaben, die dir fuer die Beurteilung fehlen"]
}"""


def render_use_case_prompt(package: UseCasePackage) -> str:
    teile = [
        _ANWEISUNG,
        f"USE CASE: {package.use_case_id} ({package.title})\n{package.text}",
    ]

    zeilen = ["CODEAENDERUNGEN (Klasse oder Methode, bisherige und neue Fassung):"]
    for change in package.changes:
        ziel = change.class_id if change.signature is None else f"{change.class_id}#{change.signature}"
        zeilen.append(f"### {ziel}\nBISHER:\n{change.before}\n\nNEU:\n{change.after}")
    teile.append("\n\n".join(zeilen))

    teile.append("ANTWORTFORMAT:\n" + _ANTWORTFORMAT)
    return "\n\n".join(teile)


# --- Antwort ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Assessment:
    """Die Einschaetzung des Modells, so wie es sie geschrieben hat."""

    status: DeviationStatus
    #: Betroffene Stelle im Use Case.
    affected_passage: str
    #: Begruendung. Getrennt vom Textvorschlag (Konzept 4.10).
    reason: str
    proposed_text: str | None


@dataclass(frozen=True, slots=True)
class CheckedAssessment:
    state: AnswerState
    #: Probleme der Antwort als Ganzes (Format, Aufruf). Bei ANSWERED leer.
    problems: tuple[str, ...]
    #: Nur gesetzt, wenn die Antwort lesbar war.
    assessment: Assessment | None
    assessment_problems: tuple[AssessmentProblem, ...]
    assumptions: tuple[str, ...]
    missing_context: tuple[str, ...]


def open_assessment(state: AnswerState, *problems: str) -> CheckedAssessment:
    """Eine Antwort ohne Inhalt. Der Use Case bleibt offen."""
    return CheckedAssessment(
        state=state,
        problems=problems,
        assessment=None,
        assessment_problems=(),
        assumptions=(),
        missing_context=(),
    )


def check_assessment(text: str) -> CheckedAssessment:
    """Liest den Antworttext und prueft ihn. Nichts wird still repariert."""
    data, problem = load_json(text)
    if data is None:
        return open_assessment(AnswerState.INVALID_FORMAT, problem)

    format_problems: list[str] = []
    try:
        status = DeviationStatus(data.get("status"))
    except ValueError:
        format_problems.append('Das Feld "status" fehlt oder ist ungueltig')
    assumptions = read_text_list(data, "assumptions", format_problems)
    missing_context = read_text_list(data, "missing_context", format_problems)

    # Ein Formatfehler verwirft die ganze Antwort. Der Anwender kann sie neu
    # anfordern (Konzept 4.10).
    if format_problems:
        return open_assessment(AnswerState.INVALID_FORMAT, *format_problems)

    proposed = as_text(data.get("proposed_text"))
    assessment = Assessment(
        status=status,
        affected_passage=as_text(data.get("affected_passage")),
        reason=as_text(data.get("reason")),
        proposed_text=proposed or None,
    )

    problems: list[AssessmentProblem] = []
    if status is DeviationStatus.POSSIBLE_DEVIATION and not (
        assessment.affected_passage and assessment.reason
    ):
        problems.append(AssessmentProblem.INCOMPLETE)

    return CheckedAssessment(
        state=AnswerState.ANSWERED,
        problems=(),
        assessment=assessment,
        assessment_problems=tuple(problems),
        assumptions=assumptions,
        missing_context=missing_context,
    )


# --- Modellaufruf und Lauf -----------------------------------------------------


@dataclass(frozen=True, slots=True)
class UseCaseAnalysis:
    """Ergebnis einer Modellanfrage zu einem Use Case, samt Protokolldaten."""

    use_case_id: UseCaseId
    provider_name: str
    prompt_version: str
    prompt: str
    #: Der Antworttext, wie er ankam. ``None``, wenn der Aufruf gescheitert ist.
    raw_response: str | None
    answer: CheckedAssessment
    requested_at: datetime
    finished_at: datetime


def analyze_use_case(provider: LlmProvider, package: UseCasePackage) -> UseCaseAnalysis:
    prompt = render_use_case_prompt(package)
    requested_at = datetime.now(timezone.utc)
    try:
        raw = provider.complete(prompt)
    except LlmError as fehler:
        answer = open_assessment(AnswerState.NO_ANSWER, f"Modellanfrage gescheitert: {fehler}")
        raw = None
    else:
        answer = check_assessment(raw)
    finished_at = datetime.now(timezone.utc)

    return UseCaseAnalysis(
        use_case_id=package.use_case_id,
        provider_name=provider.name,
        prompt_version=BACKWARD_PROMPT_VERSION,
        prompt=prompt,
        raw_response=raw,
        answer=answer,
        requested_at=requested_at,
        finished_at=finished_at,
    )


@dataclass(frozen=True, slots=True)
class CodeChangeRun:
    """Ein Analyselauf der Gegenrichtung ueber alle Kandidaten-Use-Cases."""

    run_id: str
    scenario_id: ScenarioId
    baseline_id: BaselineId
    started_at: datetime
    finished_at: datetime
    provider_name: str
    provider_settings: dict[str, str | int | float]
    prompt_version: str
    results: tuple[UseCaseAnalysis, ...]
    #: Geaenderte Klassen ohne deklarierte Zuordnung. Sie sind nicht zuordenbar,
    #: nicht unbeeintraechtigt (Konzept 4.7).
    unassignable_class_ids: tuple[ClassId, ...]


def run_backward_analysis(
    baseline: Baseline, scenario: Scenario, provider: LlmProvider
) -> CodeChangeRun:
    started_at = datetime.now(timezone.utc)
    selection = select_backward(baseline, scenario)

    results = tuple(
        analyze_use_case(provider, build_use_case_package(baseline, scenario, candidate))
        for candidate in selection.candidates
    )

    return CodeChangeRun(
        run_id=uuid.uuid4().hex[:12],
        scenario_id=scenario.id,
        baseline_id=baseline.id,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
        provider_name=provider.name,
        provider_settings=dict(provider.settings),
        prompt_version=BACKWARD_PROMPT_VERSION,
        results=results,
        unassignable_class_ids=tuple(sorted(selection.unassignable_class_ids)),
    )
