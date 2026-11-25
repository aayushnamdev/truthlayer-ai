"""Shared helpers. All fixtures live in tests/fixtures and are SYNTHETIC."""
from pathlib import Path
import pytest
from truthlayer.config import Config

FX = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.fixture
def cfg(tmp_path):
    c = Config.fixtures(FX, tmp_path / "out")
    c.root = FX.parent.parent
    return c


@pytest.fixture
def analysis(cfg):
    from truthlayer.drift import analyse
    return analyse(cfg)
