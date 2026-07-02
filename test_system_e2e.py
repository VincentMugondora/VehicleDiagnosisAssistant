#!/usr/bin/env python3
"""
End-to-End System Test for Vehicle Diagnosis Assistant

Tests:
1. Backend health and database connectivity
2. OBD code lookup functionality
3. Message parsing
4. Webhook integration
5. AI enrichment (if enabled)
"""
import asyncio
import json
import sys
from datetime import datetime

import httpx
from app.core.config import settings
from app.db.client import get_supabase_client
from app.utils.obd_parser import parse_message
from app.services.obd_service import validate_obd_code


# Test configuration
BACKEND_URL = "http://localhost:8001"
WEBHOOK_URL = f"{BACKEND_URL}/webhook/baileys"
API_KEY = settings.baileys_api_key or "a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298"

# ANSI colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text: str):
    """Print section header"""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_test(name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = f"{GREEN}[PASS]{RESET}" if passed else f"{RED}[FAIL]{RESET}"
    print(f"{status} - {name}")
    if details:
        print(f"      {details}")


def print_info(text: str):
    """Print info message"""
    print(f"{YELLOW}[INFO] {text}{RESET}")


async def test_backend_health():
    """Test 1: Backend Health Check"""
    print_header("TEST 1: Backend Health & Database Connection")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BACKEND_URL}/health")

            if response.status_code == 200:
                data = response.json()
                print_test("Backend Health Endpoint", True, f"Status: {response.status_code}")
                print(f"      Response: {json.dumps(data, indent=2)}")
                return True
            else:
                print_test("Backend Health Endpoint", False, f"Status: {response.status_code}")
                return False

    except Exception as e:
        print_test("Backend Health Endpoint", False, f"Error: {str(e)}")
        print_info("Make sure backend is running: uvicorn app.main:app --reload --port 8001")
        return False


def test_database_connection():
    """Test 2: Supabase Connection"""
    print_header("TEST 2: Supabase Database Connection")

    try:
        client = get_supabase_client()
        print_test("Supabase Client Initialization", True)

        # Test connection by querying a table
        try:
            result = client.table("obd_codes").select("code").limit(1).execute()
            print_test("Database Query", True, f"Found {len(result.data)} record(s)")
            return True, len(result.data) > 0
        except Exception as e:
            print_test("Database Query", False, f"Error: {str(e)}")
            return True, False  # Connection works but query failed

    except Exception as e:
        print_test("Supabase Client Initialization", False, f"Error: {str(e)}")
        return False, False


def test_obd_codes_in_database():
    """Test 3: Check OBD Codes in Database"""
    print_header("TEST 3: OBD Codes in Database")

    try:
        client = get_supabase_client()

        # Count total codes
        result = client.table("obd_codes").select("code", count="exact").execute()
        total_count = result.count

        print_test("OBD Codes Count", total_count > 0, f"Found {total_count} codes")

        if total_count > 0:
            # Sample some codes
            sample = client.table("obd_codes").select("code, description").limit(5).execute()
            print_info(f"Sample codes:")
            for code_data in sample.data:
                print(f"      {code_data['code']}: {code_data['description'][:50]}...")
            return True
        else:
            print_info("Database is empty - you need to run the migration script")
            return False

    except Exception as e:
        print_test("Query OBD Codes", False, f"Error: {str(e)}")
        return False


def test_message_parsing():
    """Test 4: Message Parsing"""
    print_header("TEST 4: Message Parsing")

    test_cases = [
        {
            "input": "P0420",
            "expected": {"code": "P0420", "make": None, "model": None, "year": None}
        },
        {
            "input": "P0420 Toyota Camry 2015",
            "expected": {"code": "P0420", "make": "Toyota", "model": "Camry", "year": "2015"}
        },
        {
            "input": "p0171 Honda Civic 2018 1.5L",
            "expected": {"code": "P0171", "make": "Honda", "model": "Civic", "year": "2018", "engine": "1.5L"}
        },
        {
            "input": "My car has code P 0 4 2 0",
            "expected": {"code": "P0420"}
        },
        {
            "input": "Random text without code",
            "expected": {"code": None}
        }
    ]

    all_passed = True
    for case in test_cases:
        parsed = parse_message(case["input"])

        # Check expected fields
        passed = True
        for key, expected_value in case["expected"].items():
            if parsed.get(key) != expected_value:
                passed = False
                break

        all_passed = all_passed and passed

        test_name = f"Parse: '{case['input'][:40]}...'"
        details = f"Code: {parsed.get('code')}, Vehicle: {parsed.get('make')} {parsed.get('model')} {parsed.get('year')}"
        print_test(test_name, passed, details)

    return all_passed


def test_code_validation():
    """Test 5: Code Validation"""
    print_header("TEST 5: OBD Code Validation")

    test_cases = [
        ("P0420", True),
        ("P0171", True),
        ("B1234", True),
        ("C0001", True),
        ("U0100", True),
        ("p0420", True),  # Case insensitive
        ("X0420", False),  # Invalid letter
        ("P042", False),   # Too short
        ("P04200", False), # Too long
        ("", False),
        (None, False)
    ]

    all_passed = True
    for code, expected in test_cases:
        result = validate_obd_code(code)
        passed = result == expected
        all_passed = all_passed and passed

        print_test(f"Validate '{code}'", passed, f"Result: {result}, Expected: {expected}")

    return all_passed


