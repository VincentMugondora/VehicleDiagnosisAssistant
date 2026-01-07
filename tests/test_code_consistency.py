import re
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_reply_contains_requested_code(test_app):
    payload = {
        "from": "123@s.whatsapp.net",
        "text": "P0705 Toyota Hilux 2011 2.5D",
    }

    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        response = await ac.post("/webhook/baileys", json=payload)

    assert response.status_code == 200
    reply = response.json()["reply"]

    match = re.search(r"P0\d{3}", reply)
    assert match is not None, "No OBD code found in reply"
    assert match.group() == "P0705", "Reply code does not match request"
