"""
Test script for Paynow payment integration.

Run this after setting up Paynow credentials to verify everything works.
"""
import asyncio
import sys
sys.path.insert(0, ".")

from app.db.client import get_supabase_client
from app.repositories.payment_repository import PaymentRepository
from app.services.payment_service import PaymentService
from app.utils.phone import hash_phone_number
from app.core.config import settings


def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)


async def main():
    print("\n" + "="*70)
    print(" PAYNOW PAYMENT INTEGRATION TEST")
    print("="*70)

    # 1. Check configuration
    print_section("1. Configuration Check")

    if not settings.paynow_integration_id:
        print("[X] PAYNOW_INTEGRATION_ID not configured")
        print("    Add to .env: PAYNOW_INTEGRATION_ID=your-id")
        return 1

    if not settings.paynow_integration_key:
        print("[X] PAYNOW_INTEGRATION_KEY not configured")
        print("    Add to .env: PAYNOW_INTEGRATION_KEY=your-key")
        return 1

    print(f"[OK] PAYNOW_INTEGRATION_ID: {settings.paynow_integration_id}")
    print(f"[OK] PAYNOW_INTEGRATION_KEY: {'*' * 20}... (hidden)")
    print(f"[OK] PAYNOW_RESULT_URL: {settings.paynow_result_url}")
    print(f"[OK] SUBSCRIPTION_PRICE: ${settings.subscription_price}")
    print(f"[OK] FREE_DIAGNOSTICS_LIMIT: {settings.free_diagnostics_limit}")

    # 2. Check database connection
    print_section("2. Database Connection")

    client = get_supabase_client()
    if not client:
        print("[X] Supabase client not initialized")
        print("    Check SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
        return 1

    print("[OK] Supabase client initialized")

    # 3. Check database tables
    print_section("3. Database Tables")

    try:
        # Check transactions table
        result = client.table("transactions").select("*").limit(1).execute()
        print("[OK] transactions table exists")

        # Check subscriptions table
        result = client.table("subscriptions").select("*").limit(1).execute()
        print("[OK] subscriptions table exists")

        # Check user_usage table
        result = client.table("user_usage").select("*").limit(1).execute()
        print("[OK] user_usage table exists")

    except Exception as e:
        print(f"[X] Database table error: {e}")
        print("    Run migration: migrations/add_payments_tables.sql")
        return 1

    # 4. Test payment repository
    print_section("4. Payment Repository")

    try:
        payment_repo = PaymentRepository(client)
        print("[OK] PaymentRepository initialized")

        # Test access check
        test_phone_hash = hash_phone_number("whatsapp:+263771234567")
        access_info = payment_repo.check_access(test_phone_hash, free_limit=5)
        print(f"[OK] Access check works: {access_info['reason']}")
        print(f"    - Can access: {access_info['can_access']}")
        print(f"    - Diagnostics used: {access_info['diagnostics_used']}")
        print(f"    - Diagnostics remaining: {access_info['diagnostics_remaining']}")

    except Exception as e:
        print(f"[X] PaymentRepository error: {e}")
        return 1

    # 5. Test payment service
    print_section("5. Payment Service")

    try:
        payment_service = PaymentService(payment_repo)

        if not payment_service.paynow:
            print("[X] Paynow client not initialized")
            print("    Check PAYNOW_INTEGRATION_ID and PAYNOW_INTEGRATION_KEY")
            return 1

        print("[OK] PaymentService initialized")
        print("[OK] Paynow client ready")

    except Exception as e:
        print(f"[X] PaymentService error: {e}")
        return 1

    # 6. Test payment initiation (DRY RUN - won't charge)
    print_section("6. Payment Initiation Test (Dry Run)")

    print("\n[!] This would initiate a real payment if you proceed.")
    print("[!] To test for real, uncomment the code below and use a test EcoCash number.")
    print("[!] For now, skipping to avoid accidental charges.\n")

    # Uncomment to test real payment initiation:
    # test_phone = "0771234567"  # Replace with test number
    # test_email = "test@example.com"
    #
    # print(f"Initiating payment for: {test_email}, {test_phone}")
    # result = await payment_service.initiate_subscription_payment(
    #     user_phone=test_phone,
    #     user_email=test_email,
    #     subscription_type="monthly"
    # )
    #
    # if result["success"]:
    #     print(f"[OK] Payment initiated!")
    #     print(f"    Order reference: {result['order_reference']}")
    #     print(f"    Poll URL: {result['poll_url']}")
    #     print(f"    Instructions: {result['instructions']}")
    # else:
    #     print(f"[X] Payment initiation failed: {result.get('error')}")

    # 7. Summary
    print_section("7. Summary")

    print("\n[OK] All basic checks passed!")
    print("\nNext steps:")
    print("  1. Start backend: uvicorn app.main:app --reload")
    print("  2. Test endpoint: curl http://localhost:8000/payments/test")
    print("  3. Test with real EcoCash number (uncomment section 6)")
    print("  4. Configure webhook URL in Paynow dashboard")
    print("  5. Monitor logs: grep 'paynow' app.log")

    print("\nWhatsApp commands users can send:")
    print("  - SUBSCRIBE john@example.com 0771234567")
    print("  - STATUS")

    print("\nAPI endpoints:")
    print("  - POST /payments/initiate")
    print("  - GET  /payments/status/{order_reference}")
    print("  - GET  /payments/access-check/{phone}")
    print("  - POST /webhook/paynow")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
