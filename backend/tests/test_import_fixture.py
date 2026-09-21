"""Import des synthetischen Beispielprojekts.

Geprueft wird der Weg von den Dateien auf der Platte bis zur Baseline, samt
Java-Parser. Die erwarteten Zahlen beziehen sich auf das Fixture unter
``fixtures/sample-project`` und nicht auf das spaeter bereitgestellte System.
"""

from __future__ import annotations

from cia.domain.artifacts import MethodSignature
from cia.domain.ids import ClassId, UseCaseId
from cia.importing.project import import_project
from cia.importing.result import DiagnosticCode, Severity


def test_import_liest_alle_artefakte(fixture_root):
    report = import_project(fixture_root, label="bib-fixture")
    counts = report.baseline.counts()

    assert counts["use_cases"] == 6
    assert counts["classes"] == 8
    assert counts["parsed_classes"] == 8
    assert counts["trace_links"] == 14


def test_gelesene_zeilen_und_eindeutige_zuordnungen_sind_getrennt(fixture_root):
    """Konzept 4.13 verlangt diese Unterscheidung ausdruecklich."""
    report = import_project(fixture_root)

    assert report.read_link_lines == 15
    assert report.duplicate_link_lines == 1
    assert len(report.baseline.trace_graph) == 14


def test_import_meldet_keine_fehler(fixture_root):
    report = import_project(fixture_root)

    fehler = report.diagnostics.by_severity(Severity.ERROR)
    assert fehler == [], f"unerwartete Fehler: {[str(f) for f in fehler]}"


def test_klasse_ohne_zuordnung_wird_gemeldet_aber_nicht_entwarnt(fixture_root):
    """Konzept 4.1: Ein nicht verknuepftes Artefakt gilt nicht allein deshalb
    als sicher unbeeintraechtigt."""
    report = import_project(fixture_root)

    assert ClassId("Konfiguration.java") in report.baseline.unlinked_class_ids
    befunde = report.diagnostics.of(DiagnosticCode.UNLINKED_CLASS)
    assert any("Konfiguration.java" in b.message for b in befunde)
    assert all(b.severity is Severity.INFO for b in befunde)


def test_use_case_ohne_zuordnung_wird_gemeldet(fixture_root):
    report = import_project(fixture_root)

    assert UseCaseId("UC6") in report.baseline.unlinked_use_case_ids
    befunde = report.diagnostics.of(DiagnosticCode.UNLINKED_USE_CASE)
    assert any("UC6" in b.message for b in befunde)


def test_use_case_text_wird_uebernommen(fixture_root):
    report = import_project(fixture_root)
    uc1 = report.baseline.use_case(UseCaseId("UC1"))

    assert uc1 is not None
    assert uc1.title == "Buch ausleihen"
    assert "hoechstens zehn Titel" in uc1.text


def test_parser_erkennt_methoden_mit_quelltextbereich(fixture_root):
    report = import_project(fixture_root)
    service = report.baseline.java_class(ClassId("AusleihService.java"))

    assert service is not None and service.parsed
    namen = {m.signature.name for m in service.methods}
    assert {"ausleihen", "zurueckgeben", "offeneAusleihen", "alleOffenen"} <= namen

    ausleihen = service.method(
        MethodSignature("ausleihen", ("Mitglied", "Buch"))
    )
    assert ausleihen is not None
    assert ausleihen.ref.source_range.start_line < ausleihen.ref.source_range.end_line
    assert "buch.entnehmen()" in ausleihen.source


def test_ueberladene_methoden_werden_unterschieden(fixture_root):
    """Konzept 4.2: Ueberladene Methoden werden anhand ihrer Signaturen
    unterschieden, insbesondere anhand von Name und Parametertypen."""
    report = import_project(fixture_root)
    katalog = report.baseline.java_class(ClassId("Katalog.java"))

    assert katalog is not None
    treffer = katalog.methods_named("suche")
    assert len(treffer) == 2

    signaturen = {m.signature for m in treffer}
    assert MethodSignature("suche", ("String",)) in signaturen
    assert MethodSignature("suche", ("String", "String")) in signaturen

    # Die Quelltextbereiche der beiden Ueberladungen ueberschneiden sich nicht.
    a, b = sorted(treffer, key=lambda m: m.ref.source_range.start_byte)
    assert a.ref.source_range.end_byte <= b.ref.source_range.start_byte


def test_konstruktoren_werden_erkannt(fixture_root):
    report = import_project(fixture_root)
    mitglied = report.baseline.java_class(ClassId("Mitglied.java"))

    assert mitglied is not None
    konstruktoren = [m for m in mitglied.methods if m.is_constructor]
    assert len(konstruktoren) == 1
    assert konstruktoren[0].signature == MethodSignature("Mitglied", ("String", "String"))


def test_methodenreferenz_traegt_baseline_und_klasse(fixture_root):
    """Konzept 4.2: Identitaet, Version und Position sind getrennte Merkmale.
    Eine Referenz muss stets auf einen bestimmten Ausgangsstand zurueckfuehren."""
    report = import_project(fixture_root)
    buch = report.baseline.java_class(ClassId("Buch.java"))

    assert buch is not None
    for methode in buch.methods:
        assert methode.ref.baseline_id == report.baseline.id
        assert methode.ref.class_id == ClassId("Buch.java")
