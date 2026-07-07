# WhatsApp Image Send - Root Cause Analysis

**Date:** 2026-07-07  
**Status:** 🔴 **CRITICAL BUG IDENTIFIED**

---

## Executive Summary

**Root Cause:** Missing `get_image_client()` function in `app/core/http_clients.py`

**Impact:** ALL image sends fail with `AttributeError` - images never reach users

**Severity:** **CRITICAL** - Complete image sending feature outage

**Fix Complexity:** Simple - Add missing function (5 lines of code)

---

## 1. System Overview

### How Image Sending Should Work

```
User sends: "P0420"
    ↓
Webhook receives message → routes to diagnosis
    ↓
DiagnosticResult returned with code + system
    ↓
Component mapper extracts component from description
    ↓
SystemDiagramRepository queries for matching diagram
    ↓
Diagram found? → Send image FIRST via Baileys
    ↓
Then send text diagnosis with attribution
```

**Architecture:**
- **Inbound:** Baileys WhatsApp backend → FastAPI webhook
- **Outbound:** FastAPI → Baileys HTTP API (`/send-image` endpoint)
- **Image Storage:** Public HTTPS URLs (Wikimedia, hosted images)
- **Transport:** HTTP POST with JSON payload

---

## 2. Execution Flow

### File: `app/api/routes/webhook.py` (Lines 629-679)

**Step 1:** Diagnostic result returned
```python
if isinstance(result, DiagnosticResult):
```

**Step 2:** Component extraction
```python
from app.services.component_mapper import extract_component_from_description
component = extract_component_from_description(result.description, code=result.code)
search_term = component or result.system
```

**Step 3:** Diagram lookup
```python
diagram = repos["diagram_repo"].get_by_system_fuzzy(search_term)
```

**Step 4:** Image send attempt
```python
image_sender = ImageSender(
    baileys_webhook_url=getattr(settings, 'baileys_outbound_url', None),
    timeout=15.0
)

image_sent = await image_sender.send_system_diagram(
    to_number=from_number,
    diagram=diagram
)
```

### File: `app/services/image_sender.py`

**Step 5:** HTTP client acquisition (Lines 140-141)
```python
from app.core.http_clients import get_image_client  # ❌ IMPORT FAILS HERE
client = get_image_client()  # ❌ FUNCTION DOESN'T EXIST
```

**Step 6:** HTTP POST (Lines 142-147)
```python
response = await client.post(
    self.baileys_webhook_url,  # http://localhost:3000/send-image
    json=payload,
    headers=headers,
    timeout=self.timeout
)
```

**Expected Payload:**
```json
{
  "to": "263771234567",
  "image": {
    "url": "https://example.com/diagram.jpg"
  },
  "caption": "Catalytic Converter Diagram"  // Optional
}
```

---

## 3. Problems Found

### 🔴 CRITICAL: Missing `get_image_client()` Function

**File:** `app/services/image_sender.py` (Line 140)  
**Error Type:** `AttributeError`  
**Error Message:** `module 'app.core.http_clients' has no attribute 'get_image_client'`

**Code:**
```python
from app.core.http_clients import get_image_client  # ❌ FAILS
client = get_image_client()  # ❌ NEVER EXECUTES
```

**Why This Fails:**
- `app/core/http_clients.py` defines:
  - ✅ `get_twilio_client()`
  - ✅ `get_baileys_client()`
  - ❌ `get_image_client()` **MISSING**

**Impact:**
- Import fails immediately
- Exception caught at line 82-90 in `image_sender.py`
- Logged as `image_send_failed`
- Returns `False` (graceful degradation)
- User receives text diagnosis but **NO IMAGE**

**Evidence:**
```python
# app/core/http_clients.py - Only 2 functions defined:
@lru_cache(maxsize=1)
def get_twilio_client() -> httpx.AsyncClient:
    ...

@lru_cache(maxsize=1)
def get_baileys_client() -> httpx.AsyncClient:
    ...

# get_image_client() DOES NOT EXIST
```

---

### ⚠️ MAJOR: Silent Failure in Exception Handler

**File:** `app/services/image_sender.py` (Lines 82-90)

