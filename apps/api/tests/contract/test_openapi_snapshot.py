from __future__ import annotations

import json
from pathlib import Path

from app.core.settings import get_settings


def test_openapi_contains_p0_contract_paths(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/postgres")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service")
    get_settings.cache_clear()
    from app.core.app import create_app

    app = create_app()
    schema = app.openapi()
    snapshot_path = Path(__file__).resolve().parents[1] / "snapshots" / "openapi_p0_paths.json"
    expected = json.loads(snapshot_path.read_text())

    actual_paths = {
        path: sorted(list(methods.keys()))
        for path, methods in schema["paths"].items()
        if path in expected
    }

    assert actual_paths == expected
    get_settings.cache_clear()
