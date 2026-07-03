#!/usr/bin/env python3
"""
Quick script to check Supabase project status
"""

import sys
import requests

PROJECT_ID = "ojxijkrkadymllbigcme"
URL = f"https://{PROJECT_ID}.supabase.co"

print("=" * 60)
print("🔍 Checking Supabase Project Status")
print("=" * 60)
print()
print(f"Project ID: {PROJECT_ID}")
print(f"URL: {URL}")
print()
print("Testing connection...")
print()

try:
    # Try to connect with a short timeout
    response = requests.get(URL, timeout=5)
    print(f"✅ Project exists and is reachable!")
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.text[:100]}...")
except requests.exceptions.ConnectionError:
    print(f"❌ Cannot connect to {URL}")
    print()
    print("Possible reasons:")
    print("  1. Project was deleted or paused")
    print("  2. Project URL changed")
    print("  3. Network/DNS issue")
    print()
    print("SOLUTION:")
    print("  1. Go to: https://supabase.com/dashboard")
    print("  2. Check if project exists")
    print("  3. If not, create a NEW project")
    print("  4. Copy the NEW project URL")
    print("  5. Update .env file with new credentials")
except requests.exceptions.Timeout:
    print(f"⚠️  Connection timeout - project may be slow or paused")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 60)
print("Next Steps:")
print("=" * 60)
print()
print("1. Open: https://supabase.com/dashboard")
print("2. Login to your account")
print("3. Look for your projects")
print()
print("If you don't see any projects or they're all paused:")
print()
print("CREATE NEW PROJECT:")
print("  • Click 'New Project'")
print("  • Name: vehicle-diagnosis")
print("  • Database Password: (generate secure one)")
print("  • Region: (closest to you)")
print("  • Click 'Create new project'")
print("  • Wait 2-3 minutes")
print()
print("Then get credentials:")
print("  • Settings → API")
print("  • Copy Project URL")
print("  • Copy service_role key")
print("  • Update .env file")
print()
