# Malformed SUBSCRIBE Command - Bot Response Examples

## Test Results: Input Validation

### ✅ Valid Inputs (These Work)

| Input | Result | Notes |
|-------|--------|-------|
| `SUBSCRIBE john@example.com 0771234567` | ✅ Accepted | Standard format |
| `subscribe john@example.com 0771234567` | ✅ Accepted | Case-insensitive |
| `SUBSCRIBE john@example.com 077-123-4567` | ✅ Accepted | Dashes auto-removed |
| `SUBSCRIBE john@example.com 0731234567` | ✅ Accepted | Valid prefix (073) |
| `SUBSCRIBE john@example.com 0781234567` | ✅ Accepted | Valid prefix (078) |

### ❌ Invalid Inputs (Bot Shows Error)

#### 1. Missing Arguments

**User sends:** `SUBSCRIBE`

**Bot responds:**
```
❌ Invalid SUBSCRIBE command format.

Correct format:
SUBSCRIBE <email> <phone>

Example:
SUBSCRIBE john@example.com 0771234567

Make sure:
• Email has @ and domain
• Phone is 10 digits starting with 0
• Phone supports EcoCash (071, 073, 077, 078)
```

---

#### 2. Missing Phone Number

**User sends:** `SUBSCRIBE john@example.com`

**Bot responds:**
```
❌ Invalid SUBSCRIBE command format.

Correct format:
SUBSCRIBE <email> <phone>

Example:
SUBSCRIBE john@example.com 0771234567

Make sure:
• Email has @ and domain
• Phone is 10 digits starting with 0
• Phone supports EcoCash (071, 073, 077, 078)
```

---

#### 3. Invalid Email (No @ Symbol)

**User sends:** `SUBSCRIBE notanemail 0771234567`

**Bot responds:**
```
❌ Invalid SUBSCRIBE command format.

Correct format:
SUBSCRIBE <email> <phone>

Example:
SUBSCRIBE john@example.com 0771234567

Make sure:
• Email has @ and domain
• Phone is 10 digits starting with 0
• Phone supports EcoCash (071, 073, 077, 078)
```

---

#### 4. Invalid Email (No Domain)

**User sends:** `SUBSCRIBE john 0771234567`

**Bot responds:**
```
❌ Invalid SUBSCRIBE command format.

Correct format:
SUBSCRIBE <email> <phone>

Example:
SUBSCRIBE john@example.com 0771234567

Make sure:
• Email has @ and domain
• Phone is 10 digits starting with 0
• Phone supports EcoCash (071, 073, 077, 078)
```

---

#### 5. Invalid Email (No TLD)

**User sends:** `SUBSCRIBE john@domain 0771234567`

**Bot responds:**
```
❌ Invalid SUBSCRIBE command format.

Correct format:
SUBSCRIBE <email> <phone>

Example:
SUBSCRIBE john@example.com 0771234567

Make sure:
• Email has @ and domain
• Phone is 10 digits starting with 0
• Phone supports EcoCash (071, 073, 077, 078)
```

---

#### 6. Invalid Phone (Too Short)

**User sends:** `SUBSCRIBE john@example.com 12345`

**Bot responds:**
```
❌ Invalid SUBSCRIBE command format.

Correct format:
SUBSCRIBE <email> <phone>

Example:
SUBSCRIBE john@example.com 0771234567

Make sure:
• Email has @ and domain
• Phone is 10 digits starting with 0
• Phone supports EcoCash (071, 073, 077, 078)
```

---

#### 7. Invalid Phone (Too Long)

**User sends:** `SUBSCRIBE john@example.com 0771234567890`

**Bot responds:**
```
❌ Invalid SUBSCRIBE command format.

Correct format:
SUBSCRIBE <email> <phone>

Example:
SUBSCRIBE john@example.com 0771234567

Make sure:
• Email has @ and domain
• Phone is 10 digits starting with 0
• Phone supports EcoCash (071, 073, 077, 078)
```

