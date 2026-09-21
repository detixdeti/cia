"""Entscheidungen des Anwenders zu Modellvorschlaegen (F5, Konzept 4.6).

Das Werkzeug schlaegt vor, der Mensch entscheidet. Geprueft wird, dass eine
Entscheidung den Vorschlag nicht veraendert, dass Ueberarbeitung und Vorschlag
getrennt bleiben und dass ein ungueltiger Vorschlag nicht angenommen werden kann.
"""

from __future__ import annotations

import json

from cia.llm.mock import MockProvider
from conftest import api_client, neues_szenario

#: Der Mock schlaegt fuer jede Klasse dasselbe vor. Fuer Katalog.java gibt es
#: suche(String), fuer Buch.java nicht. Dort ist der Eintrag ein Problemfall.
VORSCHLAG = "Methode entfernen"
ANTWORT_MIT_VORSCHLAG = json.dumps(
    {
        "entries": [
            {
                "target_kind": "method",
                "target": "suche(String)",
                "status": "change_proposed",
                "use_case_passage": "Das System liefert die passenden Titel",
                "reason": "UC5 entfaellt",
                "proposal": VORSCHLAG,
            }
        ]
    }
)
ANTWORT_OHNE_VORSCHLAG = json.dumps(
    {
        "entries": [
            {
                "target_kind": "method",
                "target": "suche(String)",
                "status": "no_change_visible",
                "use_case_passage": "",
                "reason": "nichts erkennbar",
                "proposal": None,
            }
        ]
    }
)


def _analysiert(fixture_root, antwort=ANTWORT_MIT_VORSCHLAG):
    """Legt ein Szenario an und startet die Analyse. Gibt Client, Szenario, Lauf zurueck."""
    client = api_client(fixture_root, MockProvider(antwort))
    sid = neues_szenario(client, "UC5")
    lauf = client.post(f"/api/scenarios/{sid}/analyses").json()
    return client, sid, lauf


def _entscheide(client, sid, lauf, kind, class_id="Katalog.java", index=0, **extra):
    body = {"run_id": lauf["run_id"], "subject_id": class_id, "entry_index": index, "kind": kind}
    body.update(extra)
    return client.post(f"/api/scenarios/{sid}/decisions", json=body)


def test_annahme_wird_festgehalten_und_der_vorschlag_bleibt_unveraendert(fixture_root):
    client, sid, lauf = _analysiert(fixture_root)

    antwort = _entscheide(client, sid, lauf, "accepted")

    assert antwort.status_code == 201
    assert antwort.json()["kind"] == "accepted"
    laeufe = client.get(f"/api/scenarios/{sid}/analyses").json()
    ergebnis = {r["class_id"]: r for r in laeufe[0]["results"]}["Katalog.java"]
    assert ergebnis["analysis"]["answer"]["entries"][0]["entry"]["proposal"] == VORSCHLAG


def test_ueberarbeitung_steht_neben_dem_modellvorschlag(fixture_root):
    client, sid, lauf = _analysiert(fixture_root)

    antwort = _entscheide(
        client, sid, lauf, "accepted", revised_proposal="Methode nur deaktivieren"
    )

    assert antwort.json()["revised_proposal"] == "Methode nur deaktivieren"
    laeufe = client.get(f"/api/scenarios/{sid}/analyses").json()
    ergebnis = {r["class_id"]: r for r in laeufe[0]["results"]}["Katalog.java"]
    assert ergebnis["analysis"]["answer"]["entries"][0]["entry"]["proposal"] == VORSCHLAG


def test_ueberarbeitung_ohne_annahme_wird_abgewiesen(fixture_root):
    client, sid, lauf = _analysiert(fixture_root)

    antwort = _entscheide(client, sid, lauf, "rejected", revised_proposal="anders")

    assert antwort.status_code == 422


def test_leere_ueberarbeitung_wird_abgewiesen(fixture_root):
    client, sid, lauf = _analysiert(fixture_root)

    assert _entscheide(client, sid, lauf, "accepted", revised_proposal="  ").status_code == 422


