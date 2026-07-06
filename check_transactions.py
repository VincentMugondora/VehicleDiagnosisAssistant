"""Quick script to check transactions in database"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.client import get_supabase_client

client = get_supabase_client()

# Get all transactions
result = client.table('transactions').select('*').order('created_at', desc=True).limit(5).execute()

print("Recent Transactions:")
print("=" * 80)
for tx in result.data:
    print(f"Order: {tx['order_reference']}")
    print(f"  Phone Hash: {tx['phone_hash'][:20]}...")
    print(f"  Status: {tx['status']}")
    print(f"  Amount: ${tx['amount']} {tx['currency']}")
    print(f"  Phone: {tx['user_phone']}")
    print(f"  Created: {tx['created_at']}")
    print()
