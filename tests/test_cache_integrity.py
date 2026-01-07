import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_previous_code_not_reused(test_app):
    payload1 = {"from": "1@s.whatsapp.net", "text": "P0301"}
    payload2 = {"from": "2@s.whatsapp.net", "text": "P0705"}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r1 = await ac.post("/webhook/baileys", json=payload1)
        r2 = await ac.post("/webhook/baileys", json=payload2)

    assert r1.status_code == 200
    assert r2.status_code == 200

    reply2 = r2.json()["reply"]
    assert "P0301" not in reply2
    assert "P0705" in reply2
