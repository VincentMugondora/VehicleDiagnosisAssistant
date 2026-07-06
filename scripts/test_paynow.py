"""
Test Paynow Integration
Verifies credentials and creates a test payment
"""
import sys
import asyncio
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.services.payment_service import PaymentService
from app.db.client import get_supabase_client

async def main():
    print("=" * 70)
    print("PAYNOW INTEGRATION TEST")
    print("=" * 70)

    # Check credentials configured
    print("\n[1/4] Checking Paynow credentials...")

    integration_id = getattr(settings, 'paynow_integration_id', None)
    integration_key = getattr(settings, 'paynow_integration_key', None)

    if not integration_id or not integration_key:
        print("    [ERROR] Paynow credentials not configured!")
        print("\n    Add to .env:")
        print("    PAYNOW_INTEGRATION_ID=25487")
        print("    PAYNOW_INTEGRATION_KEY=f33ab311-0cdb-4302-a9a9-d2257170acdd")
        return 1

    print(f"    Integration ID: {integration_id}")
    print(f"    Integration Key: {integration_key[:20]}...")
    print("    [OK] Credentials configured")

    # Initialize payment service
    print("\n[2/4] Initializing PaymentService...")
    try:
        client = get_supabase_client()
        payment_service = PaymentService(client)
        print("    [OK] PaymentService initialized")
    except Exception as e:
        print(f"    [ERROR] Failed to initialize: {e}")
        return 1

    # Create test payment
    print("\n[3/4] Creating test payment...")

    # Test data
    test_phone = "0771234567"  # Zimbabwe format
    test_email = "test@example.com"

    try:
        result = await payment_service.initiate_subscription_payment(
            user_phone=test_phone,
            user_email=test_email,
            subscription_type="monthly"
        )

        if result.get('success'):
            print("    [OK] Payment initiated successfully!")
            print(f"\n    Order Reference: {result.get('order_reference')}")
            print(f"    Paynow Reference: {result.get('paynow_reference', 'N/A')}")
            print(f"    Status: {result.get('status')}")

            if result.get('redirect_url'):
                print(f"\n    Payment URL: {result.get('redirect_url')}")
                print("\n    User would be redirected to this URL to complete payment")

            if result.get('poll_url'):
                print(f"\n    Poll URL: {result.get('poll_url')}")
                print("    Use this to check payment status")

        else:
            print(f"    [ERROR] Payment initiation failed")
            print(f"    Error: {result.get('error')}")
            return 1

    except Exception as e:
        print(f"    [ERROR] Exception during payment: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Check database
    print("\n[4/4] Checking database record...")
    try:
        order_ref = result.get('order_reference')
        db_result = client.table('transactions').select('*').eq('order_reference', order_ref).execute()

        if db_result.data:
            record = db_result.data[0]
            print("    [OK] Transaction recorded in database")
            print(f"    ID: {record['id']}")
            print(f"    Status: {record['status']}")
            print(f"    Amount: ${record['amount']} {record['currency']}")
        else:
            print("    [WARN] No database record found")

    except Exception as e:
        print(f"    [ERROR] Database check failed: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. If test passed: Try via WhatsApp with '/subscribe'")
    print("  2. Complete test payment using EcoCash")
    print("  3. Monitor transaction status with poll URL")
    print("\nPaynow Test Mode:")
    print("  - Use test EcoCash numbers if available")
    print("  - Or use real number for $1 test (refundable)")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