---

#### 8. Invalid Phone (Wrong Prefix - Not EcoCash)

**User sends:** `SUBSCRIBE john@example.com 0881234567`

**Bot responds:**
```
❌ Invalid SUBSCRIBE command format.

Correct format:
SUBSCRIBE <email> <phone>

Example:
SUBSCRIBE john@example.com 0771234567

Make sure:
• Email has @ and domain
• Phone is 10 digits starting with 0
• Phone supports EcoCash (071, 073, 077, 078)
```

---

#### 9. Invalid Phone (Country Code Format)

**User sends:** `SUBSCRIBE john@example.com +263771234567`

**Bot responds:**
```
❌ Invalid SUBSCRIBE command format.

Correct format:
SUBSCRIBE <email> <phone>

Example:
SUBSCRIBE john@example.com 0771234567

Make sure:
• Email has @ and domain
• Phone is 10 digits starting with 0
• Phone supports EcoCash (071, 073, 077, 078)
```

**Note:** Country code format `+263` not supported. User must use local format starting with `0`.

---

## Validation Rules

### Email Validation
- ✅ Must contain `@` symbol
- ✅ Must have domain after `@`
- ✅ Must have TLD (`.com`, `.co.zw`, etc.)
- ❌ No validation for email deliverability (Paynow requirement only)

### Phone Validation
- ✅ Must be exactly 10 digits
- ✅ Must start with `0`
- ✅ Must use valid EcoCash prefix: `071`, `073`, `077`, `078`
- ✅ Dashes and spaces auto-removed before validation
- ❌ Country code format (`+263`) not supported

### Command Parsing
- ✅ Case-insensitive (`SUBSCRIBE` or `subscribe` both work)
- ✅ Requires exactly 3 parts: `SUBSCRIBE <email> <phone>`
- ❌ No support for extra arguments
- ❌ No support for quoted strings with spaces

---

## Edge Cases

### What if user adds extra text?

**User sends:** `SUBSCRIBE john@example.com 0771234567 please subscribe me`

**Result:** Extra text ignored, command parsed successfully if first 3 parts are valid.

### What if user uses different spacing?

**User sends:** `SUBSCRIBE    john@example.com    0771234567`

**Result:** Extra spaces handled correctly, command parsed successfully.

### What if email has + or . before @?

**User sends:** `SUBSCRIBE john.doe+test@example.com 0771234567`

**Result:** ✅ Accepted (basic email validation only checks for @ and domain).

---

## Testing Checklist

Before production deployment, test these scenarios:

- [ ] Valid format: `SUBSCRIBE john@example.com 0771234567`
- [ ] Missing email: `SUBSCRIBE 0771234567`
- [ ] Missing phone: `SUBSCRIBE john@example.com`
- [ ] Invalid email: `SUBSCRIBE notanemail 0771234567`
- [ ] Invalid phone prefix: `SUBSCRIBE john@example.com 0881234567`
- [ ] Phone with dashes: `SUBSCRIBE john@example.com 077-123-4567`
- [ ] Lowercase command: `subscribe john@example.com 0771234567`
- [ ] Country code: `SUBSCRIBE john@example.com +263771234567`

---

## For Developers

### Where validation happens:

1. **First pass:** `app/services/payment_commands.py` → `parse_subscribe_command()`
   - Basic format check (3 parts)
   - Email format (@ and domain)
   - Phone format (10 digits, starts with 0, valid prefix)

2. **Second pass:** `app/models/payment.py` → `PaymentInitRequest` Pydantic model
   - Additional validation if API called directly
   - Raises ValidationError with detailed messages

### Error message location:

File: `app/services/payment_commands.py`
Function: `handle_subscribe_command()`
Lines: ~30-45

To customize error message, edit the return string in `handle_subscribe_command()`.

---

**Last Updated:** 2026-07-03  
**Test Script:** `test_malformed_subscribe.py`
