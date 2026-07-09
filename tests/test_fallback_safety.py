import pytest
from httpx import AsyncClient, ASGITransport

FORBIDDEN_PHRASES = [
    "i bought",
    "yesterday",
    "my car",
    "someone said",
    "it came up with",
]


@pytest.mark.skip(reason="Requires live Baileys instance with auth - run as E2E test")
@pytest.mark.asyncio
async def test_no_forum_language(test_app, mock_baileys_auth):
    """
    Verify responses don't contain informal forum-style language.

    NOTE: This is an E2E test requiring a live instance.
    Response quality is validated through formatter tests.
    """
    payload = {
        "from": "123@s.whatsapp.net",
        "text": "P0401",
    }

    headers = {"X-API-Key": mock_baileys_auth}

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/webhook/baileys", json=payload, headers=headers)

    assert response.status_code == 200
    reply = response.json()["reply"].lower()

    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in reply, f"Forum text leaked: {phrase}"
