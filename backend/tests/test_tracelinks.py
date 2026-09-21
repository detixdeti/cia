"""Tests des Trace-Link-Parsers.

Geprueft wird das in Konzept Abschnitt 4.2 festgelegte Format sowie die
Behandlung der Faelle, die dort ausdruecklich genannt sind: doppelte
Zuordnungen, Mehrfachzuordnungen eines Use Cases und fehlerhafte Zeilen.
"""

from __future__ import annotations

from cia.domain.ids import ClassId, UseCaseId
from cia.importing.result import Diagnostics, DiagnosticCode, Severity
from cia.importing.tracelinks import parse_trace_links


def parse(content: str):
    diagnostics = Diagnostics()
    return parse_trace_links(content, diagnostics), diagnostics


def test_einfache_zuordnung():
    result, diagnostics = parse("UC1 -> Person.java")

    assert len(result.links) == 1
    assert result.links[0].use_case_id == UseCaseId("UC1")
    assert result.links[0].class_id == ClassId("Person.java")
    assert len(diagnostics) == 0


def test_mehrere_klassen_je_use_case():
    """Konzept 4.2: Das Format erlaubt mehrere Zuordnungen zu einem Use Case,
    indem dessen Kennung in mehreren Zeilen wiederholt wird."""
    result, diagnostics = parse("UC1 -> A.java\nUC1 -> B.java\nUC2 -> A.java")

    assert result.unique_link_count == 3
    assert result.read_lines == 3
    assert not diagnostics.has_errors


def test_leerzeilen_und_kommentare_werden_uebergangen():
    result, diagnostics = parse(
        "# Kommentar\n\n// noch einer\nUC1 -> A.java\n   \n"
    )

    assert result.unique_link_count == 1
    assert result.read_lines == 1
    assert len(diagnostics) == 0


def test_unterschiedliche_abstaende_und_pfeilformen():
    result, _ = parse("UC1->A.java\n  UC2   -->   B.java  ")

    assert result.unique_link_count == 2


def test_doppelte_zuordnung_wird_zusammengefasst():
    """Konzept 4.2: Doppelte identische Zuordnungen koennen zusammengefasst
    werden, ohne daraus zusaetzliche Evidenz abzuleiten. Die Zeile bleibt aber
    als Befund erhalten, weil Konzept 4.13 gelesene Zeilen und eindeutige
    Zuordnungen auseinanderhaelt."""
    result, diagnostics = parse("UC1 -> A.java\nUC1 -> A.java")

    assert result.unique_link_count == 1
    # Beide Zeilen waren wohlgeformte Zuordnungszeilen und zaehlen als gelesen.
    assert result.read_lines == 2
    assert result.duplicate_lines == 1
    befunde = diagnostics.of(DiagnosticCode.DUPLICATE_LINK)
    assert len(befunde) == 1
    assert befunde[0].severity is Severity.INFO


def test_fehlerhafte_zeile_wird_ausgewiesen():
    """Eine Zeile ohne Pfeil ist keine Zuordnung. Der Parser raet nicht, sondern
    weist den Befund aus."""
    result, diagnostics = parse("UC1 -> A.java\nUC2 B.java\nUC3 -> C.java")

    assert result.unique_link_count == 2
    befunde = diagnostics.of(DiagnosticCode.MALFORMED_LINE)
    assert len(befunde) == 1
    assert befunde[0].line_number == 2
    assert befunde[0].severity is Severity.ERROR


def test_fehlerhafte_zeile_bricht_die_verarbeitung_nicht_ab():
    """Der Import sammelt Befunde, statt abzubrechen. Sonst erfuehre der
    Anwender nicht, welche Zuordnungen in Ordnung waren."""
    result, diagnostics = parse("kaputt\nUC1 -> A.java")

    assert result.unique_link_count == 1
    assert diagnostics.has_errors
