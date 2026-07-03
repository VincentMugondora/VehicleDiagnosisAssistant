"""
Test malformed SUBSCRIBE commands to see actual bot responses.
"""
import sys
sys.path.insert(0, ".")

from app.services.payment_commands import parse_subscribe_command


def test_malformed_commands():
    """Test various malformed SUBSCRIBE commands"""

    test_cases = [
        # (input, description)
        ("SUBSCRIBE", "Missing email and phone"),
        ("SUBSCRIBE john@example.com", "Missing phone number"),
        ("SUBSCRIBE notanemail 0771234567", "Invalid email format"),
        ("SUBSCRIBE john@example.com 12345", "Invalid phone format (too short)"),
        ("SUBSCRIBE john@example.com 0771234567890", "Invalid phone format (too long)"),
        ("SUBSCRIBE john@example.com 0881234567", "Invalid phone prefix (088 not EcoCash)"),
        ("SUBSCRIBE john 0771234567", "Email missing domain"),
        ("SUBSCRIBE john@domain 0771234567", "Email missing TLD"),
        ("subscribe john@example.com 0771234567", "Lowercase (should work)"),
        ("SUBSCRIBE john@example.com 077-123-4567", "Phone with dashes (should work after cleaning)"),
        ("SUBSCRIBE john@example.com +263771234567", "Phone with country code"),
    ]

    print("\n" + "="*80)
    print(" MALFORMED SUBSCRIBE COMMAND TEST")
    print("="*80)

    for i, (command, description) in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {description}")
        print(f"Input: {command}")

        result = parse_subscribe_command(command)

        if result:
            email, phone = result
            print(f"[OK] PARSED: email={email}, phone={phone}")
        else:
            print(f"[X] REJECTED: Would show error message to user")
            print("\nUser would receive:")
            print("-" * 80)
            print("[X] Invalid SUBSCRIBE command format.")
            print()
            print("Correct format:")
            print("SUBSCRIBE <email> <phone>")
            print()
            print("Example:")
            print("SUBSCRIBE john@example.com 0771234567")
            print()
            print("Make sure:")
            print("  - Email has @ and domain")
            print("  - Phone is 10 digits starting with 0")
            print("  - Phone supports EcoCash (071, 073, 077, 078)")
            print("-" * 80)


if __name__ == "__main__":
    test_malformed_commands()
