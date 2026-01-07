import pytest
from httpx import AsyncClient, ASGITransport

FORBIDDEN_PHRASES = [
    "i bought",
    "yesterday",
    "my car",
    "someone said",
    "it came up with",
]


@pytest.mark.asyncio
async def test_no_forum_language(test_app):
    payload = {
        "from": "123@s.whatsapp.net",
        "text": "P0401",
    }

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/webhook/baileys", json=payload)

    assert response.status_code == 200
    reply = response.json()["reply"].lower()

    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in reply, f"Forum text leaked: {phrase}"
