# Database Tables Quick Reference

**Complete list of all tables needed for VehicleDiagnosisAssistant**

Last Updated: 2026-07-06

---

## Total Count

- **16 User Tables**
- **4 Functions**
- **1 View**
- **13 Triggers**

---

## Tables by Migration File

### Migration 1: `supabase/migrations/001_initial_schema.sql`

| # | Table Name | Purpose | Key Columns |
|---|------------|---------|-------------|
| 1 | `obd_codes` | Master DTC code database | code (PK), description, system |
| 2 | `message_logs` | WhatsApp message audit | id (PK), phone_hash, message_id |
| 3 | `diagnostic_logs` | Analytics tracking | id (PK), code, vehicle, source |
| 4 | `conversation_sessions` | Multi-turn conversation state | id (PK), phone_hash (UNIQUE), state (JSONB) |
| 5 | `external_obd_cache` | External API response cache | (code, make, model, year, engine) PK |
| 6 | `obd_summaries` | AI-generated summaries | (code, make, model, year, engine) PK |
| 7 | `vehicle_overrides` | Vehicle-specific known issues | (code, make, model, year, engine) PK |

### Migration 2: `migrations/add_system_diagrams_table.sql`

| # | Table Name | Purpose | Key Columns |
|---|------------|---------|-------------|
| 8 | `system_diagrams` | Educational diagram URLs | id (PK), system (UNIQUE), image_url |

### Migration 3: `migrations/add_dtc_detail_tables.sql`

| # | Table Name | Purpose | Key Columns |
|---|------------|---------|-------------|
| 9 | `code_vehicle_fitment` | Vehicle applicability per code | id (PK), code_id (FK), make, model, year_start, year_end |
| 10 | `repair_steps` | Step-by-step instructions | id (PK), code_id (FK), step_number, instruction |
| 11 | `parts` | Required parts for repair | id (PK), code_id (FK), part_name, part_number |
| 12 | `common_symptoms` | Driver-reported symptoms | id (PK), code_id (FK), symptom |
| 13 | `related_codes` | Related DTC codes | id (PK), code_id (FK), related_code |

### Migration 4: `migrations/add_payments_tables.sql`

| # | Table Name | Purpose | Key Columns |
|---|------------|---------|-------------|
| 14 | `transactions` | Payment transaction records | id (PK), order_reference (UNIQUE), phone_hash, status |
| 15 | `subscriptions` | Active user subscriptions | id (PK), phone_hash (UNIQUE), start_date, end_date |
| 16 | `user_usage` | Free tier usage tracking | id (PK), phone_hash, diagnostics_count, period_start |

---

## Database Functions

| Function | Returns | Purpose | Migration |
|----------|---------|---------|-----------|
| `update_updated_at_column()` | TRIGGER | Auto-update timestamps | 3 & 4 |
| `has_active_subscription(phone_hash)` | BOOLEAN | Check if user subscribed | 4 |
| `get_weekly_usage(phone_hash)` | INT | Get weekly diagnostic count | 4 |
| `increment_user_usage(phone_hash)` | INT | Increment usage counter | 4 |

---

## Views

| View | Purpose | Migration |
|------|---------|-----------|
| `active_subscriptions` | Currently active subscriptions (is_active=true AND end_date>now()) | 4 |

---

## Foreign Key Relationships

```
obd_codes (code)
    ├── code_vehicle_fitment.code_id → ON DELETE CASCADE
    ├── repair_steps.code_id → ON DELETE CASCADE
    ├── parts.code_id → ON DELETE CASCADE
    ├── common_symptoms.code_id → ON DELETE CASCADE
    └── related_codes.code_id → ON DELETE CASCADE

transactions (id)
    └── subscriptions.transaction_id → ON DELETE SET NULL

conversation_sessions (id)
    └── message_logs.session_id → (optional reference)
```

---

## Setup Order (Critical!)

Run migrations in this exact order:

1. `supabase/migrations/001_initial_schema.sql` → 7 tables
2. `migrations/add_system_diagrams_table.sql` → 1 table
3. `migrations/add_dtc_detail_tables.sql` → 5 tables + function + 5 triggers
4. `migrations/add_payments_tables.sql` → 3 tables + 3 functions + 1 view + 3 triggers

---

## Verification Query

Run this in Supabase SQL Editor after setup:

```sql
-- Count all user tables (should be 16+)
SELECT COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE';

-- List all tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Count functions (should be 4)
SELECT COUNT(*) as function_count
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_type = 'FUNCTION';

-- Count views (should be 1)
SELECT COUNT(*) as view_count
FROM information_schema.views
WHERE table_schema = 'public';
```

---

## Critical Indexes

Most important indexes for performance:

| Table | Index | Purpose |
|-------|-------|---------|
| `message_logs` | idx_message_logs_phone | Fast user message history |
| `conversation_sessions` | idx_sessions_phone_hash | Fast session lookup |
| `code_vehicle_fitment` | idx_code_vehicle_fitment_code_id | Fast fitment lookup |
| `repair_steps` | idx_repair_steps_code_step | Ordered step retrieval |
| `transactions` | idx_transactions_phone_hash | Fast payment history |
| `subscriptions` | idx_subscriptions_phone_hash | Fast subscription check |

---

## Data Population Priority

### Must Have (Day 1)

- `obd_codes`: 132+ base codes (run `scripts/import_obd_datasets.py`)

### Should Have (Week 1)

- `system_diagrams`: Top 10-20 systems (catalytic converter, O2 sensor, etc.)

### Nice to Have (Month 1)

- `code_vehicle_fitment`: Top 100 codes × top 20 vehicle models
- `repair_steps`: Top 50 common codes
- `parts`: Top 50 common codes
- `common_symptoms`: Top 50 common codes
- `related_codes`: Top 50 common codes

### Auto-populated

- `message_logs`: Populated by app during operation
- `diagnostic_logs`: Populated by app during operation
- `conversation_sessions`: Populated by app during operation
- `external_obd_cache`: Populated by app when external APIs called
- `obd_summaries`: Populated by AI during operation
- `transactions`: Populated during payment flow
- `subscriptions`: Populated when subscription activated
- `user_usage`: Populated when diagnostics run

---

## Storage Estimates

| Category | Tables | Initial Size | Growth Rate |
|----------|--------|--------------|-------------|
| Knowledge Base | obd_codes, fitment, steps, parts, symptoms, related | ~50 MB | Minimal |
| Educational | system_diagrams | ~50 KB | Minimal |
| User Data | sessions, subscriptions, usage | ~1 MB | ~10-50 MB/month |
| Logs | message_logs, diagnostic_logs | ~1 MB | ~100-500 MB/month |
| Cache | external_obd_cache, summaries | ~5 MB | ~50-100 MB/month |
| Payments | transactions | ~1 MB | ~10-20 MB/month |

**Total Initial:** ~60 MB  
**Monthly Growth:** ~170-700 MB (depending on usage)

---

## Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| "Table does not exist" | Re-run migration SQL in Supabase editor |
| "Foreign key constraint" | Ensure `obd_codes` table exists first |
| "Function not found" | Re-run `add_payments_tables.sql` migration |
| No data in obd_codes | Run `python scripts/import_obd_datasets.py` |

---

**Need Full Details?** See `DATABASE_SETUP_CHECKLIST.md` for complete setup guide.

**Need Schema Details?** See individual migration SQL files for full DDL.
