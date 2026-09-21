"""Artefakte des importierten Projektstands.

Umsetzung von Konzept Abschnitt 4.2. Alle Typen sind unveraenderlich. Ein
importierter Stand darf sich nach dem Import nicht mehr aendern, weil sonst
Analyseergebnisse nachtraeglich ihre Grundlage verlieren wuerden.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .ids import BaselineId, ClassId, UseCaseId


@dataclass(frozen=True, slots=True)
class SourceRange:
    """Ein Quelltextbereich innerhalb einer Datei.

    Zeilen sind einsbasiert, ``end_line`` ist einschliesslich. Der Bereich gilt
    ausschliesslich fuer die Fassung, aus der er gewonnen wurde. Konzept 4.2
    haelt fest, dass ein Zeilenbereich ohne Versionsbezug nach einer Einfuegung
    auf eine andere Methode zeigen kann. Deshalb wird ein Bereich nie allein
    weitergereicht, sondern stets als Teil einer :class:`MethodRef`.
    """

    start_line: int
    end_line: int
    start_byte: int
    end_byte: int

    def __post_init__(self) -> None:
        if self.start_line < 1:
            raise ValueError(f"start_line muss >= 1 sein, war {self.start_line}")
        if self.end_line < self.start_line:
            raise ValueError(
                f"end_line ({self.end_line}) liegt vor start_line ({self.start_line})"
            )
        if self.end_byte < self.start_byte:
            raise ValueError(
                f"end_byte ({self.end_byte}) liegt vor start_byte ({self.start_byte})"
            )

    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1


@dataclass(frozen=True, slots=True)
class MethodSignature:
    """Technische Identitaet einer Methode innerhalb ihrer Klasse.

    Konzept 4.2 verlangt, ueberladene Methoden anhand von Name und
    Parametertypen zu unterscheiden. Der Rueckgabetyp gehoert nicht zur
    Identitaet, weil Java keine Ueberladung allein ueber ihn zulaesst.
    """

    name: str
    parameter_types: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.name}({', '.join(self.parameter_types)})"


@dataclass(frozen=True, slots=True)
class MethodRef:
    """Vollstaendige Referenz auf eine Methode.

    Traegt die drei in Konzept 4.2 geforderten Merkmale zusammen: die
    technische Identitaet (Klasse und Signatur), den Versionsbezug ueber die
    Baseline und die Position im Quelltext. Nur so laesst sich eine
    Modellaussage spaeter eindeutig einer Stelle zuordnen.
    """

    baseline_id: BaselineId
    class_id: ClassId
    signature: MethodSignature
    source_range: SourceRange

    def __str__(self) -> str:
        return f"{self.class_id}#{self.signature}"


@dataclass(frozen=True, slots=True)
class JavaMethod:
    """Eine geparste Methode mit ihrem Quelltext."""

    ref: MethodRef
    source: str
    is_constructor: bool = False

    @property
    def signature(self) -> MethodSignature:
        return self.ref.signature


@dataclass(frozen=True, slots=True)
class JavaClass:
    """Eine importierte Java-Datei.

    Der Parser kann scheitern. Konzept 4.13 verlangt, dass eine nicht
    verarbeitete Klasse sichtbar bleibt und nicht stillschweigend als
    unauffaellig gilt. Deshalb unterscheidet ``parsed`` den erfolgreichen vom
    gescheiterten Fall, statt eine leere Methodenliste zu liefern.
    """

    id: ClassId
    baseline_id: BaselineId
    file_name: str
    relative_path: str
    source: str
    methods: tuple[JavaMethod, ...] = ()
    parsed: bool = True
    parse_error: str | None = None

    def method(self, signature: MethodSignature) -> JavaMethod | None:
        for m in self.methods:
            if m.signature == signature:
                return m
        return None

    def methods_named(self, name: str) -> tuple[JavaMethod, ...]:
        return tuple(m for m in self.methods if m.signature.name == name)


@dataclass(frozen=True, slots=True)
class UseCase:
    """Eine Anforderung in Form eines Use Cases.

    ``id`` bleibt ueber Bearbeitungsstaende hinweg stabil, Bezeichnung und Text
    duerfen sich aendern (Konzept 4.2). ``active`` bildet den Zustand innerhalb
    eines Szenarios ab; in einer Baseline sind alle Use Cases aktiv.
    """

    id: UseCaseId
    baseline_id: BaselineId
    title: str
    text: str
    source_file: str | None = None
    active: bool = True
    tags: tuple[str, ...] = field(default_factory=tuple)

    def deactivated(self) -> UseCase:
        """Liefert eine inaktive Fassung. Der Ausgangsstand bleibt unberuehrt."""
        return UseCase(
            id=self.id,
            baseline_id=self.baseline_id,
            title=self.title,
            text=self.text,
            source_file=self.source_file,
            active=False,
            tags=self.tags,
        )

    def with_text(self, text: str) -> UseCase:
        return UseCase(
            id=self.id,
            baseline_id=self.baseline_id,
            title=self.title,
            text=text,
            source_file=self.source_file,
            active=self.active,
            tags=self.tags,
        )
