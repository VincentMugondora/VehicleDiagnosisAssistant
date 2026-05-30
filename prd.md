# CLAUDE.md — WhatsApp Vehicle Diagnosis Assistant

> Drop this file at the project root. Claude Code reads it automatically on every task.
> Keep rules concrete. No vague guidance like "write clean code".

---

## Project identity

WhatsApp-based vehicle diagnostic assistant. Users send OBD codes and vehicle details via
WhatsApp; the system returns structured diagnosis, causes, repair steps, and optionally image
references. Stack: **FastAPI · Baileys (WhatsApp) · Gemini AI · Supabase/PostgreSQL**.

---

## Absolute rules — never break these

1. **One concern per file.** Routes, services, repositories, schemas, and utilities live in
   separate files. No business logic inside route handlers.

2. **No secrets in code.** All credentials come from environment variables via `config.py`.
   Never hard-code keys, tokens, URLs, or phone numbers.

3. **All functions are typed.** Every parameter and return value has a Python type annotation.
   No `Any` unless genuinely unavoidable — comment why if used.

4. **Validate at the boundary.** All incoming data (webhook payloads, query params) must pass
   through a Pydantic model before touching any service layer.

5. **No raw SQL strings.** Use Supabase client methods or SQLAlchemy ORM. Parameterised queries
   only — never f-string or %-format a SQL string.

6. **Catch only what you handle.** `except Exception` is forbidden except in the top-level
   error handler. Catch specific exception types and do something meaningful.

7. **Log, never print.** Use `structlog` with JSON output. Every log entry must carry
   `phone_number_hash` (SHA-256, never raw), `session_id`, and `request_id`.

8. **WhatsApp messages are idempotent.** The webhook may deliver the same message twice.
   Check `message_id` against the sessions table before processing.

---

## Project structure

```
app/
  api/
    routes/
      webhook.py       # POST /webhook — entry point only, no logic
      health.py        # GET /health, GET /ready
  services/
    message_router.py  # classifies inbound messages, dispatches
    session_manager.py # load/save/expire conversation state
    diagnostic.py      # OBD lookup, symptom mapping, repair guidance
    gemini_client.py   # all Gemini API calls live here
    media_handler.py   # download, validate, pass image to Gemini vision
  repositories/
    sessions_repo.py   # Supabase reads/writes for session state
    obd_cache_repo.py  # OBD code lookups with caching layer
  models/
    webhook.py         # Pydantic models for incoming WhatsApp payloads
    diagnostic.py      # DiagnosticRequest, DiagnosticResult, etc.
    session.py         # SessionState, ConversationTurn
  core/
    config.py          # Settings via pydantic-settings + .env
    logging.py         # structlog setup
    errors.py          # custom exception classes
    middleware.py      # request ID injection, timing
  utils/
    phone.py           # normalise + hash phone numbers
    obd_parser.py      # extract OBD codes from free text
tests/
  unit/
  integration/
.env.example
Dockerfile
docker-compose.yml
pyproject.toml
CLAUDE.md              # this file
```

---

## Naming conventions

| Thing | Convention | Example |
|---|---|---|
| Files | `snake_case.py` | `session_manager.py` |
| Classes | `PascalCase` | `DiagnosticService` |
| Functions / methods | `snake_case` | `get_session_state` |
| Constants | `UPPER_SNAKE` | `MAX_SESSION_TTL_SECONDS` |
| Pydantic models | `PascalCase` + noun | `DiagnosticRequest` |
| DB tables | `snake_case`, plural | `conversation_sessions` |
| Env vars | `UPPER_SNAKE` prefixed | `GEMINI_API_KEY`, `SUPABASE_URL` |

---

## Service layer rules

- Services receive plain Python objects (Pydantic models or dataclasses). They never import
  FastAPI `Request` or `Response`.
- Services never import other services directly — dependency injection via constructor or
  `Depends()` only.
- One public method = one responsibility. If a method needs a docstring longer than two lines
  to explain what it does, split it.
- Async all the way down. Use `async def` for every service method that does I/O.

---

## Session management

- Session state lives in Supabase `conversation_sessions` table, keyed by `phone_number_hash`.
- TTL: 30 minutes of inactivity. Extend on each message. Expire in-band (check timestamp on
  load, do not rely on a cron job for correctness).
- State schema (stored as JSONB `state` column):

```python
class SessionState(BaseModel):
    phone_number_hash: str
    persona: Literal["customer", "provider", "unknown"]
    current_step: str                  # e.g. "awaiting_vehicle_info"
    vehicle: VehicleContext | None
    pending_obd_codes: list[str]
    turns: list[ConversationTurn]      # last 10 turns only
    last_active: datetime
```

- Never store raw phone numbers in the state or logs.

---

## Gemini integration

- All Gemini calls go through `GeminiClient` in `services/gemini_client.py`.
- Use `gemini-1.5-flash` by default. Allow override via `GEMINI_MODEL` env var so you can
  swap to `gemini-1.5-pro` without a code change.
- Every prompt is a function with a clear docstring. No inline prompt strings in service files.
- Implement retry with exponential backoff (max 3 attempts, 1s / 2s / 4s) on `429` and `503`.
- Responses from Gemini must be validated. If the model returns something unparseable, return
  a graceful degradation message — never surface a raw exception to WhatsApp.