def test_vorschlag_mit_problem_kann_nicht_angenommen_aber_verworfen_werden(fixture_root):
    """Konzept 4.10: Ein ungueltiger Eintrag wird nicht stillschweigend
    uebernommen. Buch.java hat kein suche(String)."""
    client, sid, lauf = _analysiert(fixture_root)

    angenommen = _entscheide(client, sid, lauf, "accepted", class_id="Buch.java")
    verworfen = _entscheide(client, sid, lauf, "rejected", class_id="Buch.java")

    assert angenommen.status_code == 422
    assert "unknown_method" in angenommen.json()["detail"][0]
    assert verworfen.status_code == 201


def test_eintrag_ohne_aenderungsvorschlag_wird_nicht_entschieden(fixture_root):
    client, sid, lauf = _analysiert(fixture_root, ANTWORT_OHNE_VORSCHLAG)

    assert _entscheide(client, sid, lauf, "accepted").status_code == 422


def test_unbekannter_lauf_und_unbekannter_eintrag_werden_abgewiesen(fixture_root):
    client, sid, lauf = _analysiert(fixture_root)

    falscher_lauf = client.post(
        f"/api/scenarios/{sid}/decisions",
        json={"run_id": "gibt-es-nicht", "subject_id": "Katalog.java", "entry_index": 0, "kind": "accepted"},
    )

    assert falscher_lauf.status_code == 422
    assert _entscheide(client, sid, lauf, "accepted", index=5).status_code == 422
    assert _entscheide(client, sid, lauf, "accepted", index=-1).status_code == 422
    assert _entscheide(client, sid, lauf, "accepted", class_id="Gibt.java").status_code == 422


def test_spaetere_entscheidung_ersetzt_die_fruehere_nur_in_der_aktuellen_sicht(fixture_root):
    client, sid, lauf = _analysiert(fixture_root)
    _entscheide(client, sid, lauf, "rejected")
    _entscheide(client, sid, lauf, "accepted")

    daten = client.get(f"/api/scenarios/{sid}/decisions").json()

    assert [d["kind"] for d in daten["history"]] == ["rejected", "accepted"]
    assert [d["kind"] for d in daten["current"]] == ["accepted"]


def test_zurueckgestellt_bleibt_eine_erfasste_entscheidung(fixture_root):
    client, sid, lauf = _analysiert(fixture_root)

    _entscheide(client, sid, lauf, "deferred")

    daten = client.get(f"/api/scenarios/{sid}/decisions").json()
    assert [d["kind"] for d in daten["current"]] == ["deferred"]


def test_entscheidung_nur_im_zustand_bereit_zur_pruefung(fixture_root):
    client, sid, lauf = _analysiert(fixture_root)
    ohne_analyse = neues_szenario(client, "UC5")
    client.post(f"/api/scenarios/{sid}/discard")

    verworfen = _entscheide(client, sid, lauf, "accepted")
    ungeprueft = client.post(
        f"/api/scenarios/{ohne_analyse}/decisions",
        json={"run_id": lauf["run_id"], "subject_id": "Katalog.java", "entry_index": 0, "kind": "accepted"},
    )

    assert verworfen.status_code == 409
    assert ungeprueft.status_code == 409


def test_entscheidungen_eines_szenarios_erscheinen_nicht_in_einem_anderen(fixture_root):
    client, sid, lauf = _analysiert(fixture_root)
    anderes = neues_szenario(client, "UC5")
    _entscheide(client, sid, lauf, "accepted")

    daten = client.get(f"/api/scenarios/{anderes}/decisions").json()

    assert daten == {"history": [], "current": []}


def test_unbekanntes_szenario_liefert_404(fixture_root):
    client, _, _ = _analysiert(fixture_root)

    assert client.get("/api/scenarios/gibt-es-nicht/decisions").status_code == 404
    antwort = client.post(
        "/api/scenarios/gibt-es-nicht/decisions",
        json={"run_id": "x", "subject_id": "K.java", "entry_index": 0, "kind": "accepted"},
    )
    assert antwort.status_code == 404
