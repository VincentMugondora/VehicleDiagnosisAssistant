"""Test follow-up message flow"""
import asyncio
import sys
sys.path.insert(0, ".")

from app.services.message_router import MessageRouter
from app.services.obd_service import OBDService
from app.repositories.obd_repository import OBDRepository
from app.db.client import get_supabase_client
from app.models.session import SessionState


async def test_followup():
    print("\n" + "="*70)
    print("FOLLOW-UP MESSAGE FLOW TEST")
    print("="*70)

    client = get_supabase_client()
    obd_repo = OBDRepository(client)
    obd_service = OBDService(obd_repo, ai_client=None, auto_learn=False)
    message_router = MessageRouter(obd_service)

    # Create session
    from datetime import datetime
    session = SessionState(
        phone_hash="test_hash",
        last_active=datetime.utcnow()
    )

    # Step 1: Send P0420
    print("\n[Step 1] User sends: P0420")
    result1 = await message_router.route_message(
        raw_text="P0420",
        phone_hash="test_hash",
        request_id="test_1",
        session=session
    )

    if hasattr(result1, 'code'):
        print(f"[OK] Got diagnostic for {result1.code}")
        print(f"     Description: {result1.description[:60]}...")
        print(f"     Last diagnosis stored: {session.last_diagnosis is not None}")
        if session.last_diagnosis:
            print(f"     Stored code: {session.last_diagnosis.code}")
    else:
        print(f"[X] Unexpected result: {result1}")
        return

    # Step 2: Check AI client
    print(f"\n[Step 2] Check AI client")
    print(f"     AI client exists: {message_router.ai_client is not None}")
    if message_router.ai_client:
        print(f"     AI provider: {message_router.ai_client.provider}")

    # Step 3: Send follow-up
    test_phrases = [
        "explain further",
        "I don't understand",
        "why is that",
        "what should I do"
    ]

    for phrase in test_phrases:
        print(f"\n[Step 3] User sends: '{phrase}'")
        print(f"     Session has last_diagnosis: {session.last_diagnosis is not None}")
        print(f"     AI client available: {message_router.ai_client is not None}")

        # Check the condition
        will_route_to_followup = (
            session and
            session.last_diagnosis and
            message_router.ai_client
        )
        print(f"     Will route to follow-up: {will_route_to_followup}")

        try:
            result2 = await message_router.route_message(
                raw_text=phrase,
                phone_hash="test_hash",
                request_id="test_2",
                session=session
            )

            if isinstance(result2, dict):
                if result2.get("type") == "followup_response":
                    print(f"[OK] Got follow-up response:")
                    print(f"     {result2['reply'][:100]}...")
                elif "error" in result2:
                    print(f"[X] Got error response: {result2['error']}")
                else:
                    print(f"[X] Got unexpected dict: {result2}")
            else:
                print(f"[X] Got unexpected result type: {type(result2)}")
                print(f"     {result2}")

        except Exception as e:
            print(f"[X] Exception: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_followup())