**Code:**
```python
except Exception as e:
    logger.error(
        "image_send_failed",
        to=to_number,
        system=diagram.system,
        error=str(e),
        error_type=type(e).__name__
    )
    return False  # ❌ Swallows error silently
```

**Why This is a Problem:**
- Exception logged but **never propagated**
- Webhook continues processing
- User unaware images are broken
- Logs required to detect issue
- No monitoring alerts

**Should Be:**
- Log critical errors to alert channel
- Increment failure metrics
- Consider circuit breaker pattern

---

### ⚠️ MINOR: Inconsistent HTTP Client Usage

**Problem:** Three different client functions for similar tasks

1. `get_twilio_client()` - For Twilio API calls
2. `get_baileys_client()` - For Baileys outbound (exists but **NOT USED**)
3. `get_image_client()` - For image sends (**MISSING**)

**Should Be:**
- Use `get_baileys_client()` for all Baileys outbound calls
- Remove `get_image_client()` import
- Consolidate HTTP client strategy

---

### ⚠️ MINOR: Missing HTTPS Validation

**File:** `app/models/system_diagram.py` (Line 19)

**Code:**
```python
image_url: str  # No validation
```

**Risk:**
- HTTP URLs may fail in WhatsApp (requires HTTPS)
- Invalid URLs crash at send time
- No validation at insertion time

**Should Be:**
```python
from pydantic import HttpUrl, validator

image_url: HttpUrl  # Type-level validation

@validator('image_url')
def validate_https(cls, v):
    if not str(v).startswith('https://'):
        raise ValueError('Image URL must use HTTPS')
    return v
```

---

### ⚠️ MINOR: Hardcoded Timeout

**File:** `app/api/routes/webhook.py` (Line 656)

**Code:**
```python
timeout=15.0  # Images are cached locally, should be fast
```

**Problem:**
- Comment mentions "cached locally" but images are external URLs
- 15s timeout may be too high for UX
- Not configurable via environment

**Should Be:**
```python
# .env
IMAGE_SEND_TIMEOUT_SECONDS=10

# Code
timeout=settings.image_send_timeout_seconds
```

---

## 4. Root Cause

### The Exact Reason Images Are Not Being Sent

**Primary Cause:** `AttributeError: module 'app.core.http_clients' has no attribute 'get_image_client'`

**Sequence of Failure:**

1. User sends OBD code (e.g., "P0420")
2. Diagnosis succeeds → returns `DiagnosticResult`
3. Diagram lookup succeeds → finds matching image
4. `ImageSender.send_system_diagram()` called
5. **Line 140:** `from app.core.http_clients import get_image_client`
6. **Import fails** → `AttributeError`
7. Exception caught in `_send_image_internal()`
8. Bubbles up to `send_system_diagram()` (line 82)
9. Logged as `image_send_failed`
10. Returns `False`
11. Webhook continues with text-only response

**Why This Bug Exists:**

Likely causes (in order of probability):

1. **Refactoring accident** - Function renamed/removed but import not updated
2. **Incomplete implementation** - TODO left in code
3. **Copy-paste error** - Copied from `get_baileys_client()` reference
4. **Merge conflict** - Function deleted in merge

**Why This Wasn't Caught:**

1. ❌ **No unit tests** for `ImageSender`
2. ❌ **No integration tests** for image flow
3. ❌ **Graceful degradation** masks error (returns `False` instead of raising)
4. ❌ **No monitoring alerts** on image send failures
5. ❌ **Logs not checked** during testing

---

## 5. Fixed Code

### Fix #1: Add Missing `get_image_client()` Function

**File:** `app/core/http_clients.py`

**Add after `get_baileys_client()`:**

```python
@lru_cache(maxsize=1)
def get_image_client() -> httpx.AsyncClient:
    """
    Get or create a persistent HTTP client for sending images via Baileys.

    Optimized for:
    - Fast image sends (shorter timeout than general Baileys client)
    - Connection reuse for multiple diagrams
    - Retry on transient failures

    Returns:
        Configured httpx.AsyncClient instance
    """
    transport = httpx.AsyncHTTPTransport(
        retries=2,  # Retry transient failures
        http2=False
    )

    client = httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(15.0, connect=3.0),  # Align with ImageSender.timeout
        limits=httpx.Limits(
            max_keepalive_connections=3,
            max_connections=5,
            keepalive_expiry=30.0
        ),
        follow_redirects=False  # Baileys endpoint should not redirect
    )

    logger.info("image_http_client_created")
    return client
```

