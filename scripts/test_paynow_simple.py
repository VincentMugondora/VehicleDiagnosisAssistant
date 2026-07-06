"""
Simple Paynow Test - Direct SDK Test
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from paynow import Paynow
from app.core.config import settings

print("=" * 70)
print("PAYNOW SDK TEST")
print("=" * 70)

# Get credentials
integration_id = getattr(settings, 'paynow_integration_id', None)
integration_key = getattr(settings, 'paynow_integration_key', None)
return_url = getattr(settings, 'paynow_return_url', 'http://localhost:8000/return')
result_url = getattr(settings, 'paynow_result_url', 'http://localhost:8000/callback')

print(f"\nIntegration ID: {integration_id}")
print(f"Integration Key: {integration_key[:20]}...")
print(f"Return URL: {return_url}")
print(f"Result URL: {result_url}")

# Initialize Paynow
print("\n[1] Initializing Paynow client...")
paynow = Paynow(
    integration_id=integration_id,
    integration_key=integration_key,
    return_url=return_url,
    result_url=result_url
)
print("[OK] Paynow client initialized")

# Create payment
print("\n[2] Creating payment...")
payment = paynow.create_payment(
    reference="TEST-" + str(int(datetime.now().timestamp())),
    auth_email="nopausegroupofcompanies@gmail.com"  # Your registered email
)
print("[OK] Payment object created")

# Add item
print("\n[3] Adding item...")
payment.add("Test Subscription - Monthly", 1.00)
print("[OK] Item added: $1.00")

# Send mobile payment
print("\n[4] Sending mobile payment...")
print("    Using Paynow test case number for test mode")
try:
    # Paynow test mode requires specific test numbers
    # Test numbers: 0771111111, 0772222222, 0773333333
    response = paynow.send_mobile(
        payment=payment,
        phone="0771111111",  # Paynow test case number (always succeeds)
        method="ecocash"
    )

    print(f"\n[5] Response received:")
    print(f"    Success: {response.success}")

    if response.success:
        print(f"    Redirect URL: {response.redirect_url}")
        print(f"    Poll URL: {response.poll_url}")
        print(f"    Hash: {response.hash if hasattr(response, 'hash') else 'N/A'}")

        print("\n" + "=" * 70)
        print("SUCCESS! Paynow integration working!")
        print("=" * 70)
        print(f"\nPayment URL: {response.redirect_url}")
        print("\nNext steps:")
        print("  1. Visit the URL above")
        print("  2. Complete payment with EcoCash")
        print("  3. Check status with poll_url")
        print("=" * 70)
    else:
        print(f"    Error: {response.error if hasattr(response, 'error') else 'Unknown error'}")
        print(f"    Status: {response.status if hasattr(response, 'status') else 'N/A'}")
        print(f"    Data: {response.data if hasattr(response, 'data') else 'N/A'}")
        print(f"\n[ERROR] Payment failed")

        # Check all response details
        print("\n    Full response details:")
        for attr in ['error', 'status', 'data', 'instructions', 'poll_url', 'redirect_url']:
            if hasattr(response, attr):
                val = getattr(response, attr)
                print(f"      {attr}: {val}")

except Exception as e:
    print(f"\n[ERROR] Exception: {e}")
    import traceback
    traceback.print_exc()

from datetime import datetime
