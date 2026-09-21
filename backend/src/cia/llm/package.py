"""Analysepaket und Prompt fuer eine Kandidatenklasse.

Umsetzung von Konzept Abschnitt 4.5. Fuer jede Kandidatenklasse wird ein Paket
zusammengestellt: die Aenderungen des Szenarios, die weiter geltenden Use Cases
der Klasse und die Methoden der Klasse mit ihrem Quelltext. Aus dem Paket
entsteht der Prompt.

Die Kandidaten selbst kommen aus ``analysis/``. Dieses Modul bewertet nichts,
es sammelt nur die Eingaben fuer das Modell.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..analysis.structural import ClassCandidate
from ..domain.artifacts import JavaMethod
from ..domain.baseline import Baseline
from ..domain.ids import BaselineId, ClassId, ScenarioId, UseCaseId
from ..domain.scenario import ChangeKind, RequirementChange, Scenario

#: Version der Prompt-Vorlage (Konzept 4.5). Bei jeder Aenderung am Text
#: unten hochzaehlen, damit sich Antworten einer Vorlage zuordnen lassen.
#: TODO: Aufbau und Umfang des Prompts am Prototyp erproben (Konzept 4.5).
PROMPT_VERSION = "v1-entwurf"


@dataclass(frozen=True, slots=True)
class ChangeInPackage:
    """Eine Aenderung des Szenarios, wie das Modell sie sieht."""

    use_case_id: UseCaseId
    kind: ChangeKind
    #: Bisheriger Text. Bei einem neuen Use Case gibt es keinen.
    old_text: str | None
    #: Geplanter Text. Beim Deaktivieren gibt es keinen.
    new_text: str | None
    #: Ob diese Aenderung ueber ihre Links zu dieser Klasse gefuehrt hat.
    is_trigger: bool


@dataclass(frozen=True, slots=True)
class ContextUseCase:
    """Ein weiter aktiver Use Case der Klasse (Erhaltungskontext, Konzept 4.3)."""

    use_case_id: UseCaseId
    title: str
    text: str


@dataclass(frozen=True, slots=True)
class ClassPackage:
    scenario_id: ScenarioId
    baseline_id: BaselineId
    class_id: ClassId
    #: Alle Aenderungen des Szenarios, nicht nur die ausloesenden. Konzept 4.11:
    #: Das Modell soll den gemeinsamen Zielzustand kennen.
    changes: tuple[ChangeInPackage, ...]
    context_use_cases: tuple[ContextUseCase, ...]
    methods: tuple[JavaMethod, ...]


@dataclass(frozen=True, slots=True)
class PackageProblem:
    """Grund, warum fuer eine Klasse kein Paket gebaut werden konnte.

    Die Klasse gilt dann als "nicht verarbeitet" (Konzept 4.12), nicht als
    unauffaellig.
    """

    class_id: ClassId
    reason: str


def method_id(method: JavaMethod) -> str:
    """Die Kennung, mit der das Modell eine Methode benennen muss."""
    return str(method.signature)


def build_class_package(
    baseline: Baseline, scenario: Scenario, candidate: ClassCandidate
) -> ClassPackage | PackageProblem:
    """Baut das Paket fuer eine Kandidatenklasse.

    Ergebnis ist entweder das Paket oder ein ``PackageProblem``.
    """
    class_id = candidate.class_id
    java_class = baseline.java_class(class_id)

    if java_class is None:
        return PackageProblem(class_id, "Klasse ist im Ausgangsstand nicht vorhanden")
    if not java_class.parsed:
        return PackageProblem(class_id, f"Klasse wurde nicht verarbeitet: {java_class.parse_error}")

    # Das Modell nennt Methoden ueber ihre Kennung. Kommt eine Kennung zweimal
    # vor (z. B. durch innere Klassen), waere die Zuordnung nicht eindeutig.
    ids = [method_id(m) for m in java_class.methods]
    doppelt = sorted({i for i in ids if ids.count(i) > 1})
    if doppelt:
        return PackageProblem(
            class_id, "Methodenkennungen nicht eindeutig: " + ", ".join(doppelt)
        )

    changes = tuple(
        _change_in_package(baseline, change, candidate)
        for change in scenario.requirement_changes
    )
    context = tuple(
        ContextUseCase(uid, baseline.use_cases[uid].title, baseline.use_cases[uid].text)
        for uid in sorted(candidate.preservation_context_ids)
    )
    return ClassPackage(
        scenario_id=scenario.id,
        baseline_id=baseline.id,
        class_id=class_id,
        changes=changes,
        context_use_cases=context,
        methods=java_class.methods,
    )


def _change_in_package(
    baseline: Baseline, change: RequirementChange, candidate: ClassCandidate
) -> ChangeInPackage:
    use_case = baseline.use_case(change.use_case_id)
    return ChangeInPackage(
        use_case_id=change.use_case_id,
        kind=change.kind,
        old_text=use_case.text if use_case is not None else None,
        new_text=None if change.kind is ChangeKind.DEACTIVATE else change.target_text,
        is_trigger=change.use_case_id in candidate.triggering_use_case_ids,
    )


# --- Prompt ---------------------------------------------------------------

_ANWEISUNG = """\
Du beurteilst, welche Methoden einer Java-Klasse durch einen Aenderungsauftrag
an Anforderungen beruehrt sind, und schlaegst Anpassungen vor.

