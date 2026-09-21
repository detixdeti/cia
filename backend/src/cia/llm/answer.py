"""Antwort des Modells lesen und pruefen.

Umsetzung von Konzept Abschnitt 4.10. Die Pruefung ist rein technisch: Sie
klaert, ob die Antwort lesbar ist und ob ihre Verweise zum Ausgangsstand passen.
Ob eine Aussage fachlich stimmt, prueft der Anwender. Eine Antwort, die diese
Pruefung besteht, gilt deshalb weiter als "fachlich ungeprueft".

Grundsaetze:
- Nichts wird still repariert. Eine unbekannte Methodenkennung wird nicht der
  aehnlichsten bekannten Methode zugeordnet, sondern bleibt als Problem sichtbar.
- Eine Methode, zu der das Modell nichts sagt, gilt nicht als unveraendert. Sie
  steht in ``unanswered_methods`` und bleibt offen.
- Ein Fehler wird nie zu einer Entwarnung (Konzept 4.5).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from ..domain.artifacts import MethodRef
from .package import ClassPackage, method_id


class Status(str, Enum):
    """Einschaetzung des Modells zu einer Stelle (Konzept 4.5)."""

    CHANGE_PROPOSED = "change_proposed"
    #: Nur "im gegebenen Kontext nicht erkennbar", keine Garantie.
    NO_CHANGE_VISIBLE = "no_change_visible"
    NOT_ASSESSABLE = "not_assessable"


class TargetKind(str, Enum):
    METHOD = "method"
    NEW_METHOD = "new_method"
    CLASS = "class"


class EntryProblem(str, Enum):
    """Was an einem einzelnen Eintrag nicht stimmt."""

    #: Die Kennung gehoert zu keiner Methode der Klasse.
    UNKNOWN_METHOD = "unknown_method"
    #: Als neue Methode gemeldet, den Namen gibt es aber schon.
    ALREADY_EXISTS = "already_exists"
    #: Dieselbe Stelle kommt mehrfach vor, evtl. mit Widerspruch.
    DUPLICATE = "duplicate"
    #: Ein Aenderungsvorschlag ohne Use-Case-Stelle, Begruendung oder Soll-Zustand.
    INCOMPLETE = "incomplete"


class AnswerState(str, Enum):
    ANSWERED = "answered"
    #: Das Modell hat geantwortet, die Antwort ist aber nicht lesbar.
    INVALID_FORMAT = "invalid_format"
    #: Es gibt keine Antwort, z. B. wegen eines Fehlers beim Aufruf.
    NO_ANSWER = "no_answer"


@dataclass(frozen=True, slots=True)
class Entry:
    """Ein Eintrag der Modellantwort, so wie das Modell ihn geschrieben hat."""

    target_kind: TargetKind
    target: str
    status: Status
    #: Betroffene Stelle im Use-Case-Text.
    use_case_passage: str
    #: Begruendung (Betroffenheit). Getrennt vom Soll-Vorschlag (Konzept 4.10).
    reason: str
    #: Vorgeschlagener Soll-Zustand, falls vorhanden.
    proposal: str | None


@dataclass(frozen=True, slots=True)
class CheckedEntry:
    entry: Entry
    #: Nur gesetzt, wenn der Eintrag eine bestehende Methode meint und deren
    #: Kennung bekannt ist.
    method_ref: MethodRef | None
    problems: tuple[EntryProblem, ...]


@dataclass(frozen=True, slots=True)
class CheckedAnswer:
    state: AnswerState
    #: Probleme der Antwort als Ganzes (Format, Aufruf). Bei ANSWERED leer.
    problems: tuple[str, ...]
    entries: tuple[CheckedEntry, ...]
    #: Methoden, zu denen die Antwort nichts sagt. Sie bleiben offen.
    unanswered_methods: tuple[MethodRef, ...]
    assumptions: tuple[str, ...]
    missing_context: tuple[str, ...]


def open_answer(package: ClassPackage, state: AnswerState, problem: str) -> CheckedAnswer:
    """Eine Antwort ohne Inhalt. Alle Methoden der Klasse bleiben offen."""
    return CheckedAnswer(
        state=state,
        problems=(problem,),
        entries=(),
        unanswered_methods=tuple(m.ref for m in package.methods),
        assumptions=(),
        missing_context=(),
    )


def check_answer(package: ClassPackage, text: str) -> CheckedAnswer:
    """Liest den Antworttext des Modells und prueft ihn gegen das Paket."""
    data, problem = load_json(text)
    if data is None:
        return open_answer(package, AnswerState.INVALID_FORMAT, problem)

    entries, format_problems = _read_entries(data)
    assumptions = read_text_list(data, "assumptions", format_problems)
    missing_context = read_text_list(data, "missing_context", format_problems)

    # Ein Formatfehler irgendwo verwirft die ganze Antwort. Das ist streng, aber
    # einfach: Der Anwender kann die Anfrage neu stellen (Konzept 4.10).
    if format_problems:
        return CheckedAnswer(
            state=AnswerState.INVALID_FORMAT,
            problems=tuple(format_problems),
            entries=(),
            unanswered_methods=tuple(m.ref for m in package.methods),
            assumptions=(),
            missing_context=(),
        )

    checked = _check_entries(package, entries)

    genannt = {e.target for e in entries if e.target_kind is TargetKind.METHOD}
    unanswered = tuple(m.ref for m in package.methods if method_id(m) not in genannt)

    return CheckedAnswer(
        state=AnswerState.ANSWERED,
        problems=(),
        entries=checked,
        unanswered_methods=unanswered,
        assumptions=assumptions,
        missing_context=missing_context,
    )


# --- Lesen ----------------------------------------------------------------


def load_json(text: str) -> tuple[dict | None, str]:
    """Holt das JSON aus dem Antworttext.

    Modelle setzen ihr JSON oft in einen Codeblock oder schreiben einen Satz
    davor. Deshalb wird alles zwischen der ersten "{" und der letzten "}"
    gelesen. Am Inhalt wird dabei nichts veraendert.
    """
    start = text.find("{")
    ende = text.rfind("}")
    if start == -1 or ende < start:
        return None, "Die Antwort enthaelt kein JSON"
    try:
        return json.loads(text[start : ende + 1]), ""
    except json.JSONDecodeError as fehler:
        return None, f"Das JSON ist nicht lesbar: {fehler}"


def _read_entries(data: dict) -> tuple[list[Entry], list[str]]:
    problems: list[str] = []
    raw_entries = data.get("entries")
    if not isinstance(raw_entries, list):
        return [], ['Das Feld "entries" fehlt oder ist keine Liste']

    entries: list[Entry] = []
    for nummer, raw in enumerate(raw_entries, start=1):
        entry = _read_entry(raw, nummer, problems)
        if entry is not None:
            entries.append(entry)
    return entries, problems


def _read_entry(raw: object, nummer: int, problems: list[str]) -> Entry | None:
    if not isinstance(raw, dict):
        problems.append(f"Eintrag {nummer} ist kein Objekt")
        return None
    try:
        kind = TargetKind(raw.get("target_kind"))
        status = Status(raw.get("status"))
    except ValueError:
        problems.append(f"Eintrag {nummer}: target_kind oder status ist ungueltig")
        return None

    target = raw.get("target")
    if not isinstance(target, str) or not target.strip():
        problems.append(f'Eintrag {nummer}: "target" fehlt')
        return None

    proposal = raw.get("proposal")
    return Entry(
        target_kind=kind,
        target=target.strip(),
        status=status,
        use_case_passage=as_text(raw.get("use_case_passage")),
        reason=as_text(raw.get("reason")),
        proposal=proposal.strip() if isinstance(proposal, str) and proposal.strip() else None,
    )


def as_text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def read_text_list(data: dict, key: str, problems: list[str]) -> tuple[str, ...]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        problems.append(f'Das Feld "{key}" muss eine Liste von Texten sein')
        return ()
    return tuple(x.strip() for x in value if x.strip())


# --- Pruefen --------------------------------------------------------------


def _check_entries(package: ClassPackage, entries: list[Entry]) -> tuple[CheckedEntry, ...]:
    methods_by_id = {method_id(m): m for m in package.methods}
    schon_gesehen: set[tuple[TargetKind, str]] = set()
    checked: list[CheckedEntry] = []

    for entry in entries:
        problems: list[EntryProblem] = []
        ref: MethodRef | None = None

        if entry.target_kind is TargetKind.METHOD:
            method = methods_by_id.get(entry.target)
            if method is None:
                problems.append(EntryProblem.UNKNOWN_METHOD)
            else:
                ref = method.ref
        elif entry.target_kind is TargetKind.NEW_METHOD and entry.target in methods_by_id:
            problems.append(EntryProblem.ALREADY_EXISTS)

        stelle = (entry.target_kind, entry.target)
        if stelle in schon_gesehen:
            problems.append(EntryProblem.DUPLICATE)
        schon_gesehen.add(stelle)

        if entry.status is Status.CHANGE_PROPOSED and not (
            entry.use_case_passage and entry.reason and entry.proposal
        ):
            problems.append(EntryProblem.INCOMPLETE)

        checked.append(CheckedEntry(entry, ref, tuple(problems)))

    return tuple(checked)
