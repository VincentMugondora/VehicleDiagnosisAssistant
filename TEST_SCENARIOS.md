# 🧪 Comprehensive Test Scenarios

## Test Your Vehicle Diagnosis Assistant

Send these messages via WhatsApp to test all features:

---

## ✅ Basic Tests

### Test 1: Help/Welcome Message
```
hi
```
**Expected:** Welcome message with instructions

### Test 2: Help Command
```
help
```
**Expected:** Detailed help text with examples

### Test 3: Unknown Command
```
blahblah
```
**Expected:** Helpful error message suggesting valid inputs

---

## 🔧 OBD Code Lookup Tests

### Test 4: Simple Code (Catalytic Converter)
```
P0420
```
**Expected:** 
- Code name: Catalyst System Efficiency Below Threshold
- System: Emissions
- Severity: moderate
- Multiple causes listed
- Symptoms listed

### Test 5: Misfire Code
```
P0300
```
**Expected:**
- Code name: Random/Multiple Cylinder Misfire
- System: Ignition
- Severity: serious
- Check engine light flashing mentioned

### Test 6: Lean Condition
```
P0171
```
**Expected:**
- Code name: System Too Lean (Bank 1)
- System: Fuel System
- Vacuum leak mentioned as cause

### Test 7: Rich Condition
```
P0172
```
**Expected:**
- Code name: System Too Rich (Bank 1)
- Black smoke mentioned
- Fuel smell mentioned

### Test 8: Specific Cylinder Misfires
```
P0301
```
Then:
```
P0302
```
Then:
```
P0303
```
**Expected:** Each returns cylinder-specific misfire info

### Test 9: EVAP Codes (Different Sizes)
```
P0442
```
Then:
```
P0455
```
Then:
```
P0456
```
**Expected:** Small, large, and very small leak distinctions

### Test 10: Transmission Code
```
P0700
```
**Expected:**
- Transmission Control System Malfunction
- Harsh shifting mentioned

### Test 11: Network Communication Code
```
U0100
```
**Expected:**
- Lost Communication with ECM/PCM
- CAN bus issues mentioned

### Test 12: Body Code (Airbag)
```
B0001
```
**Expected:**
- Driver Airbag Circuit Malfunction
- Airbag warning light mentioned

### Test 13: Chassis Code
```
C1201
```
**Expected:**
- Engine Control System Malfunction
- ABS light mentioned

---

## 🚗 Vehicle-Specific Tests

### Test 14: Code with Vehicle Info
```
P0420 Toyota Camry 2015
```
**Expected:** 
- Code diagnosis
- Vehicle info acknowledged
- May mention Toyota-specific notes (if AI enrichment enabled)

### Test 15: Different Vehicle Format
```
what does P0300 mean for a 2018 Honda Civic?
```
**Expected:**
- Natural language understood
- Code diagnosed
- Vehicle context used

### Test 16: Code with Make/Model/Year
```
P0171 on my 2020 Ford F-150 3.5L EcoBoost
```
**Expected:**
- Code diagnosis
- Engine size acknowledged

---

## 💬 Natural Language Tests

### Test 17: Symptom Description
```
my car is misfiring and won't start
```
**Expected:**
- Asks for more info or
- Suggests possible codes (P0300, P0301-P0304)
- General troubleshooting advice

### Test 18: Check Engine Light Question
```
why is my check engine light on?
```
**Expected:**
- Explanation of check engine light
- Instructions to get code read
- Offer to diagnose code

### Test 19: Rough Idle
```
my engine is idling rough
```
**Expected:**
- Possible causes listed
- Suggests getting OBD codes
- May mention P0507, P0171, vacuum leaks

### Test 20: Poor Fuel Economy
```
my gas mileage is terrible
```
**Expected:**
- Common causes (O2 sensors, MAF, etc.)
- Suggests diagnostic codes
- May mention P0420, P0171/P0172

---

## 🔄 Session Management Tests

