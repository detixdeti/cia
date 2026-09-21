"""Schnittstelle am Beispielprojekt.

Geprueft werden Import, Graph, Teilgraph, Artefaktdetails und die strukturelle
Auswahl in beiden Richtungen. Die erwarteten Werte beziehen sich auf das Fixture
unter ``fixtures/sample-project``. Besonderes Augenmerk gilt den Faellen, in
denen Fehlen kein Befund der Unbedenklichkeit ist (Konzept 4.13) und keine
Loeschfreigabe entsteht (Konzept 4.6).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cia.api.app import create_app


@pytest.fixture
def client(fixture_root):
    with TestClient(create_app(autoload=fixture_root)) as test_client:
        yield test_client


@pytest.fixture
def baseline_id(client) -> str:
    return client.get("/api/baselines").json()[0]["baseline_id"]


def _ids(nodes, kind: str) -> set[str]:
    return {n["ref"] for n in nodes if n["kind"] == kind}


def _szenario(client, baseline_id: str, body: dict):
    return client.post(f"/api/baselines/{baseline_id}/scenarios", json=body)


def _deaktivierung(*use_case_ids: str) -> dict:
    return {
        "title": "Test",
        "direction": "requirement_to_code",
        "requirement_changes": [
            {"kind": "deactivate", "use_case_id": u} for u in use_case_ids
        ],
    }


# --- Import und Baseline (F1) ------------------------------------------------


def test_import_ueber_die_schnittstelle_liefert_zaehlwerte(client, fixture_root):
    antwort = client.post("/api/baselines", json={"path": str(fixture_root), "label": "bib"})

    assert antwort.status_code == 201
    daten = antwort.json()
    assert daten["label"] == "bib"
    assert daten["counts"]["use_cases"] == 6
    assert daten["counts"]["trace_links"] == 14
    assert daten["counts"]["read_link_lines"] == 15
    assert daten["counts"]["duplicate_link_lines"] == 1
    assert daten["has_errors"] is False


def test_import_haelt_befunde_ueber_klassen_und_use_cases_ohne_zuordnung_fest(
    client, baseline_id
):
    daten = client.get(f"/api/baselines/{baseline_id}").json()

    meldungen = {d["code"]: d for d in daten["diagnostic_entries"]}
    assert "unlinked_class" in meldungen
    assert "unlinked_use_case" in meldungen
    assert meldungen["unlinked_class"]["severity"] == "info"


def test_import_eines_fehlenden_verzeichnisses_wird_abgewiesen(client, tmp_path):
    antwort = client.post("/api/baselines", json={"path": str(tmp_path / "gibt-es-nicht")})

    assert antwort.status_code == 422


def test_unbekannter_ausgangsstand_liefert_404(client):
    assert client.get("/api/baselines/gibt-es-nicht").status_code == 404
    assert client.get("/api/baselines/gibt-es-nicht/graph").status_code == 404


# --- Graph (F2) -----------------------------------------------------------------


def test_graph_enthaelt_alle_artefakte_und_eindeutigen_kanten(client, baseline_id):
    graph = client.get(f"/api/baselines/{baseline_id}/graph").json()

    assert len(_ids(graph["nodes"], "use_case")) == 6
    assert len(_ids(graph["nodes"], "class")) == 8
    assert len(graph["edges"]) == 14


def test_graph_zeigt_artefakte_ohne_zuordnung_als_nicht_verlinkt(client, baseline_id):
    """Konzept 4.1: Ein nicht verknuepftes Artefakt bleibt sichtbar und gilt nicht
    als sicher unbeeintraechtigt."""
    graph = client.get(f"/api/baselines/{baseline_id}/graph").json()
    knoten = {n["id"]: n for n in graph["nodes"]}

    assert knoten["class:Konfiguration.java"]["linked"] is False
    assert knoten["uc:UC6"]["linked"] is False
    assert knoten["uc:UC1"]["linked"] is True


def test_graph_enthaelt_nur_kanten_zwischen_use_case_und_klasse(client, baseline_id):
    """Konzept 4.3: UC-zu-UC-Kanten werden weder importiert noch abgeleitet."""
    graph = client.get(f"/api/baselines/{baseline_id}/graph").json()

    for kante in graph["edges"]:
        assert kante["source"].startswith("uc:")
        assert kante["target"].startswith("class:")
        assert kante["origin"] == "imported"


def test_teilgraph_zu_use_case_zeigt_nur_dessen_klassen(client, baseline_id):
    """UC3 teilt Mitglied.java mit UC1 und UC4. Beide gehoeren nicht in den
    Teilgraphen, weil nicht ueber gemeinsame Klassen ausgebreitet wird."""
    graph = client.get(
        f"/api/baselines/{baseline_id}/subgraph", params={"use_case": "UC3"}
    ).json()

    assert _ids(graph["nodes"], "use_case") == {"UC3"}
    assert _ids(graph["nodes"], "class") == {"Mitglied.java"}
    assert len(graph["edges"]) == 1


def test_teilgraph_zu_klasse_zeigt_deren_use_cases(client, baseline_id):
    graph = client.get(
        f"/api/baselines/{baseline_id}/subgraph", params={"class": "Ausleihe.java"}
    ).json()

    assert _ids(graph["nodes"], "use_case") == {"UC1", "UC2", "UC4"}
    assert _ids(graph["nodes"], "class") == {"Ausleihe.java"}


def test_teilgraph_unterscheidet_auswahl_und_nachbarn(client, baseline_id):
    graph = client.get(
        f"/api/baselines/{baseline_id}/subgraph", params={"use_case": "UC3"}
    ).json()
    knoten = {n["ref"]: n for n in graph["nodes"]}

    assert knoten["UC3"]["selected"] is True
    assert knoten["Mitglied.java"]["selected"] is False


def test_teilgraph_eines_use_cases_ohne_zuordnung_bleibt_sichtbar(client, baseline_id):
    graph = client.get(
        f"/api/baselines/{baseline_id}/subgraph", params={"use_case": "UC6"}
    ).json()

    assert _ids(graph["nodes"], "use_case") == {"UC6"}
    assert graph["edges"] == []
    assert graph["nodes"][0]["linked"] is False


def test_teilgraph_ohne_auswahl_wird_abgewiesen(client, baseline_id):
    assert client.get(f"/api/baselines/{baseline_id}/subgraph").status_code == 422


def test_teilgraph_mit_unbekannter_kennung_nennt_diese(client, baseline_id):
    antwort = client.get(
        f"/api/baselines/{baseline_id}/subgraph", params={"use_case": ["UC1", "UC99"]}
    )

    assert antwort.status_code == 404
    assert "UC99" in antwort.json()["detail"]


# --- Artefaktdetails -----------------------------------------------------------------


def test_use_case_detail_nennt_text_und_klassen(client, baseline_id):
    daten = client.get(f"/api/baselines/{baseline_id}/use-cases/UC5").json()

    assert daten["title"]
    assert daten["text"]
    assert daten["class_ids"] == ["Buch.java", "Katalog.java"]
    assert daten["linked"] is True


def test_klassendetail_traegt_vollstaendige_methodenreferenzen(client, baseline_id):
    """Konzept 4.2: Baseline, Klasse, Signatur und Quelltextbereich gehoeren
    zusammen. Ueberladene Methoden bleiben ueber ihre Parametertypen getrennt."""
    daten = client.get(f"/api/baselines/{baseline_id}/classes/Katalog.java").json()

    suche = [m for m in daten["methods"] if m["ref"]["signature"]["name"] == "suche"]
    assert {tuple(m["ref"]["signature"]["parameter_types"]) for m in suche} == {
        ("String",),
        ("String", "String"),
    }
    for methode in suche:
        ref = methode["ref"]
        assert ref["baseline_id"] == baseline_id
        assert ref["class_id"] == "Katalog.java"
        assert set(ref["source_range"]) == {"start_line", "end_line", "start_byte", "end_byte"}


def test_unbekannte_artefakte_liefern_404(client, baseline_id):
    assert client.get(f"/api/baselines/{baseline_id}/use-cases/UC99").status_code == 404
    assert client.get(f"/api/baselines/{baseline_id}/classes/Gibt.java").status_code == 404


# --- Szenarien, Anforderungsrichtung -----------------------------------------------------


def test_deaktivierung_liefert_kandidaten_mit_erhaltungskontext(client, baseline_id):
    szenario = _szenario(client, baseline_id, _deaktivierung("UC5"))
    assert szenario.status_code == 201
    sid = szenario.json()["scenario_id"]

    auswahl = client.get(f"/api/scenarios/{sid}/selection").json()

    kandidaten = {c["class_id"]: c for c in auswahl["candidates"]}
    assert set(kandidaten) == {"Buch.java", "Katalog.java"}
    assert kandidaten["Buch.java"]["preservation_context_ids"] == ["UC1", "UC2"]


def test_klasse_ohne_verbleibenden_use_case_erhaelt_keine_loeschfreigabe(client, baseline_id):
    """Konzept 4.6: Auch wenn Katalog.java nach UC5 keinen aktiven Use Case mehr
    hat, steht in der Ausgabe kein Feld, das eine Freigabe ausdruecken koennte."""
    sid = _szenario(client, baseline_id, _deaktivierung("UC5")).json()["scenario_id"]

    auswahl = client.get(f"/api/scenarios/{sid}/selection").json()
    katalog = next(c for c in auswahl["candidates"] if c["class_id"] == "Katalog.java")

    assert katalog["preservation_context_ids"] == []
    assert set(katalog) == {
        "class_id",
        "triggering_use_case_ids",
        "preservation_context_ids",
        "parsed",
    }


def test_use_case_ohne_zuordnung_wird_als_ungeklaert_ausgewiesen(client, baseline_id):
    """Konzept 4.3: Die leere Kandidatenmenge bedeutet nicht, dass die Aenderung
    wirkungslos waere."""
    sid = _szenario(client, baseline_id, _deaktivierung("UC6")).json()["scenario_id"]

    auswahl = client.get(f"/api/scenarios/{sid}/selection").json()

    assert auswahl["candidates"] == []
    assert [u["use_case_id"] for u in auswahl["unresolved"]] == ["UC6"]


def test_neuer_use_case_ohne_klassenauswahl_meldet_fehlende_zuordnung(client, baseline_id):
    body = {
        "title": "Neu",
        "direction": "requirement_to_code",
        "requirement_changes": [
            {"kind": "add", "use_case_id": "UC7", "target_text": "Vormerkung eines Titels"}
        ],
    }
    sid = _szenario(client, baseline_id, body).json()["scenario_id"]

    auswahl = client.get(f"/api/scenarios/{sid}/selection").json()

    assert auswahl["candidates"] == []
    assert auswahl["unresolved"][0]["reason"] == "keine Zuordnung fuer die Analyse vorhanden"


def test_neuer_use_case_mit_klassenauswahl_aendert_den_ausgangsstand_nicht(client, baseline_id):
    body = {
        "title": "Neu",
        "direction": "requirement_to_code",
        "requirement_changes": [
            {
                "kind": "add",
                "use_case_id": "UC7",
                "target_text": "Vormerkung eines Titels",
                "manual_class_ids": ["Katalog.java", "Katalog.java"],
            }
        ],
    }
    sid = _szenario(client, baseline_id, body).json()["scenario_id"]

    auswahl = client.get(f"/api/scenarios/{sid}/selection").json()
    graph = client.get(f"/api/baselines/{baseline_id}/graph").json()

    assert [c["class_id"] for c in auswahl["candidates"]] == ["Katalog.java"]
    assert len(graph["edges"]) == 14
    assert "UC7" not in _ids(graph["nodes"], "use_case")


def test_neues_szenario_ist_strukturell_geprueft(client, baseline_id):
    szenario = _szenario(client, baseline_id, _deaktivierung("UC1")).json()

    assert szenario["state"] == "structurally_checked"
    assert szenario["baseline_id"] == baseline_id


def test_szenario_ohne_aenderung_wird_abgewiesen(client, baseline_id):
    """Eine leere Aenderungsmenge liesse sich als 'kein Einfluss' lesen."""
    body = {"title": "leer", "direction": "requirement_to_code"}

    assert _szenario(client, baseline_id, body).status_code == 422


def test_szenario_sammelt_alle_eingabefehler(client, baseline_id):
    body = _deaktivierung("UC98", "UC99")

    antwort = _szenario(client, baseline_id, body)

    assert antwort.status_code == 422
    probleme = antwort.json()["detail"]
    assert any("UC98" in p for p in probleme)
    assert any("UC99" in p for p in probleme)


def test_neuer_use_case_darf_keine_vergebene_kennung_tragen(client, baseline_id):
    body = {
        "title": "Kollision",
        "direction": "requirement_to_code",
        "requirement_changes": [{"kind": "add", "use_case_id": "UC1", "target_text": "x"}],
    }

    assert _szenario(client, baseline_id, body).status_code == 422


def test_manuelle_zuordnung_zu_unbekannter_klasse_wird_abgewiesen(client, baseline_id):
    body = {
        "title": "x",
        "direction": "requirement_to_code",
        "requirement_changes": [
            {
                "kind": "add",
                "use_case_id": "UC7",
                "target_text": "x",
                "manual_class_ids": ["Gibt.java"],
            }
        ],
    }

    assert _szenario(client, baseline_id, body).status_code == 422


# --- Szenarien, Gegenrichtung -----------------------------------------------------------


def _codeaenderung(class_id: str, signature: dict | None = None) -> dict:
    item = {"class_id": class_id, "after": "// geaendert"}
    if signature is not None:
        item["signature"] = signature
    return {"title": "Code", "direction": "code_to_requirement", "code_changes": [item]}


def test_gegenrichtung_liefert_zugeordnete_use_cases(client, baseline_id):
    sid = _szenario(client, baseline_id, _codeaenderung("Ausleihe.java")).json()["scenario_id"]

    auswahl = client.get(f"/api/scenarios/{sid}/selection").json()

    assert auswahl["direction"] == "code_to_requirement"
    assert [c["use_case_id"] for c in auswahl["candidates"]] == ["UC1", "UC2", "UC4"]


def test_gegenrichtung_weist_klasse_ohne_zuordnung_als_nicht_zuordenbar_aus(client, baseline_id):
    sid = _szenario(client, baseline_id, _codeaenderung("Konfiguration.java")).json()[
        "scenario_id"
    ]

    auswahl = client.get(f"/api/scenarios/{sid}/selection").json()

    assert auswahl["candidates"] == []
    assert auswahl["unassignable_class_ids"] == ["Konfiguration.java"]


def test_ausgangsfassung_einer_methodenaenderung_stammt_aus_dem_import(client, baseline_id):
    """Konzept 4.7: Das Feld der Ausgangsfassung wird aus dem importierten Stand
    vorbefuellt. Der Anwender gibt nur die geaenderte Fassung ein."""
    signatur = {"name": "suche", "parameter_types": ["String"]}
    szenario = _szenario(client, baseline_id, _codeaenderung("Katalog.java", signatur)).json()

    vorher = szenario["code_changes"][0]["before"]

    assert vorher.lstrip().startswith("public List<Buch> suche(String titelFragment)")
    assert "autorFragment" not in vorher


def test_methodenaenderung_mit_unbekannter_signatur_wird_abgewiesen(client, baseline_id):
    signatur = {"name": "suche", "parameter_types": ["int"]}

    antwort = _szenario(client, baseline_id, _codeaenderung("Katalog.java", signatur))

    assert antwort.status_code == 422


def test_codeaenderung_an_unbekannter_klasse_wird_abgewiesen(client, baseline_id):
    assert _szenario(client, baseline_id, _codeaenderung("Gibt.java")).status_code == 422


def test_richtungen_lassen_sich_nicht_mischen(client, baseline_id):
    body = _deaktivierung("UC1")
    body["code_changes"] = [{"class_id": "Buch.java", "after": "x"}]

    assert _szenario(client, baseline_id, body).status_code == 422


# --- Verwerfen -----------------------------------------------------------------------------


def test_verworfenes_szenario_bleibt_abrufbar_und_der_ausgangsstand_unveraendert(
    client, baseline_id
):
    """Konzept 4.12: Die bis dahin erhaltenen Ergebnisse bleiben als Ergebnisse
    eines verworfenen Szenarios sichtbar."""
    sid = _szenario(client, baseline_id, _deaktivierung("UC5")).json()["scenario_id"]

    verworfen = client.post(f"/api/scenarios/{sid}/discard")

    assert verworfen.status_code == 200
    assert verworfen.json()["state"] == "discarded"
    assert client.get(f"/api/scenarios/{sid}/selection").status_code == 200
    assert client.get(f"/api/baselines/{baseline_id}").json()["counts"]["trace_links"] == 14


def test_zweites_verwerfen_ist_ein_konflikt(client, baseline_id):
    sid = _szenario(client, baseline_id, _deaktivierung("UC5")).json()["scenario_id"]
    client.post(f"/api/scenarios/{sid}/discard")

    assert client.post(f"/api/scenarios/{sid}/discard").status_code == 409


def test_unbekanntes_szenario_liefert_404(client):
    assert client.get("/api/scenarios/gibt-es-nicht").status_code == 404
    assert client.get("/api/scenarios/gibt-es-nicht/selection").status_code == 404