---

### Fix #2: Use Existing `get_baileys_client()` (Recommended)

**File:** `app/services/image_sender.py` (Line 140)

**Change:**
```python
# BEFORE (broken):
from app.core.http_clients import get_image_client
client = get_image_client()

# AFTER (use existing client):
from app.core.http_clients import get_baileys_client
client = get_baileys_client()
```

**Why This is Better:**
- ✅ No new function needed
- ✅ Consistent HTTP client strategy
- ✅ Already configured correctly
- ✅ One less import to maintain

**Full Fixed Method:**

```python
async def _send_image_internal(
    self,
    to_number: str,
    diagram: SystemDiagram
) -> bool:
    """
    Internal method to send image via Baileys webhook.

    Args:
        to_number: Recipient number
        diagram: System diagram

    Returns:
        True if successful

    Raises:
        ImageSendError: If send fails
    """
    # Prepare payload for Baileys
    payload = {
        "to": to_number,
        "image": {
            "url": diagram.image_url
        }
    }

    # Add caption if present (keep short for WhatsApp)
    if diagram.caption:
        caption = diagram.caption[:60]
        payload["caption"] = caption

    logger.info(
        "sending_system_diagram",
        to=to_number,
        system=diagram.system,
        image_url=diagram.image_url
    )

    # Send via HTTP POST to Baileys webhook
    headers = {"Content-Type": "application/json"}

    # Add API key if configured
    baileys_api_key = getattr(settings, 'baileys_api_key', None)
    if baileys_api_key:
        headers["X-API-Key"] = baileys_api_key

    # ✅ FIX: Use get_baileys_client() instead of get_image_client()
    from app.core.http_clients import get_baileys_client
    client = get_baileys_client()
    
    response = await client.post(
        self.baileys_webhook_url,
        json=payload,
        headers=headers,
        timeout=self.timeout
    )

    # Check response
    if response.status_code == 200:
        logger.info(
            "system_diagram_sent",
            to=to_number,
            system=diagram.system
        )
        return True
    else:
        logger.warning(
            "system_diagram_send_failed",
            to=to_number,
            system=diagram.system,
            status_code=response.status_code,
            response=response.text[:200]
        )
        return False
```

---

## 6. Additional Improvements

### Improvement #1: Add Monitoring & Alerting

**File:** `app/services/image_sender.py`

```python
# Add metrics tracking
from app.core.metrics import increment_counter, record_histogram

async def send_system_diagram(...) -> bool:
    start_time = time.time()
    
    try:
        result = await self._send_image_internal(...)
        
        # Track success/failure
        increment_counter(
            "image_sends_total",
            labels={"status": "success" if result else "failure"}
        )
        
        # Track latency
        duration = time.time() - start_time
        record_histogram("image_send_duration_seconds", duration)
        
        return result
        
    except Exception as e:
        increment_counter(
            "image_sends_total",
            labels={"status": "error", "error_type": type(e).__name__}
        )
        raise
```

---

### Improvement #2: Add Circuit Breaker

**File:** `app/services/image_sender.py`

```python
from circuitbreaker import circuit

class ImageSender:
    @circuit(failure_threshold=5, recovery_timeout=60)
    async def _send_image_internal(...) -> bool:
        # Existing code
        ...
```

**Why:**
- Stop hammering failed endpoint
- Fail fast after 5 consecutive failures
- Auto-recover after 60 seconds
- Reduces latency during outages

---

### Improvement #3: Validate Image URLs at Insertion

**File:** `app/repositories/system_diagram_repository.py`

```python
def insert_diagram(self, diagram_data: dict) -> dict:
    # Validate HTTPS
    image_url = diagram_data.get('image_url', '')
    if not image_url.startswith('https://'):
        raise ValueError(f"Image URL must use HTTPS: {image_url}")
    
    # Validate URL is reachable (optional - expensive)
    # response = requests.head(image_url, timeout=5)
    # if response.status_code != 200:
    #     raise ValueError(f"Image URL not reachable: {image_url}")
    
    return self.client.table("system_diagrams").insert(diagram_data).execute()
```

---

