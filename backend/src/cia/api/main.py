"""Einstiegspunkt fuer ``uvicorn cia.api.main:app``.

Umgebungsvariablen:
- ``CIA_AUTOLOAD_PROJECT``: Projektstand, der beim Start importiert wird,
  z. B. ``../fixtures/sample-project``.
- ``CIA_PROTOCOL_DIR``: Verzeichnis fuer das Protokoll (Vorgabe: ``protocol``).
- ``CIA_CORS_ORIGINS``: Adressen der Oberflaeche, durch Komma getrennt
  (Vorgabe: ``http://localhost:5173`` und ``http://127.0.0.1:5173``).
- ``CIA_LLM``: ``demo`` liefert gekennzeichnete Beispielantworten fuer
  Vorfuehrungen. Ohne Angabe antwortet der Mock, der nichts bewertet.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..llm.demo import DemoProvider
from .app import create_app

_autoload = os.environ.get("CIA_AUTOLOAD_PROJECT")
app = create_app(
    autoload=Path(_autoload).expanduser() if _autoload else None,
    provider=DemoProvider() if os.environ.get("CIA_LLM") == "demo" else None,
    protocol_dir=Path(os.environ.get("CIA_PROTOCOL_DIR", "protocol")),
    cors_origins=[o.strip() for o in os.environ["CIA_CORS_ORIGINS"].split(",")]
    if "CIA_CORS_ORIGINS" in os.environ
    else None,
)
