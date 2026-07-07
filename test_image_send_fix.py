#!/usr/bin/env python3
"""
Quick test to verify image send fix
"""
import asyncio
import sys
from datetime import datetime

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from app.services.image_sender import ImageSender
from app.models.system_diagram import SystemDiagram
from app.core.config import settings

async def test_image_send():
    """Test image send with mock diagram"""

    print("=" * 70)
    print("IMAGE SEND FIX VERIFICATION")
    print("=" * 70)

    # Check configuration
    print("\n[1] Configuration Check")
    print(f"  Baileys URL: {settings.baileys_outbound_url}")
    print(f"  Baileys API Key: {'SET' if settings.baileys_api_key else 'NOT SET'}")

    if not settings.baileys_outbound_url:
        print("\n[ERROR] BAILEYS_OUTBOUND_URL not configured!")
        print("   Set in .env: BAILEYS_OUTBOUND_URL=http://localhost:3000/send-image")
        return

    # Create test diagram
    print("\n[2] Creating Test Diagram")
    diagram = SystemDiagram(
        id="test-123",
        system="catalytic converter",
        image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/6/64/Catalytic_converter.jpg/320px-Catalytic_converter.jpg",
        source="Wikimedia Commons",
        license="CC BY-SA 4.0",
        attribution_text="Catalytic converter diagram (Wikimedia Commons)",
        caption="Catalytic Converter",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    print(f"  System: {diagram.system}")
    print(f"  Image URL: {diagram.image_url[:60]}...")

    # Test import (this was failing before)
    print("\n[3] Testing HTTP Client Import")
    try:
        from app.core.http_clients import get_baileys_client
        print("  [OK] get_baileys_client() imported successfully")
        client = get_baileys_client()
        print(f"  [OK] Client created: {type(client).__name__}")
    except Exception as e:
        print(f"  [ERROR] Import failed: {e}")
        return

    # Test image sender
    print("\n[4] Testing ImageSender Initialization")
    try:
        sender = ImageSender(
            baileys_webhook_url=settings.baileys_outbound_url,
            timeout=10.0
        )
        print("  [OK] ImageSender created successfully")
    except Exception as e:
        print(f"  [ERROR] ImageSender creation failed: {e}")
        return

    # Test actual send (will fail if Baileys server not running, but won't crash)
    print("\n[5] Testing Actual Image Send")
    print("  [WARNING] This will fail if Baileys server is not running")
    print("  [WARNING] But the code should handle it gracefully")

    try:
        result = await sender.send_system_diagram(
            to_number="263771234567",  # Test number
            diagram=diagram
        )

        if result:
            print("  [OK] Image sent successfully!")
            print("       (Baileys server accepted the request)")
        else:
            print("  [WARNING] Image send returned False")
            print("            (Expected if Baileys server not running)")
            print("            (Check logs for details)")

    except Exception as e:
        print(f"  [ERROR] Unexpected exception: {e}")
        print(f"          Error type: {type(e).__name__}")
        import traceback
        print(f"          Traceback:\n{traceback.format_exc()}")
        return

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\n[SUCCESS] THE FIX IS WORKING!")
    print("   - No AttributeError on import")
    print("   - ImageSender initialized correctly")
    print("   - HTTP client created successfully")
    print("\nNext Steps:")
    print("   1. Ensure Baileys server is running on port 3000")
    print("   2. Test with real WhatsApp message: send 'P0420'")
    print("   3. Check logs for 'system_diagram_sent'")
    print("   4. Verify image received in WhatsApp")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_image_send())
