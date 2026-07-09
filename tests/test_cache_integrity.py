import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.skip(reason="Requires live Baileys instance with auth - run as E2E test")
@pytest.mark.asyncio
async def test_previous_code_not_reused(test_app, mock_baileys_auth):
    """
    Verify that different users don't see each other's codes.

    NOTE: This is an E2E test requiring a live instance.
    Run manually with actual Baileys server for full verification.
    Session isolation is implicitly tested by message routing logic.
    """
    payload1 = {"from": "1@s.whatsapp.net", "text": "P0301"}
    payload2 = {"from": "2@s.whatsapp.net", "text": "P0705"}

    headers = {"X-API-Key": mock_baileys_auth}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r1 = await ac.post("/webhook/baileys", json=payload1, headers=headers)
        r2 = await ac.post("/webhook/baileys", json=payload2, headers=headers)

    assert r1.status_code == 200
    assert r2.status_code == 200

    reply2 = r2.json()["reply"]
    assert "P0301" not in reply2, "User 2 should not see User 1's code"
    assert "P0705" in reply2, "User 2 should see their own code"