### Test 21: Follow-up Question
```
P0420
```
Then wait for response, then send:
```
how do I fix it?
```
**Expected:**
- Remembers P0420 context
- Provides fix/repair information

### Test 22: Ask for More Detail
```
P0300
```
Then:
```
tell me more about the causes
```
**Expected:**
- Expands on causes
- More detailed explanation

### Test 23: Vehicle Context Persistence
```
2018 Honda Accord
```
Then:
```
P0171
```
**Expected:**
- Remembers Honda Accord
- Applies vehicle-specific context

---

## 🧠 AI Enrichment Tests (Cohere)

### Test 24: Complex Question
```
I have codes P0420 and P0300 on my 2015 Toyota Camry. What should I fix first?
```
**Expected:**
- AI analyzes both codes
- Recommends fixing P0300 first (misfire can damage cat)
- Prioritizes repairs

### Test 25: Diagnostic Path
```
P0171 and rough idle
```
**Expected:**
- Connects lean condition to rough idle
- Suggests checking for vacuum leaks first

---

## ⚠️ Error Handling Tests

### Test 26: Invalid Code Format
```
X9999
```
**Expected:**
- Explains invalid format
- Suggests proper format (P, C, B, U followed by 4 digits)

### Test 27: Unknown Code (Not in Database)
```
P9999
```
**Expected:**
- Explains code not found
- May offer to research it (if auto-learn enabled)
- Provides general guidance

### Test 28: Empty Message
```
(send empty message)
```
**Expected:**
- Asks for input
- Shows help message

### Test 29: Very Long Message
```
(send 500+ characters of text)
```
**Expected:**
- Handles gracefully
- Extracts relevant info
- Responds appropriately

---

## 📊 Rate Limiting Tests (Only works with Supabase)

### Test 30: Rapid Messages
Send 5 messages quickly:
```
P0420
P0300
P0171
P0128
P0442
```
**Expected:**
- All processed (under limit)
- No errors

### Test 31: Check Limit (If rate limiting enabled)
Send 25+ messages in short time
**Expected:**
- Eventually rate limited (if configured)
- Error message about limit

---

## 🔁 Idempotency Tests

### Test 32: Duplicate Message Detection
Send same message twice quickly:
```
P0420
```
(wait for response)
```
P0420
```
**Expected:**
- Both processed (different message IDs)
- Both get responses

---

## 🌐 Multi-Language Tests (If Supported)

### Test 33: Spanish
```
¿Qué significa el código P0420?
```
**Expected:**
- English response (or Spanish if supported)
- Code diagnosed correctly

---

## 🎯 Edge Cases

### Test 34: Multiple Codes in One Message
```
I have P0420, P0300, and P0171
```
**Expected:**
- Acknowledges all codes
- May diagnose all or ask which to focus on

### Test 35: Code with Extra Characters
```
P0420.
```
or
```
Code: P0420
```
**Expected:**
- Extracts P0420 correctly
- Ignores extra characters

### Test 36: Lowercase Code
```
p0420
```
**Expected:**
- Normalized to P0420
- Diagnosed correctly

### Test 37: Mixed Content
```
Hi, I need help with P0420 on my Toyota
```
**Expected:**
- Extracts code and vehicle
- Provides diagnosis

---

## 📱 Baileys-Specific Tests

### Test 38: Media Messages (If Supported)
Send image with caption:
```
P0420
```
**Expected:**
- Extracts text from caption
- Responds to code

### Test 39: Reply to Bot Message
Reply to the bot's previous message
**Expected:**
- Handles reply context
- Maintains conversation thread

---

## 🔧 Backend API Tests (Direct)

### Test 40: Health Check
```bash
curl http://localhost:8001/healthz
```
**Expected:**
```json
{"status":"ok","version":"2.0.0","env":"development"}
```

### Test 41: Root Endpoint
```bash
curl http://localhost:8001/
```
**Expected:**
```json
{"service":"Vehicle Diagnosis Assistant","version":"2.0.0","docs":"/docs"}
```

