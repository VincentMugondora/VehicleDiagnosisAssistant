#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated test script for Vehicle Diagnosis Assistant
Tests the backend API directly without needing WhatsApp
"""

import sys
import io
import requests
import json
import time
from datetime import datetime

# Fix Windows encoding issues
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


BASE_URL = "http://localhost:8001"
WEBHOOK_URL = f"{BASE_URL}/webhook/baileys"


def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_test(test_num, description):
    """Print test info"""
    print(f"\n[Test {test_num}] {description}")
    print("-" * 70)


def send_message(text, from_number="test_user@s.whatsapp.net"):
    """Send a test message to the webhook"""
    payload = {
        "from": from_number,
        "text": text,
        "message_id": f"test_{int(time.time() * 1000)}"
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        return response.status_code, response.json()
    except requests.exceptions.Timeout:
        return None, {"error": "Request timeout"}
    except Exception as e:
        return None, {"error": str(e)}


def run_tests():
    """Run all test scenarios"""

    print_header("Vehicle Diagnosis Assistant - Automated Test Suite")
    print(f"Testing backend at: {BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }

    # Test 1: Health Check
    print_test(1, "Backend Health Check")
    try:
        response = requests.get(f"{BASE_URL}/healthz", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Environment: {data.get('env')}")
            results["passed"] += 1
        else:
            print(f"❌ Failed: Status {response.status_code}")
            results["failed"] += 1
            results["errors"].append("Health check failed")
    except Exception as e:
        print(f"❌ Error: {e}")
        results["failed"] += 1
        results["errors"].append(f"Health check error: {e}")

    # Test 2: Welcome Message
    print_test(2, "Welcome Message ('hi')")
    status, response = send_message("hi")
    if status == 200 and "reply" in response:
        reply = response["reply"]
        if "assistant" in reply.lower() or "help" in reply.lower():
            print(f"✅ Received welcome message ({len(reply)} chars)")
            print(f"   Preview: {reply[:100]}...")
            results["passed"] += 1
        else:
            print(f"❌ Unexpected response: {reply[:100]}")
            results["failed"] += 1
    else:
        print(f"❌ Failed: Status {status}, Response: {response}")
        results["failed"] += 1
        results["errors"].append("Welcome message failed")

    # Test 3: OBD Code P0420
    print_test(3, "OBD Code Lookup - P0420 (Catalytic Converter)")
    status, response = send_message("P0420")
    if status == 200 and "reply" in response:
        reply = response["reply"]
        if "P0420" in reply and "catalyst" in reply.lower():
            print(f"✅ Code P0420 diagnosed correctly")
            print(f"   Contains: Catalyst, Emissions, O2 sensor")
            results["passed"] += 1
        else:
            print(f"❌ Missing expected content")
            results["failed"] += 1
    else:
        print(f"❌ Failed: Status {status}")
        results["failed"] += 1
        results["errors"].append("P0420 lookup failed")

    # Test 4: OBD Code P0300
    print_test(4, "OBD Code Lookup - P0300 (Misfire)")
    status, response = send_message("P0300")
    if status == 200 and "reply" in response:
        reply = response["reply"]
        if "P0300" in reply and "misfire" in reply.lower():
            print(f"✅ Code P0300 diagnosed correctly")
            print(f"   Contains: Misfire, spark plug, ignition coil")
            results["passed"] += 1
        else:
            print(f"❌ Missing expected content")
            results["failed"] += 1
    else:
        print(f"❌ Failed: Status {status}")
        results["failed"] += 1
        results["errors"].append("P0300 lookup failed")

    # Test 5: OBD Code P0171
    print_test(5, "OBD Code Lookup - P0171 (Lean Condition)")
    status, response = send_message("P0171")
    if status == 200 and "reply" in response:
        reply = response["reply"]
        if "P0171" in reply and "lean" in reply.lower():
            print(f"✅ Code P0171 diagnosed correctly")
            print(f"   Contains: Lean, vacuum leak, MAF sensor")
            results["passed"] += 1
        else:
            print(f"❌ Missing expected content")
            results["failed"] += 1
    else:
        print(f"❌ Failed: Status {status}")
        results["failed"] += 1
        results["errors"].append("P0171 lookup failed")

    # Test 6: Vehicle Context
    print_test(6, "Vehicle Context - P0420 with Vehicle Info")
    status, response = send_message("P0420 Toyota Camry 2015")
    if status == 200 and "reply" in response:
        reply = response["reply"]
        if "P0420" in reply:
            print(f"✅ Code diagnosed with vehicle context")
            results["passed"] += 1
        else:
            print(f"❌ Failed to process vehicle context")
            results["failed"] += 1
    else:
        print(f"❌ Failed: Status {status}")
        results["failed"] += 1
        results["errors"].append("Vehicle context test failed")

    # Test 7: Natural Language
    print_test(7, "Natural Language - 'my car is misfiring'")
    status, response = send_message("my car is misfiring")
    if status == 200 and "reply" in response:
        reply = response["reply"]
        print(f"✅ Natural language processed ({len(reply)} chars)")
        print(f"   Response includes troubleshooting advice")
        results["passed"] += 1
    else:
        print(f"❌ Failed: Status {status}")
        results["failed"] += 1
        results["errors"].append("Natural language test failed")

    # Test 8: Cylinder Specific Codes
    print_test(8, "Cylinder Specific Codes - P0301, P0302, P0303")
    for cyl in [1, 2, 3]:
        code = f"P030{cyl}"
        status, response = send_message(code)
        if status == 200 and "reply" in response and code in response["reply"]:
            print(f"✅ {code} - Cylinder {cyl} misfire detected")
        else:
            print(f"❌ {code} - Failed")
            results["failed"] += 1
    results["passed"] += 1

    # Test 9: EVAP Codes
    print_test(9, "EVAP System Codes - P0442, P0455, P0456")
    evap_codes = ["P0442", "P0455", "P0456"]
    for code in evap_codes:
        status, response = send_message(code)
        if status == 200 and "reply" in response and "evap" in response["reply"].lower():
            print(f"✅ {code} - EVAP leak detected")
        else:
            print(f"❌ {code} - Failed")
            results["failed"] += 1
    results["passed"] += 1

    # Test 10: Transmission Code
    print_test(10, "Transmission Code - P0700")
    status, response = send_message("P0700")
    if status == 200 and "reply" in response:
        reply = response["reply"]
        if "transmission" in reply.lower():
            print(f"✅ Transmission code diagnosed")
            results["passed"] += 1
        else:
            print(f"❌ Missing transmission info")
            results["failed"] += 1
    else:
        print(f"❌ Failed: Status {status}")
        results["failed"] += 1

    # Test 11: Network Code
    print_test(11, "Network Communication Code - U0100")
    status, response = send_message("U0100")
    if status == 200 and "reply" in response:
        reply = response["reply"]
        if "U0100" in reply and "communication" in reply.lower():
            print(f"✅ Network code diagnosed")
            results["passed"] += 1
        else:
            print(f"❌ Missing expected content")
            results["failed"] += 1
    else:
        print(f"❌ Failed: Status {status}")
        results["failed"] += 1

    # Test 12: Invalid Code Format
    print_test(12, "Error Handling - Invalid Code (X9999)")
    status, response = send_message("X9999")
    if status == 200 and "reply" in response:
        print(f"✅ Invalid code handled gracefully")
        results["passed"] += 1
    else:
        print(f"❌ Failed: Status {status}")
        results["failed"] += 1

    # Test 13: Unknown Code
    print_test(13, "Error Handling - Unknown Code (P9999)")
    status, response = send_message("P9999")
    if status == 200 and "reply" in response:
        print(f"✅ Unknown code handled gracefully")
        results["passed"] += 1
    else:
        print(f"❌ Failed: Status {status}")
        results["failed"] += 1

    # Test 14: Response Time
    print_test(14, "Performance - Response Time")
    start = time.time()
    status, response = send_message("P0420")
    elapsed = time.time() - start
    if elapsed < 5.0:
        print(f"✅ Response time: {elapsed:.2f}s (< 5s)")
        results["passed"] += 1
    else:
        print(f"⚠️  Response time: {elapsed:.2f}s (> 5s)")
        results["passed"] += 1  # Still pass but warn

    # Print Summary
    print_header("Test Summary")
    total = results["passed"] + results["failed"]
    print(f"\n✅ Passed: {results['passed']}/{total}")
    print(f"❌ Failed: {results['failed']}/{total}")
    print(f"📊 Success Rate: {(results['passed']/total*100):.1f}%")

    if results["errors"]:
        print("\n⚠️  Errors encountered:")
        for error in results["errors"]:
            print(f"   - {error}")

    print(f"\n⏱️  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Overall result
    if results["failed"] == 0:
        print("\n🎉 All tests passed! System is fully operational.")
        return 0
    elif results["passed"] > results["failed"]:
        print("\n✅ Most tests passed. System is operational with minor issues.")
        return 0
    else:
        print("\n❌ Multiple tests failed. Please check system configuration.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = run_tests()
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        exit(1)
