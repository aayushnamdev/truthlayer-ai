"""Shared helpers. All fixtures live in tests/fixtures and are SYNTHETIC."""
from pathlib import Path

import pytest

from truthlayer.config import Config

FX = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    """Tests never use a real key: clear it and stop the CLI from reading a developer's .env file."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    import truthlayer.cli
    monkeypatch.setattr(truthlayer.cli, "load_dotenv", lambda root=".": 0)


@pytest.fixture
def cfg(tmp_path):
    c = Config.fixtures(FX, tmp_path / "out")
    c.root = FX.parent.parent
    return c


@pytest.fixture
def analysis(cfg):
    from truthlayer.drift import analyse
    return analyse(cfg)