### Test 42: Direct Webhook Call
```bash
curl -X POST http://localhost:8001/webhook/baileys \
  -H "Content-Type: application/json" \
  -d '{
    "from": "1234567890@s.whatsapp.net",
    "text": "P0420",
    "message_id": "test123"
  }'
```
**Expected:**
```json
{"reply":"*Fault code:* P0420..."}
```

### Test 43: API Documentation
Open in browser:
```
http://localhost:8001/docs
```
**Expected:** Interactive Swagger/OpenAPI documentation

---

## 📈 Performance Tests

### Test 44: Response Time - Simple Code
```
P0420
```
**Expected:** Response < 2 seconds

### Test 45: Response Time - AI Enrichment
```
P0420 on 2015 Toyota Camry, what should I do?
```
**Expected:** Response < 5 seconds (AI processing)

### Test 46: Concurrent Users
Have 2-3 people send messages simultaneously
**Expected:** All processed correctly

---

## 🔍 Logging Tests

### Test 47: Check Backend Logs
Send any message and check terminal for:
```
[info] ai_client_initialized provider=cohere
[info] baileys_webhook_received message_id=...
[info] obd_lookup_success code=P0420
[info] session_saved
```

### Test 48: Check Baileys Logs
Check Baileys terminal for:
```
[INFO] Message received
[INFO] Reply sent successfully
```

---

## 📊 Expected Code Coverage

In fallback mode, these **20 codes** work:

**Powertrain (P):**
- ✅ P0171 - System Too Lean
- ✅ P0172 - System Too Rich
- ✅ P0128 - Thermostat
- ✅ P0300 - Random Misfire
- ✅ P0301 - Cylinder 1 Misfire
- ✅ P0302 - Cylinder 2 Misfire
- ✅ P0303 - Cylinder 3 Misfire
- ✅ P0304 - Cylinder 4 Misfire
- ✅ P0401 - EGR Flow
- ✅ P0420 - Catalyst Efficiency
- ✅ P0442 - EVAP Small Leak
- ✅ P0455 - EVAP Large Leak
- ✅ P0456 - EVAP Very Small Leak
- ✅ P0507 - High Idle
- ✅ P0606 - PCM Malfunction
- ✅ P0700 - Transmission
- ✅ P0740 - Torque Converter
- ✅ P1450 - Barometric Pressure

**Chassis (C):**
- ✅ C1201 - Engine Control System

**Body (B):**
- ✅ B0001 - Driver Airbag

**Network (U):**
- ✅ U0100 - Lost Communication

---

## 🎯 Success Criteria

### ✅ System is Working If:
- [ ] Welcome message responds correctly
- [ ] All 20 codes return detailed info
- [ ] Natural language questions understood
- [ ] Vehicle context maintained in session
- [ ] AI enrichment provides relevant answers
- [ ] Error messages are helpful
- [ ] Response times < 5 seconds
- [ ] No crashes or 500 errors
- [ ] Logs show proper flow

### ⚠️ Issues to Watch For:
- Timeout errors (backend not responding)
- 500 errors (backend crash)
- Empty responses
- Garbled text
- Missing code information
- AI not responding
- Session not maintained

---

## 📝 Test Results Template

Use this to track your tests:

| Test # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | Help Message | ✅/❌ | |
| 2 | Help Command | ✅/❌ | |
| 4 | P0420 Lookup | ✅/❌ | |
| 5 | P0300 Lookup | ✅/❌ | |
| ... | ... | ... | |

---

## 🚀 Quick Test Suite

Run these 5 tests for quick verification:

1. `hi` - Test basic response
2. `P0420` - Test code lookup
3. `P0300 on 2015 Honda` - Test vehicle context
4. `what causes rough idle?` - Test natural language
5. `help` - Test help command

If all 5 work, your system is operational! ✅

---

**Last Updated:** 2026-07-03
**Fallback Codes Available:** 20
**Supabase Status:** Offline (Fallback Mode)
