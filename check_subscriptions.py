"""Check subscriptions and user usage"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.client import get_supabase_client

client = get_supabase_client()

# Get all active subscriptions
print("=" * 80)
print("ACTIVE SUBSCRIPTIONS")
print("=" * 80)
result = client.table('subscriptions').select('*').eq('is_active', True).execute()
for sub in result.data:
    print(f"Phone Hash: {sub['phone_hash'][:20]}...")
    print(f"  Type: {sub['subscription_type']}")
    print(f"  Amount: ${sub['amount']} {sub['currency']}")
    print(f"  Start: {sub['start_date']}")
    print(f"  End: {sub['end_date']}")
    print(f"  Auto-renew: {sub['auto_renew']}")
    print()

# Get user usage
print("=" * 80)
print("USER USAGE (Free Tier)")
print("=" * 80)
result = client.table('user_usage').select('*').order('created_at', desc=True).limit(5).execute()
for usage in result.data:
    print(f"Phone Hash: {usage['phone_hash'][:20]}...")
    print(f"  Diagnostics: {usage['diagnostics_count']}")
    print(f"  Period: {usage['period_start']} to {usage['period_end']}")
    print()