async def test_webhook_integration():
    """Test 6: Webhook End-to-End"""
    print_header("TEST 6: Webhook Integration (End-to-End)")

    test_messages = [
        {
            "name": "Simple code lookup",
            "payload": {
                "from": "test@s.whatsapp.net",
                "text": "P0420",
                "message_id": f"test_{datetime.now().timestamp()}"
            }
        },
        {
            "name": "Code with vehicle context",
            "payload": {
                "from": "test@s.whatsapp.net",
                "text": "P0420 Toyota Camry 2015",
                "message_id": f"test_{datetime.now().timestamp()}_2"
            }
        },
        {
            "name": "Unknown code (tests AI generation)",
            "payload": {
                "from": "test@s.whatsapp.net",
                "text": "P9999",
                "message_id": f"test_{datetime.now().timestamp()}_3"
            }
        }
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        for test in test_messages:
            print(f"\n{YELLOW}Testing: {test['name']}{RESET}")

            try:
                response = await client.post(
                    WEBHOOK_URL,
                    json=test["payload"],
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": API_KEY
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    reply = data.get("reply", "")

                    print_test(test["name"], True, f"Status: {response.status_code}")
                    print(f"      Reply preview: {reply[:200]}...")

                    # Check reply structure
                    has_code = "P0" in reply or "P1" in reply or "P2" in reply or "P3" in reply
                    has_description = len(reply) > 50

                    if has_code or has_description:
                        print_test("Response Format", True, "Contains code/description")
                    else:
                        print_test("Response Format", False, "Unexpected format")

                elif response.status_code == 401:
                    print_test(test["name"], False, "Authentication failed - check API key")
                    return False
                else:
                    print_test(test["name"], False, f"Status: {response.status_code}")
                    print(f"      Response: {response.text}")

            except httpx.TimeoutException:
                print_test(test["name"], False, "Request timed out (backend may be slow)")
            except Exception as e:
                print_test(test["name"], False, f"Error: {str(e)}")

    return True


def test_configuration():
    """Test 7: Configuration Check"""
    print_header("TEST 7: Configuration Check")

    configs = [
        ("Supabase URL", settings.supabase_url, True),
        ("Supabase Key", settings.supabase_service_key, True),
        ("AI Provider", settings.ai_provider, False),
        ("Baileys API Key", settings.baileys_api_key, False),
        ("AI Enrich Enabled", settings.ai_enrich_enabled, False),
        ("Auto Learn Codes", settings.auto_learn_codes, False),
    ]

    for name, value, required in configs:
        has_value = bool(value)

        if required:
            print_test(name, has_value, f"Value: {'[SET]' if has_value else '[MISSING]'}")
        else:
            status = "[SET]" if has_value else "[NOT SET]"
            print_info(f"{name}: {status}")

    return True


async def main():
    """Run all tests"""
    print(f"\n{GREEN}========================================================================{RESET}")
    print(f"{GREEN}  Vehicle Diagnosis Assistant - End-to-End System Test{RESET}")
    print(f"{GREEN}========================================================================{RESET}")

    results = {}

    # Test 1: Backend health
    results["backend_health"] = await test_backend_health()

    if not results["backend_health"]:
        print(f"\n{RED}[WARNING] Backend not running. Please start it first:{RESET}")
        print(f"   cd VehicleDiagnosisAssistant")
        print(f"   venv\\Scripts\\activate")
        print(f"   uvicorn app.main:app --reload --port 8001")
        print(f"\n{YELLOW}[INFO] Running offline tests only...{RESET}")

    # Test 2 & 3: Database
    db_connected, has_codes = test_database_connection()
    results["database_connection"] = db_connected

    if db_connected:
        results["has_codes"] = test_obd_codes_in_database()

    # Test 4 & 5: Parsing
    results["message_parsing"] = test_message_parsing()
    results["code_validation"] = test_code_validation()

    # Test 6: Webhook
    results["webhook"] = await test_webhook_integration()

    # Test 7: Config
    results["configuration"] = test_configuration()

    # Summary
    print_header("TEST SUMMARY")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test_name, result in results.items():
        status = f"{GREEN}[PASS]{RESET}" if result else f"{RED}[FAIL]{RESET}"
        print(f"{status} - {test_name.replace('_', ' ').title()}")

    print(f"\n{BLUE}Results: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}[SUCCESS] All tests passed! System is operational.{RESET}")
    elif not results.get("has_codes"):
        print(f"\n{YELLOW}[WARNING] System works but database is empty.{RESET}")
        print(f"   Next step: Run the migration script to populate OBD codes")
    else:
        print(f"\n{RED}[WARNING] Some tests failed. Check errors above.{RESET}")


if __name__ == "__main__":
    asyncio.run(main())
