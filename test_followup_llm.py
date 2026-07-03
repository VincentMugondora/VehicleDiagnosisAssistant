#!/usr/bin/env python3
"""
Test LLM follow-up conversations after enabling AI_ENRICH_ENABLED.

Run this AFTER updating .env and restarting the server.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.db.client import get_supabase_client
from app.repositories.obd_repository import OBDRepository
from app.repositories.session_repository import SessionRepository
from app.services.obd_service import OBDService
from app.services.message_router import MessageRouter
from app.services.session_manager import SessionManager
from app.models.session import SessionState, LastDiagnosis
from app.core.config import settings


async def test_followup_conversation():
    """Simulate a full conversation with follow-up."""
    print('='*80)
    print('LLM FOLLOW-UP CONVERSATION TEST')
    print('='*80)

    # Check if AI is enabled
    print(f'\n[CONFIG CHECK]')
    print(f'  AI_ENRICH_ENABLED: {settings.ai_enrich_enabled}')
    print(f'  AI_PROVIDER: {settings.ai_provider}')
    print(f'  COHERE_MODEL: {settings.cohere_model}')

    if not settings.ai_enrich_enabled:
        print('\n[ERROR] AI_ENRICH_ENABLED=false')
        print('Follow-up conversations will NOT work.')
        print()
        print('FIX: Update .env:')
        print('  AI_ENRICH_ENABLED=true')
        print('  COHERE_MODEL=command-r-plus')
        print()
        print('Then restart server: .\\start_backend.bat')
        return

    # Initialize services
    client = get_supabase_client()
    repo = OBDRepository(client)
    session_repo = SessionRepository(client)
    obd_service = OBDService(repo, auto_learn=False)
    router = MessageRouter(obd_service)

    # Create test session with last diagnosis
    phone_hash = "test_followup_hash"
    request_id = "test_123"

    # Create session with diagnosis context
    session = SessionState(
        phone_hash=phone_hash,
        state={},
        created_at=datetime.utcnow(),
        last_active=datetime.utcnow()
    )

    print('\n[STEP 1] Initial diagnosis request')
    print('  User: "P0507"')

    # First message: Get diagnosis
    result1 = await router.route_message(
        raw_text="P0507",
        phone_hash=phone_hash,
        request_id=request_id,
        session=session
    )

    if hasattr(result1, 'code'):
        print(f'  Bot: [Diagnosis for {result1.code}]')
        print(f'    Description: {result1.description[:60]}...')
        print(f'    Has causes: {len(result1.causes) > 0}')
        print(f'    Has checks: {len(result1.checks) > 0}')

        # Verify session stored diagnosis
        if session.last_diagnosis:
            print(f'\n  [Session] Stored last_diagnosis:')
            print(f'    Code: {session.last_diagnosis.code}')
            print(f'    Description: {session.last_diagnosis.description[:60]}...')
    else:
        print(f'  [ERROR] First message failed: {result1}')
        return

    print('\n[STEP 2] Follow-up question')
    print('  User: "I don\'t understand"')

    # Second message: Follow-up question
    result2 = await router.route_message(
        raw_text="I don't understand",
        phone_hash=phone_hash,
        request_id=request_id,
        session=session
    )

    print(f'\n  Result type: {type(result2).__name__}')

    if isinstance(result2, dict):
        if "reply" in result2:
            print(f'\n  [SUCCESS] LLM Response:')
            print(f'  {"-"*76}')
            # Format the response nicely
            reply = result2["reply"]
            for line in reply.split('\n'):
                print(f'  {line}')
            print(f'  {"-"*76}')
        elif "error" in result2:
            print(f'\n  [FAIL] Got error message instead of LLM response:')
            print(f'    {result2["error"]}')
            print(f'\n  This means:')
            print(f'    - AI client not initialized (check AI_ENRICH_ENABLED)')
            print(f'    - Or session.last_diagnosis not set')
            print(f'    - Or AI provider error')
    else:
        print(f'\n  [UNEXPECTED] Result is not a dict: {result2}')

    print('\n' + '='*80)
    print('TEST COMPLETE')
    print('='*80)


async def main():
    """Run the test."""
    try:
        await test_followup_conversation()
    except Exception as e:
        print(f'\n[EXCEPTION] {type(e).__name__}: {str(e)}')
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
