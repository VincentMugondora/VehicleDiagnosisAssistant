# Supabase Connection Timeout Fix

**Date:** 2026-07-10
**Issue:** Production webhook failures due to Supabase connection timeouts

---

## Problem

The application was experiencing frequent connection timeouts to Supabase:

```
httpcore.ReadTimeout: The read operation timed out
httpcore.ConnectTimeout: _ssl.c:983: The handshake operation timed out
httpcore.RemoteProtocolError: Server disconnected
[WinError 10054] An existing connection was forcibly closed by the remote host
```

### Impact

- Webhook requests failing with 500 errors
- Users receiving no response when querying OBD codes
- Message idempotency checks failing
- Usage limit checks failing
- Audit logging silently dropped

### Root Causes

1. **Default timeout too short** - Supabase Python client defaults to 5s read timeout
2. **No retry logic** - Single transient network error = immediate failure
3. **No graceful degradation** - Critical operations (idempotency, rate limiting) fail hard on DB timeout

---

## Solutions Implemented

### 1. Increased Timeouts in Supabase Client

**File:** `app/db/client.py`

```python
options = ClientOptions(
    postgrest_client_timeout=30,  # 30s read timeout (up from default 5s)
    storage_client_timeout=30,
    schema="public"
)

_client = create_client(
    settings.supabase_url,
    settings.supabase_service_key,
    options=options
)
```

**Impact:**
- ✅ Handles slow network conditions better
- ✅ Prevents premature timeouts during peak load
- ⚠️ Slightly slower failure detection (30s vs 5s)

### 2. Exponential Backoff Retry Logic

**File:** `app/db/retry_utils.py`

Created utility functions for automatic retry with exponential backoff:

```python
with_retry(
    lambda: supabase.table('users').select('*').execute(),
    max_retries=3,           # Retry up to 3 times
    initial_delay=0.5,       # Start with 0.5s delay
    backoff_multiplier=2.0   # Double delay each retry (0.5s, 1s, 2s)
)
```

**Retryable Errors:**
- `ConnectTimeout` - Can't establish TCP connection
- `ReadTimeout` - Server not responding
- `RemoteProtocolError` - Server disconnected mid-request
- `ConnectError` - Network-level connection failure
- `ConnectionError` - Generic connection issues
- `TimeoutError` - Operation timed out

**Non-Retryable Errors:**
- SQL errors (bad query, constraint violations)
- Authentication errors
- Permission errors
- Data validation errors

These fail immediately without retry.

### 3. Graceful Degradation for Non-Critical Operations

**File:** `app/repositories/message_log_repository.py`

#### Count Recent Messages (Rate Limiting)

**Before:**
```python
result = self.client.table("message_logs").select("*", count="exact")...
return result.count or 0  # Crashes on timeout
```

**After:**
```python
result = with_retry_default_none(
    lambda: self.client.table("message_logs").select("*", count="exact")...,
    operation_name="count_recent_messages"
)
return result.count if result else 0  # Returns 0 on timeout (no rate limiting)
```

**Behavior:**
- On timeout: Returns 0, disables rate limiting for that request
- User gets response instead of 500 error
- Rate limiting resumes when DB recovers

#### Message Idempotency Check

**Before:**
```python
result = self.client.table("message_logs").select("id")...
return len(result.data) > 0  # Crashes on timeout
```

**After:**
```python
result = with_retry_default_none(
    lambda: self.client.table("message_logs").select("id")...,
    operation_name="check_message_exists"
)

if result is None:
    # DB unavailable - fall back to in-memory check
    return message_id in self._processed_messages

return len(result.data) > 0
```

**Behavior:**
- First tries DB with retries
- On failure: Falls back to in-memory set for duplicate detection
- Works during DB outages (limited to single server instance)

#### Audit Log Insert

**Before:**
```python
self.client.table("message_logs").insert({...}).execute()
# Crashes on timeout, no response sent to user
```

