"""Gemeinsame Hilfsmittel der Tests."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pytest
from fastapi.testclient import TestClient

from cia.api.app import create_app
from cia.domain.artifacts import JavaClass, UseCase
from cia.domain.baseline import Baseline
from cia.domain.ids import BaselineId, ClassId, ScenarioId, UseCaseId
from cia.domain.links import TraceGraph, TraceLink

TEST_BASELINE = BaselineId("test-baseline")

#: Pfad zum synthetischen Beispielprojekt.
FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "sample-project"
ECOMMERCE_FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "ecommerce-platform"


def make_baseline(
    links: Iterable[tuple[str, str]],
    extra_use_cases: Iterable[str] = (),
    extra_classes: Iterable[str] = (),
    inactive_use_cases: Iterable[str] = (),
) -> Baseline:
    """Baut eine minimale Baseline aus Kantenpaaren.

    Die Artefakte erhalten leere Texte. Fuer die strukturelle Auswahl ist nur
    die Relation massgeblich; ihr Inhalt spielt keine Rolle.
    """
    trace_links = [TraceLink(UseCaseId(u), ClassId(c)) for u, c in links]
    inactive = set(inactive_use_cases)

    use_case_ids = {link.use_case_id for link in trace_links}
    use_case_ids.update(UseCaseId(u) for u in extra_use_cases)
    class_ids = {link.class_id for link in trace_links}
    class_ids.update(ClassId(c) for c in extra_classes)

    use_cases = {
        uid: UseCase(
            id=uid,
            baseline_id=TEST_BASELINE,
            title=uid,
            text=f"Text von {uid}",
            active=uid not in inactive,
        )
        for uid in use_case_ids
    }
    classes = {
        cid: JavaClass(
            id=cid,
            baseline_id=TEST_BASELINE,
            file_name=cid,
            relative_path=cid,
            source="",
        )
        for cid in class_ids
    }

    return Baseline.create(
        baseline_id=TEST_BASELINE,
        label="test",
        use_cases=use_cases,
        classes=classes,
        trace_graph=TraceGraph(trace_links),
    )


def scenario_id(name: str = "s1") -> ScenarioId:
    return ScenarioId(name)


def api_client(fixture_root, provider=None, protocol_dir=None, **kwargs) -> TestClient:
    """Ein Testclient fuer die Schnittstelle mit importiertem Beispielprojekt."""
    app = create_app(autoload=fixture_root, provider=provider, protocol_dir=protocol_dir)
    return TestClient(app, **kwargs)


def neues_szenario(client: TestClient, *use_case_ids: str) -> str:
    """Legt ein Szenario an, das die genannten Use Cases deaktiviert."""
    baseline_id = client.get("/api/baselines").json()[0]["baseline_id"]
    body = {
        "title": "Test",
        "direction": "requirement_to_code",
        "requirement_changes": [{"kind": "deactivate", "use_case_id": u} for u in use_case_ids],
    }
    return client.post(f"/api/baselines/{baseline_id}/scenarios", json=body).json()["scenario_id"]


@pytest.fixture(scope="session")
def fixture_root() -> Path:
    if not FIXTURE_ROOT.is_dir():
        pytest.skip(f"Beispielprojekt fehlt: {FIXTURE_ROOT}")
    return FIXTURE_ROOT


@pytest.fixture(scope="session")
def ecommerce_fixture_root() -> Path:
    if not ECOMMERCE_FIXTURE_ROOT.is_dir():
        pytest.skip(f"E-Commerce-Projekt fehlt: {ECOMMERCE_FIXTURE_ROOT}")
    return ECOMMERCE_FIXTURE_ROOT