Regeln:
- Beurteile jede Methode der Klasse einzeln.
- Eine Methode, die auch fuer weiterhin geltende Use Cases gebraucht wird, darf
  nicht allein wegen des Auftrags zur Entfernung vorgeschlagen werden.
- Reicht der gegebene Kontext nicht aus, antworte mit "not_assessable" und nenne
  den fehlenden Kontext. Rate nicht.
- "no_change_visible" heisst nur: Im gegebenen Kontext ist kein Aenderungsbedarf
  erkennbar. Das ist keine Garantie.
- Benenne Methoden genau mit der Kennung aus der Liste unten. Eine neue Methode
  kennzeichnest du mit target_kind "new_method".
- Antworte ausschliesslich mit JSON im folgenden Format."""

_ANTWORTFORMAT = """\
{
  "entries": [
    {
      "target_kind": "method" | "new_method" | "class",
      "target": "Kennung der Methode, Name der neuen Methode oder Bezeichnung der Klassenstelle",
      "status": "change_proposed" | "no_change_visible" | "not_assessable",
      "use_case_passage": "betroffene Stelle im Use-Case-Text",
      "reason": "kurze fachliche Begruendung",
      "proposal": "vorgeschlagener Soll-Zustand oder null"
    }
  ],
  "assumptions": ["Annahmen, die du getroffen hast"],
  "missing_context": ["Angaben, die dir fuer die Beurteilung fehlen"]
}"""


def render_prompt(package: ClassPackage) -> str:
    """Setzt den Prompt aus dem Paket zusammen (Vorlage: PROMPT_VERSION)."""
    teile = [_ANWEISUNG, f"KLASSE: {package.class_id}"]

    zeilen = ["AENDERUNGSAUFTRAG (alle Aenderungen zusammen sind der Zielzustand):"]
    for change in package.changes:
        zeilen.append(_beschreibe_aenderung(change))
    teile.append("\n".join(zeilen))

    if package.context_use_cases:
        zeilen = ["WEITERHIN GELTENDE USE CASES DIESER KLASSE (muessen erfuellt bleiben):"]
        for use_case in package.context_use_cases:
            zeilen.append(f"- {use_case.use_case_id} ({use_case.title}): {use_case.text}")
        teile.append("\n".join(zeilen))
    else:
        teile.append("WEITERHIN GELTENDE USE CASES DIESER KLASSE: keine bekannt.")

    zeilen = ["METHODEN DER KLASSE (Kennung, danach Quelltext):"]
    for method in package.methods:
        zeilen.append(f"### {method_id(method)}\n{method.source}")
    teile.append("\n\n".join(zeilen))

    teile.append("ANTWORTFORMAT:\n" + _ANTWORTFORMAT)
    return "\n\n".join(teile)


def _beschreibe_aenderung(change: ChangeInPackage) -> str:
    hinweis = " [fuehrt zu dieser Klasse]" if change.is_trigger else ""
    if change.kind is ChangeKind.DEACTIVATE:
        return f"- {change.use_case_id}: wird deaktiviert{hinweis}. Bisheriger Text: {change.old_text}"
    if change.kind is ChangeKind.MODIFY:
        return (
            f"- {change.use_case_id}: wird geaendert{hinweis}.\n"
            f"  Bisheriger Text: {change.old_text}\n  Neuer Text: {change.new_text}"
        )
    return f"- {change.use_case_id}: wird neu angelegt{hinweis}. Text: {change.new_text}"
