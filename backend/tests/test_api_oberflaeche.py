"""Endpunkte, die die Oberflaeche braucht: Szenarien auflisten, Methoden-Quelltext
und Anzeige-Ereignisse fuer das Protokoll (Konzept 4.6 und 4.13)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from cia.api.app import create_app
from conftest import api_client, neues_szenario


def _ereignis(client, sid, **felder):
    return client.post(f"/api/scenarios/{sid}/events", json=felder)


# --- Szenarien auflisten -----------------------------------------------------------------------


def test_szenarien_eines_ausgangsstands_werden_der_reihe_nach_aufgelistet(fixture_root):
    client = api_client(fixture_root)
    baseline_id = client.get("/api/baselines").json()[0]["baseline_id"]
    erstes = neues_szenario(client, "UC5")
    zweites = neues_szenario(client, "UC1")

    liste = client.get(f"/api/baselines/{baseline_id}/scenarios").json()

    assert [s["scenario_id"] for s in liste] == [erstes, zweites]
    assert liste[0]["state"] == "structurally_checked"


def test_auflistung_ohne_szenarien_ist_leer(fixture_root):
    client = api_client(fixture_root)
    baseline_id = client.get("/api/baselines").json()[0]["baseline_id"]

    assert client.get(f"/api/baselines/{baseline_id}/scenarios").json() == []


def test_auflistung_zeigt_auch_verworfene_szenarien(fixture_root):
    client = api_client(fixture_root)
    baseline_id = client.get("/api/baselines").json()[0]["baseline_id"]
    verworfen = neues_szenario(client, "UC5")
    client.post(f"/api/scenarios/{verworfen}/discard")

    liste = client.get(f"/api/baselines/{baseline_id}/scenarios").json()

    assert [s["state"] for s in liste] == ["discarded"]


def test_auflistung_fuer_unbekannten_ausgangsstand_liefert_404(fixture_root):
    client = api_client(fixture_root)

    assert client.get("/api/baselines/gibt-es-nicht/scenarios").status_code == 404


# --- Methoden-Quelltext ----------------------------------------------------------------------


def test_klassendetail_liefert_den_quelltext_jeder_methode(fixture_root):
    client = api_client(fixture_root)
    baseline_id = client.get("/api/baselines").json()[0]["baseline_id"]

    klasse = client.get(f"/api/baselines/{baseline_id}/classes/Katalog.java").json()

    suche = [m for m in klasse["methods"] if m["ref"]["signature"]["parameter_types"] == ["String"]]
    assert "titelFragment" in suche[0]["source"]
    assert "autorFragment" not in suche[0]["source"]


def test_methodenquelltext_stimmt_mit_dem_bereich_der_referenz_ueberein(fixture_root):
    """Der Quelltext gehoert zu genau dem Bereich, den die Referenz nennt
    (Konzept 4.2). Die Bereiche sind Byte-Positionen."""
    client = api_client(fixture_root)
    baseline_id = client.get("/api/baselines").json()[0]["baseline_id"]

    klasse = client.get(f"/api/baselines/{baseline_id}/classes/Katalog.java").json()
    daten = klasse["source"].encode("utf-8")

    for methode in klasse["methods"]:
        bereich = methode["ref"]["source_range"]
        ausschnitt = daten[bereich["start_byte"] : bereich["end_byte"]].decode("utf-8")
        assert ausschnitt == methode["source"]


# --- Anzeige-Ereignisse ------------------------------------------------------------------------


def test_anzeige_ereignis_wird_im_protokoll_festgehalten(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")

    antwort = _ereignis(client, sid, type="comparison_shown", subject_id="Katalog.java")

    assert antwort.status_code == 201
    eintraege = client.get(f"/api/scenarios/{sid}/protocol").json()
    letzter = eintraege[-1]
    assert letzter["kind"] == "ui_event"
    assert letzter["data"] == {
        "type": "comparison_shown",
        "subject_id": "Katalog.java",
        "detail": None,
    }
    assert antwort.json()["seq"] == letzter["seq"]


def test_alle_ereignisarten_sind_erlaubt(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")

    for art in ("marking_shown", "comparison_shown", "context_shown"):
        assert _ereignis(client, sid, type=art).status_code == 201


def test_unbekannte_ereignisart_wird_abgewiesen(fixture_root):
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")

    assert _ereignis(client, sid, type="irgendwas").status_code == 422


def test_ereignis_zu_unbekanntem_szenario_liefert_404(fixture_root):
    client = api_client(fixture_root)

    assert _ereignis(client, "gibt-es-nicht", type="marking_shown").status_code == 404


def test_ereignis_bleibt_auch_nach_dem_verwerfen_moeglich(fixture_root):
    """Angezeigt werden kann auch ein verworfenes Szenario (Konzept 4.12)."""
    client = api_client(fixture_root)
    sid = neues_szenario(client, "UC5")
    client.post(f"/api/scenarios/{sid}/discard")

    assert _ereignis(client, sid, type="marking_shown").status_code == 201


# --- Dokumentation ------------------------------------------------------------------------------


def test_die_interaktive_dokumentation_laesst_sich_erzeugen(fixture_root):
    """/docs wird aus den Typen der Endpunkte gebaut. Ein Fehler dort faellt
    sonst erst beim Aufruf im Browser auf."""
    client = api_client(fixture_root)

    antwort = client.get("/openapi.json")

    assert antwort.status_code == 200
    pfade = antwort.json()["paths"]
    assert "/api/scenarios/{scenario_id}/analyses" in pfade
    assert "/api/scenarios/{scenario_id}/events" in pfade


# --- Erlaubte Adressen der Oberflaeche -------------------------------------------------------


def _erlaubte_herkunft(client, herkunft: str) -> str | None:
    antwort = client.get("/api/info", headers={"Origin": herkunft})
    return antwort.headers.get("access-control-allow-origin")


def test_vorgabe_erlaubt_den_vite_entwicklungsserver():
    client = TestClient(create_app())

    assert _erlaubte_herkunft(client, "http://localhost:5173") == "http://localhost:5173"
    assert _erlaubte_herkunft(client, "http://localhost:5199") is None


def test_erlaubte_adressen_lassen_sich_einstellen():
    client = TestClient(create_app(cors_origins=["http://localhost:5199"]))

    assert _erlaubte_herkunft(client, "http://localhost:5199") == "http://localhost:5199"
    assert _erlaubte_herkunft(client, "http://localhost:5173") is None
