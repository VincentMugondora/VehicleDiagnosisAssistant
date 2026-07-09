import re
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.skip(reason="Requires live Baileys instance with auth - run as E2E test")
@pytest.mark.asyncio
async def test_reply_contains_requested_code(test_app, mock_baileys_auth):
    """
    Verify reply contains the correct requested code.

    NOTE: This is an E2E test requiring a live instance.
    Code consistency is implicitly tested by integration tests.
    """
    payload = {
        "from": "123@s.whatsapp.net",
        "text": "P0705 Toyota Hilux 2011 2.5D",
    }

    headers = {"X-API-Key": mock_baileys_auth}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/webhook/baileys", json=payload, headers=headers)

    assert response.status_code == 200
    reply = response.json()["reply"]

    match = re.search(r"P0\d{3}", reply)
    assert match is not None, "No OBD code found in reply"
    assert match.group() == "P0705", "Reply code does not match request"