**After:**
```python
try:
    with_retry(lambda: self.client.table("message_logs").insert({...}).execute())
except Exception:
    # Fallback to in-memory tracking if audit insert fails
    self._processed_messages.add(message_id)
```

**Behavior:**
- Retries audit log insert up to 3 times
- On failure: Marks as processed in-memory, continues execution
- User gets response even if audit logging fails

---

## Testing

### Local Testing

```bash
# Restart the application to load new timeout config
python -m app.main

# Test with real OBD code lookup
# Send "P0563" via WhatsApp webhook
```

### Expected Behavior

**Before:**
- Timeout after 5s
- No retry
- 500 error to user

**After:**
- First attempt: 30s timeout window
- On failure: Retry with 0.5s delay
- On 2nd failure: Retry with 1s delay
- On 3rd failure: Retry with 2s delay
- On final failure: Graceful degradation (return 0 for count, fall back to in-memory for idempotency)
- User still gets response

### Monitoring

Check logs for retry indicators:

```
2026-07-10T13:25:52.311938Z [warning] database_operation_retry operation=count_recent_messages attempt=1 max_retries=2 error_type=ReadTimeout retry_delay=0.5
```

If you see many retries, it indicates network instability between your server and Supabase.

---

## Configuration

### Environment Variables

No new environment variables needed. Uses existing:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_ENABLED`

### Tuning Timeout Values

If timeouts are still too short, adjust in `app/db/client.py`:

```python
options = ClientOptions(
    postgrest_client_timeout=60,  # Increase to 60s if needed
    ...
)
```

### Tuning Retry Behavior

If retries are too aggressive or too slow, adjust in specific repository methods:

```python
with_retry(
    lambda: ...,
    max_retries=5,           # More retries
    initial_delay=1.0,       # Longer initial delay
    backoff_multiplier=1.5   # Slower backoff growth
)
```

---

## Deployment Checklist

- [ ] Verify supabase-py version >= 2.28.0 (`pip show supabase`)
- [ ] Restart application to load new timeout config
- [ ] Monitor logs for `database_operation_retry` warnings
- [ ] Check error rates decrease in production
- [ ] Verify users receive responses during transient DB issues

---

## Monitoring Queries

### Check Retry Frequency

```bash
# Count retry warnings in last hour
grep "database_operation_retry" app.log | grep "$(date +%Y-%m-%d)" | wc -l
```

### Check Failed Operations After All Retries

```bash
grep "database_operation_failed_after_retries" app.log
```

### Check Graceful Degradations

```bash
grep "database_operation_degraded" app.log
```

---

## Future Improvements

### Short-term (Next Sprint)

1. **Connection pooling health checks**
   - Periodic ping to keep connections alive
   - Proactive detection of stale connections

2. **Circuit breaker pattern**
   - Temporarily stop hitting DB after N consecutive failures
   - Automatic recovery testing

3. **Metrics dashboard**
   - Track retry rates
   - Track degradation events
   - Alert on high retry rates

### Long-term

1. **Redis caching layer**
   - Cache OBD code lookups (rarely change)
   - Cache user usage counts (refresh every 5 mins)
   - Reduce DB load by 70-80%

2. **Read replicas**
   - Route read-heavy operations to Supabase read replicas
   - Reduce load on primary DB

3. **Regional deployment**
   - Deploy closer to Supabase region
   - Reduce network latency

---

## Related Files Modified

- ✅ `app/db/client.py` - Increased timeouts to 30s
- ✅ `app/db/retry_utils.py` - NEW: Retry logic with exponential backoff
- ✅ `app/repositories/message_log_repository.py` - Added retry + graceful degradation

## Files Created

- ✅ `app/db/client_with_timeouts.py` - Alternative implementation (not used, kept as reference)
- ✅ `app/db/retry_utils.py` - Retry utility functions
- ✅ `SUPABASE_TIMEOUT_FIX.md` - This document
