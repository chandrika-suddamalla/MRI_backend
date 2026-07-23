from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


def test_backend_env_sources_can_supply_groq_key(monkeypatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "stale-key")

    backend_root = Path(__file__).resolve().parents[1]
    expected_key = None
    for env_path in [backend_root / ".env", backend_root / ".env.example"]:
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith("GROQ_API_KEY="):
                    expected_key = line.split("=", 1)[1].strip().strip('"')
                    break
            if expected_key:
                break

    sys.modules.pop("app.core.config", None)
    import app.core.config as config_module

    importlib.reload(config_module)

    assert expected_key is not None, "backend env sources should contain GROQ_API_KEY"
    assert os.getenv("GROQ_API_KEY") == expected_key
