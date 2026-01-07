import os
import asyncio
import types
import pytest
from typing import Any, Dict

# Ensure DB init is skipped in tests
os.environ.setdefault("SKIP_INIT_DB", "true")

from app.main import app  # noqa: E402
from app.db.mongo import get_db  # noqa: E402


class AsyncFakeCollection:
    def __init__(self, backing: list):
        self._backing = backing

    async def find_one(self, query: Dict[str, Any]):
        for doc in reversed(self._backing):
            ok = True
            for k, v in query.items():
                if doc.get(k) != v:
                    ok = False
                    break
            if ok:
                return dict(doc)
        return None

    async def insert_one(self, doc: Dict[str, Any]):
        self._backing.append(dict(doc))
        return types.SimpleNamespace(inserted_id=len(self._backing))

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        # Minimal support for tests; not needed currently
        if "$set" in update:
            setvals = update["$set"]
        else:
            setvals = update
        for idx, doc in enumerate(self._backing):
            if all(doc.get(k) == v for k, v in query.items()):
                new_doc = dict(doc)
                new_doc.update(setvals)
                self._backing[idx] = new_doc
                return types.SimpleNamespace(matched_count=1, modified_count=1)
        if upsert:
            new_doc = dict(query)
            new_doc.update(setvals)
            self._backing.append(new_doc)
            return types.SimpleNamespace(upserted_id=len(self._backing))
        return types.SimpleNamespace(matched_count=0, modified_count=0)

    async def count_documents(self, query: Dict[str, Any]):
        cnt = 0
        for doc in self._backing:
            if all((k in doc and (not isinstance(v, dict) or "$gte" not in v or doc[k] >= v["$gte"])) if k in doc else False for k, v in query.items()):
                cnt += 1
        return cnt

    async def create_index(self, *args, **kwargs):
        return "ok"


class AsyncFakeDB:
    def __init__(self):
        self._stores = {
            "obd_codes": [],
            "vehicle_overrides": [],
            "message_logs": [],
            "diagnostic_logs": [],
        }

    def __getitem__(self, name: str) -> AsyncFakeCollection:
        if name not in self._stores:
            self._stores[name] = []
        return AsyncFakeCollection(self._stores[name])


@pytest.fixture()
async def test_app(monkeypatch):
    fake_db = AsyncFakeDB()

    # Seed essential codes used in tests
    await fake_db["obd_codes"].insert_one({
        "code": "P0705",
        "description": "Transmission range sensor circuit malfunction",
        "symptoms": "",
        "common_causes": "Faulty range sensor, Misadjusted neutral safety switch, Wiring damage near gearbox",
        "generic_fixes": "Inspect range sensor, Check wiring continuity, Verify gear selector alignment",
    })
    await fake_db["obd_codes"].insert_one({
        "code": "P0401",
        "description": "Insufficient exhaust gas recirculation flow",
        "symptoms": "",
        "common_causes": "Clogged EGR valve, Blocked EGR passages, Faulty EGR sensor",
        "generic_fixes": "Clean EGR valve, Inspect vacuum supply, Check EGR position sensor",
    })
    await fake_db["obd_codes"].insert_one({
        "code": "P0301",
        "description": "Cylinder 1 misfire detected",
        "symptoms": "",
        "common_causes": "Ignition coil failure, Spark plug failure, Injector malfunction, Vacuum leak",
        "generic_fixes": "Swap ignition coil, Inspect spark plug, Check injector pulse",
    })

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield app
    finally:
        app.dependency_overrides.clear()
