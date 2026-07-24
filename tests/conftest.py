import os
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-key")

from app.main import app  # noqa: E402


@pytest.fixture
def mock_baileys_auth():
    """Mock Baileys API key for testing"""
    return "test-api-key-12345"


@pytest_asyncio.fixture()
async def test_app(monkeypatch, mock_baileys_auth):
    monkeypatch.setenv("BAILEYS_API_KEY", mock_baileys_auth)

    from app.core import config
    import importlib
    importlib.reload(config)

    # Mock Supabase client to return in-memory data
    fake_client = MagicMock()

    # Seed OBD codes as Supabase-style responses
    obd_codes = {
        "P0705": {
            "code": "P0705",
            "description": "Transmission range sensor circuit malfunction",
            "symptoms": None,
            "common_causes": ["Faulty range sensor", "Misadjusted neutral safety switch", "Wiring damage near gearbox"],
            "generic_fixes": ["Inspect range sensor", "Check wiring continuity", "Verify gear selector alignment"],
            "system": "Transmission",
            "severity": "Moderate",
        },
        "P0401": {
            "code": "P0401",
            "description": "Insufficient exhaust gas recirculation flow",
            "symptoms": None,
            "common_causes": ["Clogged EGR valve", "Blocked EGR passages", "Faulty EGR sensor"],
            "generic_fixes": ["Clean EGR valve", "Inspect vacuum supply", "Check EGR position sensor"],
            "system": "Emissions",
            "severity": "Moderate",
        },
        "P0301": {
            "code": "P0301",
            "description": "Cylinder 1 misfire detected",
            "symptoms": None,
            "common_causes": ["Ignition coil failure", "Spark plug failure", "Injector malfunction", "Vacuum leak"],
            "generic_fixes": ["Swap ignition coil", "Inspect spark plug", "Check injector pulse"],
            "system": "Ignition",
            "severity": "High",
        },
    }

    def mock_table(name):
        table = MagicMock()
        select = MagicMock()
        table.select.return_value = select

        def mock_eq(field, value):
            eq_result = MagicMock()
            if name == "obd_codes" and field == "code" and value in obd_codes:
                eq_result.execute.return_value = MagicMock(data=[obd_codes[value]])
            else:
                eq_result.execute.return_value = MagicMock(data=[])
            eq_result.eq = mock_eq
            return eq_result

        select.eq = mock_eq
        table.upsert.return_value = MagicMock(execute=MagicMock(return_value=MagicMock(data=[])))
        return table

    fake_client.table = mock_table

    with patch("app.db.client.get_supabase_client", return_value=fake_client):
        yield app