```python
# Good
async def build_diagnostic_prompt(obd_codes: list[str], vehicle: VehicleContext) -> str:
    """
    Returns a structured prompt asking Gemini for diagnosis, causes,
    and repair steps for the given OBD codes and vehicle context.
    """
    ...

# Bad — prompt inline in service
result = await gemini.generate("Fix code " + code)
```

---

## OBD parsing rules

- Accept codes in formats: `P0420`, `p0420`, `P 0420`, `"P0420"`. Normalise to uppercase,
  no spaces.
- A single message may contain multiple codes. Extract all of them.
- If no valid code is found but the message contains vehicle-sounding text (make, model,
  symptom keywords), route to `diagnostic.symptom_flow` instead of erroring.
- Never hallucinate OBD meanings. If a code isn't in the local cache and Gemini returns
  low-confidence output, say so explicitly in the WhatsApp reply.

---

## WhatsApp response formatting

- Max message length: 1 500 characters. Split longer responses across 2–3 messages with
  a clear "1/2" prefix.
- Use WhatsApp markdown: `*bold*`, `_italic_`, `` `code` ``. No HTML tags.
- Structure every diagnostic reply as:

```
*Fault code:* P0420
*System:* Catalytic converter / O2 sensor

*What it means:*
Catalyst efficiency below threshold (Bank 1).

*Likely causes:*
• Worn catalytic converter
• Faulty rear O2 sensor
• Exhaust leak before sensor

*Recommended action:*
1. Check for exhaust leaks first — cheapest fix.
2. Live-data test the rear O2 sensor voltage.
3. Replace catalytic converter if sensor is good.

_Always confirm with live scanner data before replacing parts._
```

- Never start a reply with "I". Start with the subject matter.
- Do not end with "Feel free to ask more questions."

---

## Error handling

- All unhandled exceptions bubble to `app/core/middleware.py` global handler.
- Global handler logs the full traceback to structlog and sends a safe WhatsApp reply:
  `"Sorry, we hit a snag processing that. Please resend your code or try again in a moment."`
- Define custom exceptions in `core/errors.py`:

```python
class OBDCodeNotFound(AppError): ...
class SessionExpired(AppError): ...
class GeminiUnavailable(AppError): ...
class InvalidVehicleData(AppError): ...
```

- Never raise `HTTPException` inside a service. Raise domain exceptions; let the route handler
  convert them.

---

## Testing

- Every service method has a unit test. Mock Supabase and Gemini — no live calls in unit tests.
- Integration tests (`tests/integration/`) may hit a local Supabase instance (Docker).
- Fixture files live in `tests/fixtures/`. WhatsApp webhook payloads are stored as `.json`
  files there — no hardcoded payload dicts in test files.
- Aim for ≥80% coverage on `app/services/` and `app/repositories/`.
- Run: `pytest --cov=app --cov-report=term-missing`

---

## Linting and formatting

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "UP", "B", "SIM", "ANN"]
ignore = ["ANN101", "ANN102"]

[tool.ruff.per-file-ignores]
"tests/*" = ["ANN"]

[tool.mypy]
strict = true
ignore_missing_imports = true
```

Pre-commit hooks must pass before any commit:
- `ruff check . --fix`
- `ruff format .`
- `mypy app/`

CI (GitHub Actions) runs the same checks. A failing lint = failing build.

---

## Database schema (Supabase)

```sql
-- conversation_sessions
create table conversation_sessions (
  id           uuid primary key default gen_random_uuid(),
  phone_hash   text not null unique,
  state        jsonb not null default '{}',
  created_at   timestamptz default now(),
  last_active  timestamptz default now()
);
create index on conversation_sessions (last_active);

-- obd_cache
create table obd_cache (
  code         text primary key,         -- e.g. 'P0420'
  make         text,                     -- null = applies to all
  description  text not null,
  system       text,
  common_causes jsonb,
  repair_steps  jsonb,
  updated_at   timestamptz default now()
);
```

Migrations live in `supabase/migrations/`. Never alter the schema manually in production.

---

## Environment variables

```bash
# .env.example — commit this, not .env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash

SUPABASE_URL=
SUPABASE_SERVICE_KEY=

WHATSAPP_VERIFY_TOKEN=
WHATSAPP_API_TOKEN=

LOG_LEVEL=INFO
APP_ENV=development          # development | staging | production
SESSION_TTL_SECONDS=1800
MAX_CONVERSATION_TURNS=10
```

---

## Scaling considerations

- The webhook handler must respond to WhatsApp in < 5 seconds or WhatsApp retries.
  Offload heavy Gemini calls to a background task (`asyncio.create_task`) and send an
  acknowledgement first: `"Analysing your code, reply in a moment..."`.
- Supabase connection pool: use a single shared `AsyncClient` instance (initialised at
  startup via lifespan), not a new client per request.
- OBD codes are read-heavy. Cache common codes in a module-level dict on startup; refresh
  every 6 hours. Avoid a DB round-trip for every P0420.
- If daily message volume exceeds ~5 000, move Gemini calls to a task queue (ARQ / Celery)
  and store results back to Supabase for the response worker to pick up.

---

## What Claude Code should NOT do

- Do not add new dependencies without noting them in `pyproject.toml`.
- Do not create `.py` files outside the `app/` or `tests/` trees without asking first.
- Do not modify `supabase/migrations/` directly — generate a new migration file instead.
- Do not remove type annotations to fix mypy errors — fix the types properly.
- Do not use `time.sleep` anywhere — use `asyncio.sleep`.
- Do not commit `.env` or any file containing real credentials.