"""Upload eines Projektstands aus der Oberflaeche (F1, Konzept 4.2).

Die Oberflaeche liest Dateien im Browser und schickt ihre Inhalte als JSON. Der
Upload muss zum selben Ausgangsstand fuehren wie der Import von der Platte und
Fehler in den Dateien als Befunde melden, statt abzubrechen.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

import cia.api.app as app_module
from cia.api.app import create_app
from cia.importing.project import import_project
from cia.llm.demo import DemoProvider


def _client() -> TestClient:
    return TestClient(create_app())


def _datei(path: str, content: str) -> dict:
    return {"path": path, "content": content}


def _upload_des_beispielprojekts(fixture_root) -> dict:
    """Liest das Beispielprojekt so ein, wie es der Browser hochladen wuerde."""
    use_cases = [
        _datei(f"usecases/{p.name}", p.read_text(encoding="utf-8"))
        for p in sorted((fixture_root / "usecases").glob("*.md"))
    ]
    quellen = fixture_root / "src"
    sources = [
        _datei(p.relative_to(quellen).as_posix(), p.read_text(encoding="utf-8"))
        for p in sorted(quellen.rglob("*.java"))
    ]
    links = fixture_root / "tracelinks.txt"
    return {
        "label": "hochgeladen",
        "use_cases": use_cases,
        "sources": sources,
        "trace_links": _datei("tracelinks.txt", links.read_text(encoding="utf-8")),
    }


def _hochladen(client: TestClient, **felder):
    body = {"label": "test", "use_cases": [], "sources": [], "trace_links": None}
    body.update(felder)
    return client.post("/api/baselines/upload", json=body)


JAVA = "public class K { public void a() {} }"


def test_upload_ergibt_denselben_stand_wie_der_import_von_der_platte(fixture_root):
    client = _client()

    antwort = client.post("/api/baselines/upload", json=_upload_des_beispielprojekts(fixture_root))

    assert antwort.status_code == 201
    von_platte = import_project(fixture_root).summary()["counts"]
    assert antwort.json()["counts"] == von_platte


def test_hochgeladener_stand_hat_denselben_graphen_wie_der_von_der_platte(fixture_root):
    client = _client()
    baseline_id = client.post(
        "/api/baselines/upload", json=_upload_des_beispielprojekts(fixture_root)
    ).json()["baseline_id"]

    graph = client.get(f"/api/baselines/{baseline_id}/graph").json()

    kanten = {(e["source"], e["target"]) for e in graph["edges"]}
    erwartet = {
        (f"uc:{link.use_case_id}", f"class:{link.class_id}")
        for link in import_project(fixture_root).baseline.trace_graph.links
    }
    assert kanten == erwartet


def test_jeder_upload_ist_ein_neuer_ausgangsstand(fixture_root):
    """Konzept 4.2: Ein Stand wird nie ueberschrieben."""
    client = _client()
    upload = _upload_des_beispielprojekts(fixture_root)

    erster = client.post("/api/baselines/upload", json=upload).json()["baseline_id"]
    zweiter = client.post("/api/baselines/upload", json=upload).json()["baseline_id"]

    assert erster != zweiter
    assert len(client.get("/api/baselines").json()) == 2


def test_relative_pfade_und_backslashes_werden_uebernommen(fixture_root):
    client = _client()
    body = _upload_des_beispielprojekts(fixture_root)
    body["sources"] = [_datei("de\\hska\\Katalog.java", JAVA)]
    baseline_id = _hochladen(client, **body).json()["baseline_id"]

    klasse = client.get(f"/api/baselines/{baseline_id}/classes/Katalog.java").json()

    assert klasse["relative_path"] == "de/hska/Katalog.java"


def test_gleicher_dateiname_in_zwei_ordnern_ist_ein_fehler(fixture_root):
    """Konzept 4.2: Eine mehrdeutige Zuordnung wird als Importfehler ausgewiesen."""
    client = _client()

    antwort = _hochladen(client, sources=[_datei("a/K.java", JAVA), _datei("b/K.java", JAVA)])

    assert antwort.json()["counts"]["classes"] == 1
    codes = [d["code"] for d in antwort.json()["diagnostic_entries"] if d["severity"] == "error"]
    assert "ambiguous_class" in codes


def test_link_auf_unbekannte_klasse_ist_ein_fehler_und_der_rest_bleibt(fixture_root):
    client = _client()
    body = _upload_des_beispielprojekts(fixture_root)
    body["trace_links"]["content"] += "\nUC1 -> Gibt.java\n"

    antwort = client.post("/api/baselines/upload", json=body).json()

    fehler = [d for d in antwort["diagnostic_entries"] if d["severity"] == "error"]
    assert [d["code"] for d in fehler] == ["unknown_class"]
    assert antwort["counts"]["trace_links"] == 14


def test_fehlende_linkdatei_ist_ein_befund_kein_abbruch(fixture_root):
    client = _client()
    body = _upload_des_beispielprojekts(fixture_root)
    body["trace_links"] = None

    antwort = client.post("/api/baselines/upload", json=body).json()

    assert antwort["has_errors"] is True
    assert antwort["counts"]["use_cases"] == 6
    assert antwort["counts"]["classes"] == 8
    assert antwort["counts"]["trace_links"] == 0
    assert "wurde nicht gefunden" in antwort["diagnostic_entries"][0]["message"]


def test_dateien_die_nicht_zum_import_gehoeren_werden_gemeldet(fixture_root):
    client = _client()

    antwort = _hochladen(
        client,
        use_cases=[_datei("bild.png", "x"), _datei("UC1.md", "# UC1: Test\n\nText")],
        sources=[_datei("pom.xml", "<project/>"), _datei("K.java", JAVA)],
        trace_links=_datei("tracelinks.txt", "UC1 -> K.java"),
    ).json()

    ignoriert = [d["source_file"] for d in antwort["diagnostic_entries"] if d["code"] == "ignored_file"]
    assert sorted(ignoriert) == ["bild.png", "pom.xml"]
    assert antwort["counts"]["use_cases"] == 1
    assert antwort["counts"]["classes"] == 1


def test_nicht_lesbare_java_datei_bleibt_als_nicht_verarbeitet_sichtbar():
    client = _client()

    antwort = _hochladen(
        client,
        sources=[_datei("Kaputt.java", "public class Kaputt { void a( {")],
        trace_links=_datei("tracelinks.txt", ""),
    ).json()

    warnungen = [d for d in antwort["diagnostic_entries"] if d["code"] == "parse_failed"]
    assert len(warnungen) == 1
    assert antwort["counts"]["parsed_classes"] == 0


def test_use_case_ohne_ueberschrift_nimmt_den_dateinamen_als_kennung():
    client = _client()

    antwort = _hochladen(
        client,
        use_cases=[_datei("ordner/UC7.md", "Nur Text ohne Ueberschrift")],
        sources=[_datei("K.java", JAVA)],
        trace_links=_datei("tracelinks.txt", "UC7 -> K.java"),
    ).json()

    assert antwort["counts"]["use_cases"] == 1
    assert antwort["counts"]["trace_links"] == 1


def test_leerer_upload_wird_abgewiesen():
    assert _hochladen(_client()).status_code == 422


def test_datei_ohne_namen_wird_abgewiesen():
    assert _hochladen(_client(), sources=[_datei("  ", JAVA)]).status_code == 422


def test_zu_grosser_upload_wird_abgewiesen(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_UPLOAD_FILES", 2)

    antwort = _hochladen(_client(), sources=[_datei(f"K{i}.java", JAVA) for i in range(3)])

    assert antwort.status_code == 413


def test_hochgeladener_stand_traegt_ein_szenario_bis_zur_analyse(fixture_root):
    """Der Upload ist gleichwertig zum Import von der Platte: Es geht weiter bis
    zur strukturellen Auswahl."""
    client = _client()
    baseline_id = client.post(
        "/api/baselines/upload", json=_upload_des_beispielprojekts(fixture_root)
    ).json()["baseline_id"]
    body = {
        "title": "t",
        "direction": "requirement_to_code",
        "requirement_changes": [{"kind": "deactivate", "use_case_id": "UC5"}],
    }

    szenario = client.post(f"/api/baselines/{baseline_id}/scenarios", json=body).json()
    auswahl = client.get(f"/api/scenarios/{szenario['scenario_id']}/selection").json()

    assert [c["class_id"] for c in auswahl["candidates"]] == ["Buch.java", "Katalog.java"]


# --- Info ------------------------------------------------------------------------------------


def test_info_nennt_den_mock_als_standardanbieter():
    antwort = _client().get("/api/info")

    assert antwort.json() == {"provider": "mock", "settings": {}}


def test_info_nennt_den_demo_anbieter():
    client = TestClient(create_app(provider=DemoProvider()))

    assert client.get("/api/info").json()["provider"] == "demo"
