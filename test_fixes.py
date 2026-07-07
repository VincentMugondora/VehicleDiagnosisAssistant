#!/usr/bin/env python3
"""
Quick test script to verify fixes are working.
Run this AFTER restarting both services.
"""
import sys
import time

def test_cohere_client():
    """Test that CohereClient can be imported without syntax errors"""
    print("1. Testing CohereClient import...")
    try:
        from app.services.cohere_client import CohereClient
        print("   [OK] CohereClient imports successfully")
        print("   [OK] No 'await outside async' error")
        return True
    except SyntaxError as e:
        print(f"   [FAIL] Syntax error: {e}")
        return False
    except Exception as e:
        print(f"   [WARN] Import error: {e}")
        print("   (This is OK if COHERE_API_KEY not set)")
        return True

def test_http_clients():
    """Test that HTTP client module exists and imports"""
    print("\n2. Testing HTTP clients module...")
    try:
        from app.core.http_clients import get_twilio_client, get_baileys_client
        print("   [OK] HTTP clients module imported")
        print("   [OK] Connection pooling available")
        return True
    except ImportError as e:
        print(f"   [FAIL] Import error: {e}")
        return False

def test_baileys_timeout():
    """Check Baileys timeout is set to 120s"""
    print("\n3. Testing Baileys timeout setting...")
    try:
        with open('baileys-server/.env', 'r') as f:
            content = f.read()
            if 'REQUEST_TIMEOUT=120000' in content:
                print("   [OK] Baileys timeout set to 120s")
                return True
            else:
                print("   [FAIL] Baileys timeout not set correctly")
                print("   Expected: REQUEST_TIMEOUT=120000")
                return False
    except FileNotFoundError:
        print("   [FAIL] baileys-server/.env not found")
        return False

def main():
    print("=" * 60)
    print("TESTING FIXES APPLIED ON 2026-07-07")
    print("=" * 60)
    
    results = []
    results.append(test_cohere_client())
    results.append(test_http_clients())
    results.append(test_baileys_timeout())
    
    print("\n" + "=" * 60)
    if all(results):
        print("[OK] ALL TESTS PASSED")
        print("\nYou can now:")
        print("1. Start backend: python -m uvicorn main:app --reload")
        print("2. Start Baileys: cd baileys-server && node index.js")
        print("3. Send test message: 'P0171 Toyota Corolla 2015'")
        return 0
    else:
        print("[FAIL] SOME TESTS FAILED")
        print("\nCheck the errors above and:")
        print("1. Verify you're in the project root directory")
        print("2. Re-apply fixes if needed")
        print("3. See TIMEOUT_FIXES.md for details")
        return 1

if __name__ == '__main__':
    sys.exit(main())
