"""Ein- und Ausgabeformen der Schnittstelle.

Die Schemas bilden die Domaenentypen ab, ohne sie zu veraendern. Bewusst fehlt
in allen Ausgaben ein Feld, das eine Klasse oder Methode als "loeschbar" oder
"unbeeintraechtigt" bewertet (Konzept 4.6, 4.13). Die Schnittstelle liefert
Befunde ueber die Struktur, keine Freigaben.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from ..domain.decision import DecisionKind
from ..domain.scenario import ChangeKind, Direction, ScenarioState

# --- Import und Baseline (F1) ---------------------------------------------


class ImportRequest(BaseModel):
    #: Verzeichnis eines Projektstands mit ``usecases/``, ``src/`` und
    #: ``tracelinks.txt``. Die Schnittstelle ist fuer den lokalen Betrieb gedacht.
    path: str
    label: str | None = None


class UploadedFile(BaseModel):
    #: Name oder relativer Pfad, wie der Browser die Datei kennt.
    path: str
    content: str


class UploadRequest(BaseModel):
    """Ein Projektstand, wie ihn die Oberflaeche hochlaedt (Konzept 4.2)."""

    label: str | None = None
    #: Ein Use Case je Datei (.md oder .txt).
    use_cases: list[UploadedFile] = Field(default_factory=list)
    #: Java-Dateien mit relativem Pfad.
    sources: list[UploadedFile] = Field(default_factory=list)
    trace_links: UploadedFile | None = None


class DiagnosticOut(BaseModel):
    code: str
    severity: Literal["error", "warning", "info"]
    message: str
    source_file: str | None
    line_number: int | None


class BaselineSummaryOut(BaseModel):
    """Zaehlwerte der Abdeckungsanzeige (Konzept 4.13)."""

    baseline_id: str
    label: str
    counts: dict[str, int]
    diagnostics: dict[str, int]
    has_errors: bool


class BaselineDetailOut(BaselineSummaryOut):
    diagnostic_entries: list[DiagnosticOut]


# --- Graph und Teilgraph (F2) ----------------------------------------------


class GraphNodeOut(BaseModel):
    #: Eindeutig ueber beide Artefaktarten hinweg, z. B. ``uc:UC1``.
    id: str
    kind: Literal["use_case", "class"]
    #: Die Kennung im Domaenenmodell, z. B. ``UC1`` oder ``Katalog.java``.
    ref: str
    label: str
    #: Ob der Knoten mindestens eine deklarierte Zuordnung hat. ``False`` heisst
    #: nicht, dass eine Aenderung ihn unberuehrt laesst (Konzept 4.1).
    linked: bool
    #: Nur im Teilgraphen gesetzt: ausgewaehlt oder nur Nachbar.
    selected: bool | None = None
    active: bool | None = None
    parsed: bool | None = None
    method_count: int | None = None


class GraphEdgeOut(BaseModel):
    id: str
    source: str
    target: str
    origin: Literal["imported", "scenario"]


class GraphOut(BaseModel):
    baseline_id: str
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]


# --- Artefaktdetails ------------------------------------------------------


class UseCaseOut(BaseModel):
    id: str
    title: str
    text: str
    source_file: str | None
    active: bool
    class_ids: list[str]
    linked: bool


class SignatureModel(BaseModel):
    name: str
    parameter_types: list[str] = Field(default_factory=list)


class SourceRangeOut(BaseModel):
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int


class MethodRefOut(BaseModel):
    """Baseline, Klasse, Signatur und Quelltextbereich gemeinsam (Konzept 4.2)."""

    baseline_id: str
    class_id: str
    signature: SignatureModel
    source_range: SourceRangeOut


class MethodOut(BaseModel):
    ref: MethodRefOut
    is_constructor: bool
    #: Der Quelltext der Methode, fuer den Ist-Soll-Vergleich (Konzept 4.6).
    source: str


class ClassOut(BaseModel):
    id: str
    file_name: str
    relative_path: str
    source: str
    parsed: bool
    parse_error: str | None
    methods: list[MethodOut]
    use_case_ids: list[str]
    linked: bool


# --- Szenarien (F3, strukturelle Auswahl aus F4 und F6) ---------------------


class RequirementChangeModel(BaseModel):
    kind: ChangeKind
    use_case_id: str
    target_text: str | None = None
    manual_class_ids: list[str] = Field(default_factory=list)


class CodeChangeIn(BaseModel):
    """Eingabe einer Codeaenderung. Die Ausgangsfassung gibt der Anwender nicht
    ein; sie stammt aus dem importierten Stand (Konzept 4.7)."""

    class_id: str
    after: str
    signature: SignatureModel | None = None


class CodeChangeOut(BaseModel):
    class_id: str
    before: str
    after: str
    signature: SignatureModel | None


class ScenarioCreate(BaseModel):
    title: str
    direction: Direction
    requirement_changes: list[RequirementChangeModel] = Field(default_factory=list)
    code_changes: list[CodeChangeIn] = Field(default_factory=list)


class ScenarioOut(BaseModel):
    scenario_id: str
    baseline_id: str
    title: str
    direction: Direction
    state: ScenarioState
    created_at: datetime
    requirement_changes: list[RequirementChangeModel]
    code_changes: list[CodeChangeOut]


class ClassCandidateOut(BaseModel):
    class_id: str
    triggering_use_case_ids: list[str]
    #: Weitere aktive Use Cases der Klasse. Sie gelten nie als betroffen
    #: (Konzept 4.3). Eine leere Liste ist keine Loeschfreigabe (Konzept 4.6).
    preservation_context_ids: list[str]
    parsed: bool


class UnresolvedChangeOut(BaseModel):
    use_case_id: str
    reason: str


class ForwardSelectionOut(BaseModel):
    direction: Literal["requirement_to_code"] = "requirement_to_code"
    scenario_id: str
    changed_use_case_ids: list[str]
    candidates: list[ClassCandidateOut]
    #: Aenderungen ohne bestimmbare Zuordnung. Eine leere Kandidatenmenge fuer
    #: sie ist nicht "wirkungslos" (Konzept 4.3).
    unresolved: list[UnresolvedChangeOut]
    unparsed_candidate_ids: list[str]


class UseCaseCandidateOut(BaseModel):
    use_case_id: str
    triggering_class_ids: list[str]


class BackwardSelectionOut(BaseModel):
    direction: Literal["code_to_requirement"] = "code_to_requirement"
    scenario_id: str
    changed_class_ids: list[str]
    candidates: list[UseCaseCandidateOut]
    #: Geaenderte Klassen ohne deklarierte Zuordnung: nicht zuordenbar, nicht
    #: unbeeintraechtigt (Konzept 4.7).
    unassignable_class_ids: list[str]


# --- Entscheidungen (F5) ---------------------------------------------------------


class DecisionIn(BaseModel):
    #: Der Vorschlag: Lauf, Gegenstand und Nummer des Eintrags (ab 0).
    #: Gegenstand ist die Klasse (Anforderungsrichtung) oder der Use Case
    #: (Gegenrichtung, Nummer dann immer 0).
    run_id: str
    subject_id: str
    entry_index: int = 0
    #: In der Anforderungsrichtung: "accepted" uebernimmt den Vorschlag. In der
    #: Gegenrichtung: "accepted" heisst, die Codeaenderung ist gewollt und der
    #: Textvorschlag wird uebernommen; "rejected" heisst, die Anforderung gilt
    #: weiter und der Code ist zu pruefen (Konzept 4.7).
    kind: DecisionKind
    #: Vom Anwender ueberarbeiteter Soll-Zustand oder Text. Nur mit "accepted".
    revised_proposal: str | None = None


# --- Anzeige-Ereignisse (F7) -------------------------------------------------------


class UiEventType(str, Enum):
    """Was die Oberflaeche dem Anwender gezeigt hat (Konzept 4.13)."""

    MARKING_SHOWN = "marking_shown"
    COMPARISON_SHOWN = "comparison_shown"
    #: Erhaltungskontext, z. B. weiter aktive Use Cases einer Klasse.
    CONTEXT_SHOWN = "context_shown"


class UiEventIn(BaseModel):
    type: UiEventType
    #: Worauf sich die Anzeige bezog, z. B. eine Klasse oder ein Use Case.
    subject_id: str | None = None
    detail: str | None = None


# --- Abschluss ------------------------------------------------------------------


class CloseIn(BaseModel):
    #: Muss gesetzt sein, wenn noch offene Faelle bestehen (Konzept 4.8).
    acknowledge_open_items: bool = False
    #: Begruendung fuer den Abschluss trotz offener Faelle.
    note: str | None = None


SelectionOut = Annotated[
    Union[ForwardSelectionOut, BackwardSelectionOut], Field(discriminator="direction")
]