### Improvement #4: Add Retry Logic with Exponential Backoff

**File:** `app/services/image_sender.py`

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    reraise=True
)
async def _send_image_internal(...) -> bool:
    # Existing code
    ...
```

**Why:**
- Transient network failures auto-recover
- Exponential backoff prevents overwhelming endpoint
- 3 attempts = 1s, 2s, 4s delays

---

### Improvement #5: Add Unit Tests

**File:** `tests/test_image_sender.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.image_sender import ImageSender
from app.models.system_diagram import SystemDiagram
from datetime import datetime

@pytest.mark.asyncio
async def test_send_system_diagram_success():
    """Test successful image send"""
    # Mock HTTP client
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_client.post.return_value = mock_response
    
    with patch('app.core.http_clients.get_baileys_client', return_value=mock_client):
        sender = ImageSender(
            baileys_webhook_url="http://localhost:3000/send-image",
            timeout=10.0
        )
        
        diagram = SystemDiagram(
            id="test-123",
            system="catalytic converter",
            image_url="https://example.com/cat.jpg",
            source="Test",
            license="CC0",
            attribution_text="Test diagram",
            caption="Cat Converter",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = await sender.send_system_diagram("263771234567", diagram)
        
        assert result is True
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_send_system_diagram_failure():
    """Test failed image send"""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_client.post.return_value = mock_response
    
    with patch('app.core.http_clients.get_baileys_client', return_value=mock_client):
        sender = ImageSender(
            baileys_webhook_url="http://localhost:3000/send-image",
            timeout=10.0
        )
        
        diagram = SystemDiagram(...)
        result = await sender.send_system_diagram("263771234567", diagram)
        
        assert result is False


@pytest.mark.asyncio
async def test_send_system_diagram_timeout():
    """Test timeout handling"""
    mock_client = AsyncMock()
    mock_client.post.side_effect = asyncio.TimeoutError()
    
    with patch('app.core.http_clients.get_baileys_client', return_value=mock_client):
        sender = ImageSender(
            baileys_webhook_url="http://localhost:3000/send-image",
            timeout=10.0
        )
        
        diagram = SystemDiagram(...)
        result = await sender.send_system_diagram("263771234567", diagram)
        
        assert result is False


@pytest.mark.asyncio
async def test_send_system_diagram_no_url_configured():
    """Test graceful failure when Baileys URL not configured"""
    sender = ImageSender(baileys_webhook_url=None, timeout=10.0)
    
    diagram = SystemDiagram(...)
    result = await sender.send_system_diagram("263771234567", diagram)
    
    assert result is False
```

---

### Improvement #6: Add Integration Test

**File:** `tests/integration/test_image_flow.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.mark.integration
def test_full_image_send_flow():
    """Test end-to-end image send flow"""
    client = TestClient(app)
    
    # Simulate Baileys webhook with OBD code that has diagram
    payload = {
        "from": "263771234567",
        "text": "P0420",
        "message_id": "test-msg-123"
    }
    
    response = client.post(
        "/webhook/baileys",
        json=payload,
        headers={"X-API-Key": "test-key"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check reply includes attribution
    assert "Diagram:" in data["reply"]
    
    # Check image was sent (would need to mock Baileys endpoint)
    # or check logs for "system_diagram_sent"
```

---

## 7. Final Checklist

### Before Deployment

#### Code Changes
- [ ] Apply Fix #2: Change `get_image_client()` to `get_baileys_client()`
- [ ] OR Apply Fix #1: Add `get_image_client()` function
- [ ] Remove unused import if using Fix #2
- [ ] Add unit tests for `ImageSender`
- [ ] Add integration test for full flow

#### Configuration Verification
- [ ] `BAILEYS_OUTBOUND_URL` set in `.env`
  - **Current:** `http://localhost:3000/send-image`
  - **Verify:** Baileys server running on port 3000
  - **Check:** Endpoint accepts POST with `{to, image, caption}`
- [ ] `BAILEYS_API_KEY` set and matches Baileys server
  - **Current:** `a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298`
- [ ] Baileys server health check:
  ```bash
  curl -X POST http://localhost:3000/send-image \
    -H "X-API-Key: a3bb..." \
    -H "Content-Type: application/json" \
    -d '{"to":"test","image":{"url":"https://example.com/test.jpg"}}'
  ```

#### Database Verification
- [ ] System diagrams exist in database
  ```sql
  SELECT COUNT(*) FROM system_diagrams;
  ```
- [ ] Image URLs use HTTPS
  ```sql
  SELECT system, image_url FROM system_diagrams 
  WHERE image_url NOT LIKE 'https://%';
  ```
- [ ] Image URLs are publicly accessible
  ```bash
  curl -I "https://example.com/diagram.jpg"
  # Should return 200 OK
  ```

#### Network Verification
- [ ] Baileys server reachable from FastAPI
  ```bash
  # From FastAPI container/server:
  curl http://localhost:3000/health
  ```
- [ ] Image URLs reachable from Baileys server
  ```bash
  # From Baileys server:
  curl -I "https://upload.wikimedia.org/..."
  ```
- [ ] No firewall blocking ports
- [ ] HTTPS certificates valid (if using HTTPS for Baileys)

#### Testing Steps
1. **Unit Test:** Run `pytest tests/test_image_sender.py`
2. **Manual Test:** Send "P0420" via WhatsApp
3. **Check Logs:** Verify "system_diagram_sent" log entry
4. **Check WhatsApp:** Verify image received before text
5. **Test Failure:** Stop Baileys server, send code, verify graceful degradation

#### Monitoring Setup
- [ ] Add metric: `image_sends_total{status="success|failure"}`
- [ ] Add metric: `image_send_duration_seconds`
- [ ] Add alert: Image send failure rate > 10%
- [ ] Add dashboard: Image send success rate over time

#### Rollback Plan
If deployment fails:
1. Revert code changes
2. Restart FastAPI server
3. Verify text-only diagnosis still works
4. Investigate logs for new errors

---

## 8. Additional Context

### Environment Configuration

**Current `.env` Settings:**
```bash
BAILEYS_API_KEY=a3bb4b6660552743096545286d5c6677d820b0326542bc8228d428c04bca0298
BAILEYS_OUTBOUND_URL=http://localhost:3000/send-image
```

**Baileys Server Requirements:**
- **Endpoint:** `POST /send-image`
- **Headers:** `X-API-Key`, `Content-Type: application/json`
- **Payload:**
  ```json
  {
    "to": "263771234567",
    "image": {
      "url": "https://example.com/diagram.jpg"
    },
    "caption": "Optional caption"
  }
  ```
- **Response:** `200 OK` on success

---

### Expected Logs (After Fix)

**Success Case:**
```
INFO sending_system_diagram to=263771234567 system="catalytic converter" image_url="https://..."
INFO system_diagram_sent to=263771234567 system="catalytic converter"
```

**Failure Case (Network Error):**
```
INFO sending_system_diagram to=263771234567 system="catalytic converter"
WARNING system_diagram_send_failed to=263771234567 status_code=500 response="Internal Server Error"
```

**Failure Case (Timeout):**
```
INFO sending_system_diagram to=263771234567 system="catalytic converter"
WARNING image_send_timeout to=263771234567 system="catalytic converter" timeout=15.0
```

**Failure Case (No URL Configured):**
```
WARNING image_send_skipped reason="baileys_outbound_url_not_configured"
```

---

### Known Limitations

1. **No image size validation** - Large images may timeout
2. **No image format validation** - Assumes JPEG/PNG
3. **No duplicate send prevention** - Same diagram sent multiple times
4. **No image caching** - Always fetched from external URL
5. **No fallback images** - No placeholder if URL fails

---

## Conclusion

**The bug is simple:** Missing `get_image_client()` function causes `AttributeError`, breaking all image sends.

**The fix is simple:** Use existing `get_baileys_client()` function instead.

**The lesson:** Silent failures + no tests = invisible bugs. Always test critical paths end-to-end.

**Next Steps:**
1. Apply Fix #2 (recommended) - 1 line change
2. Deploy to staging
3. Test manually
4. Add unit tests
5. Deploy to production
6. Monitor logs for "system_diagram_sent"

---

**Estimated Time to Fix:** 15 minutes  
**Estimated Time to Test:** 30 minutes  
**Estimated Time to Deploy:** 15 minutes  
**Total:** ~1 hour to fully resolve

---

