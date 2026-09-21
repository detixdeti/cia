"""Eine Klasse vom Modell beurteilen lassen.

Verbindet die drei Schritte: Prompt bauen, Modell fragen, Antwort pruefen.
Ein Fehler beim Aufruf wird nicht als Ausnahme weitergegeben, sondern als
"keine Antwort" festgehalten. Die Klasse bleibt dann offen (Konzept 4.5).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from ..domain.ids import ClassId
from .answer import AnswerState, CheckedAnswer, check_answer, open_answer
from .package import PROMPT_VERSION, ClassPackage, render_prompt
from .provider import LlmError, LlmProvider


@dataclass(frozen=True, slots=True)
class ClassAnalysis:
    """Ergebnis einer Modellanfrage samt allem, was fuer das Protokoll noetig ist.

    Prompt und rohe Antwort bleiben erhalten (Konzept 4.13), auch wenn die
    Antwort nicht lesbar war.
    """

    class_id: ClassId
    provider_name: str
    prompt_version: str
    prompt: str
    #: Der Antworttext, wie er ankam. ``None``, wenn der Aufruf gescheitert ist.
    raw_response: str | None
    answer: CheckedAnswer
    #: Wann die Anfrage abgeschickt wurde und wann der Aufruf zurueckkam
    #: (Antwort oder Fehler). So lassen sich Wartezeiten von der uebrigen
    #: Bearbeitungszeit trennen (Konzept 4.13).
    requested_at: datetime
    finished_at: datetime


def analyze_class(provider: LlmProvider, package: ClassPackage) -> ClassAnalysis:
    prompt = render_prompt(package)
    requested_at = datetime.now(timezone.utc)
    try:
        raw = provider.complete(prompt)
    except LlmError as fehler:
        answer = open_answer(package, AnswerState.NO_ANSWER, f"Modellanfrage gescheitert: {fehler}")
        raw = None
    else:
        answer = check_answer(package, raw)
    finished_at = datetime.now(timezone.utc)

    return ClassAnalysis(
        class_id=package.class_id,
        provider_name=provider.name,
        prompt_version=PROMPT_VERSION,
        prompt=prompt,
        raw_response=raw,
        answer=answer,
        requested_at=requested_at,
        finished_at=finished_at,
    )
