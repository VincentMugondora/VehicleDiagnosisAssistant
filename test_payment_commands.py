"""
Test payment commands (SUBSCRIBE, STATUS, CANCEL, RENEW)
"""
import asyncio
import sys
from app.services.payment_commands import (
    parse_subscribe_command,
    parse_status_command,
    parse_cancel_command,
    parse_renew_command
)

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def test_parse_commands():
    """Test command parsing"""
    print("\n" + "="*60)
    print("PAYMENT COMMAND PARSING TESTS")
    print("="*60)

    # Test SUBSCRIBE
    print("\n[1/4] Testing SUBSCRIBE parsing...")

    tests = [
        ("SUBSCRIBE john@example.com 0771234567", True),
        ("subscribe john@example.com 0771234567", True),
        ("SUBSCRIBE invalid-email 0771234567", False),
        ("SUBSCRIBE john@example.com 123", False),
        ("SUBSCRIBE", False),
        ("SUB john@example.com 0771234567", False),
    ]

    for text, should_pass in tests:
        result = parse_subscribe_command(text)
        status = "PASS" if (result is not None) == should_pass else "FAIL"
        print(f"   [{status}] {text[:40]:40} -> {result}")

    # Test STATUS
    print("\n[2/4] Testing STATUS parsing...")

    tests = [
        ("STATUS", True),
        ("status", True),
        ("StAtUs", True),
        ("STATUS extra", False),
        ("MY STATUS", False),
    ]

    for text, should_pass in tests:
        result = parse_status_command(text)
        status = "PASS" if result == should_pass else "FAIL"
        print(f"   [{status}] {text[:40]:40} -> {result}")

    # Test CANCEL
    print("\n[3/4] Testing CANCEL parsing...")

    tests = [
        ("CANCEL", True),
        ("cancel", True),
        ("CaNcEl", True),
        ("CANCEL extra", False),
        ("MY CANCEL", False),
    ]

    for text, should_pass in tests:
        result = parse_cancel_command(text)
        status = "PASS" if result == should_pass else "FAIL"
        print(f"   [{status}] {text[:40]:40} -> {result}")

    # Test RENEW
    print("\n[4/4] Testing RENEW parsing...")

    tests = [
        ("RENEW john@example.com 0771234567", True),
        ("renew john@example.com 0771234567", True),
        ("RENEW invalid-email 0771234567", False),
        ("RENEW john@example.com 123", False),
        ("RENEW", False),
        ("REN john@example.com 0771234567", False),
    ]

    for text, should_pass in tests:
        result = parse_renew_command(text)
        status = "PASS" if (result is not None) == should_pass else "FAIL"
        print(f"   [{status}] {text[:40]:40} -> {result}")


def test_command_examples():
    """Show example commands"""
    print("\n" + "="*60)
    print("COMMAND EXAMPLES FOR TESTING")
    print("="*60)

    examples = {
        "SUBSCRIBE": [
            "SUBSCRIBE john@example.com 0771234567",
            "SUBSCRIBE jane.doe@email.co.zw 0773456789",
            "subscribe test@domain.com 0777777777"
        ],
        "STATUS": [
            "STATUS",
            "status"
        ],
        "CANCEL": [
            "CANCEL",
            "cancel"
        ],
        "RENEW": [
            "RENEW john@example.com 0771234567",
            "RENEW jane.doe@email.co.zw 0773456789",
            "renew test@domain.com 0777777777"
        ]
    }

    for cmd, examples_list in examples.items():
        print(f"\n{cmd} Command:")
        for ex in examples_list:
            print(f"   {ex}")


def test_phone_validation():
    """Test phone number validation"""
    print("\n" + "="*60)
    print("PHONE NUMBER VALIDATION")
    print("="*60)

    valid_prefixes = ['071', '073', '077', '078']

    test_numbers = [
        ("0771234567", True, "Valid Econet"),
        ("0733456789", True, "Valid NetOne"),
        ("0712345678", True, "Valid Econet"),
        ("0783456789", True, "Valid Telecel"),
        ("0791234567", False, "Invalid prefix"),
        ("771234567", False, "Missing leading 0"),
        ("07712345678", False, "Too long"),
        ("077123456", False, "Too short"),
    ]

    print("\nValid prefixes for EcoCash: " + ", ".join(valid_prefixes))
    print("\nTest Results:")

    for phone, should_pass, description in test_numbers:
        # Simulate validation
        is_valid = (
            phone.startswith('0') and
            len(phone) == 10 and
            any(phone.startswith(prefix) for prefix in valid_prefixes)
        )

        status = "PASS" if is_valid == should_pass else "FAIL"
        result = "Valid" if is_valid else "Invalid"
        print(f"   [{status}] {phone:15} {result:10} - {description}")


if __name__ == "__main__":
    print("="*60)
    print("PAYMENT COMMANDS TEST SUITE")
    print("="*60)

    test_parse_commands()
    test_command_examples()
    test_phone_validation()

    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    print("\nTo test with real backend:")
    print("1. Restart backend: .\\start_backend.bat")
    print("2. Send WhatsApp messages:")
    print("   - SUBSCRIBE john@example.com 0771234567")
    print("   - STATUS")
    print("   - CANCEL")
    print("   - RENEW john@example.com 0771234567")
    print("="*60 + "\n")
