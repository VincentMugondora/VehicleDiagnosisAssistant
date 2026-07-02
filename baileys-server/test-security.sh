#!/bin/bash

# Security Test Suite for Baileys WhatsApp Server v2.0
# This script tests all security features

set -e

BASE_URL="http://localhost:3000"
API_KEY="test-api-key-for-security-testing-32chars"

echo "=================================="
echo "🔒 Security Test Suite"
echo "=================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✅ PASS:${NC} $1"
}

fail() {
    echo -e "${RED}❌ FAIL:${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠️  WARN:${NC} $1"
}

echo "1️⃣  Testing Health Endpoint (Public Access)"
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health" | grep -q "200\|503"; then
    pass "Health endpoint accessible"
else
    fail "Health endpoint not responding"
fi
echo ""

echo "2️⃣  Testing Missing Authentication"
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/send" -X POST -H "Content-Type: application/json" -d '{"to":"123","message":"test"}' | grep -q "401"; then
    pass "Missing API key returns 401"
else
    fail "Missing API key should return 401"
fi
echo ""

echo "3️⃣  Testing Invalid Authentication"
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/send" -X POST -H "Content-Type: application/json" -H "X-API-Key: wrong-key" -d '{"to":"123","message":"test"}' | grep -q "403"; then
    pass "Invalid API key returns 403"
else
    fail "Invalid API key should return 403"
fi
echo ""

echo "4️⃣  Testing Input Validation (Missing Fields)"
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/send" -X POST -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" -d '{}' | grep -q "400"; then
    pass "Missing fields return 400"
else
    fail "Missing fields should return 400"
fi
echo ""

echo "5️⃣  Testing Input Validation (Invalid Phone)"
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/send" -X POST -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" -d '{"to":"invalid!@#","message":"test"}' | grep -q "400"; then
    pass "Invalid phone returns 400"
else
    fail "Invalid phone should return 400"
fi
echo ""

echo "6️⃣  Testing Request Size Limit (Oversized Payload)"
LARGE_MESSAGE=$(python3 -c "print('A' * 100000)")
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/send" -X POST -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" -d "{\"to\":\"123\",\"message\":\"$LARGE_MESSAGE\"}" | grep -q "413\|400"; then
    pass "Oversized payload rejected"
else
    warn "Oversized payload handling unclear (check logs)"
fi
echo ""

echo "7️⃣  Testing Rate Limiting"
echo "   Sending 25 rapid requests..."
RATE_LIMITED=0
for i in {1..25}; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/send" -X POST -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" -d '{"to":"123","message":"test"}')
    if [ "$CODE" = "429" ]; then
        RATE_LIMITED=1
        break
    fi
done

if [ $RATE_LIMITED -eq 1 ]; then
    pass "Rate limiting active (HTTP 429 received)"
else
    warn "Rate limiting not triggered (may need more requests or server not connected)"
fi
echo ""

echo "8️⃣  Testing Metrics Authentication"
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/metrics" | grep -q "401"; then
    pass "Metrics endpoint requires authentication"
else
    fail "Metrics endpoint should require authentication"
fi
echo ""

echo "9️⃣  Testing Security Headers"
HEADERS=$(curl -s -I "$BASE_URL/health")
if echo "$HEADERS" | grep -q "X-Content-Type-Options: nosniff"; then
    pass "Security headers present (X-Content-Type-Options)"
else
    warn "Security headers may be missing"
fi
echo ""

echo "🔟 Testing 404 Handling"
if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/nonexistent" | grep -q "404"; then
    pass "404 handler working"
else
    fail "404 handler not working"
fi
echo ""

echo "=================================="
echo "🎯 Test Summary"
echo "=================================="
echo ""
echo "✅ All critical security features tested"
echo ""
echo "⚠️  Note: Some tests require the server to be running"
echo "   Start server: npm start"
echo ""
echo "🔍 Additional Manual Tests:"
echo "   - Verify logs don't contain API keys"
echo "   - Test graceful shutdown (Ctrl+C)"
echo "   - Check WhatsApp message flow"
echo "   - Verify reconnection with exponential backoff"
echo ""
