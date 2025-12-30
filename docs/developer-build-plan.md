# WhatsApp Vehicle Diagnosis Assistant

## 1. Project Objective

Build a WhatsApp-based chatbot that interprets OBD-II vehicle error codes and provides mechanics with clear explanations, causes, and repair guidance, including optional visual references.

---

## 2. MVP Scope (Phase 1)

**Core goal:** From WhatsApp message → structured diagnostic response.

### MVP Features

* WhatsApp chat interface
* Accept text input: error code + vehicle details
* Interpret OBD-II codes
* Return:

  * Code meaning
  * Possible causes
  * Suggested fixes
* Stateless request-response flow

---

## 3. Tech Stack (Recommended)

### Frontend

* WhatsApp Business API (via Twilio or Meta Cloud API)

### Backend

* **Language:** Python (FastAPI)
* **Hosting:** Railway / Render / AWS
* **Database:** PostgreSQL (codes + logs)
* **Cache:** Redis (optional)

### AI Layer

* LLM (OpenAI or similar)
* Prompt-based diagnostic reasoning

### Data Sources

* Public OBD-II code datasets
* Manufacturer-specific codes (later phase)

---

## 4. System Architecture

WhatsApp → Webhook → FastAPI Backend →

* Code lookup (DB)
* AI reasoning (LLM)
  → Structured response → WhatsApp

---

## 5. Message Flow

**User Input (WhatsApp):**

```
P0171
Toyota Corolla 2015 1.6L
```

**Backend Processing:**

1. Parse message
2. Validate error code
3. Fetch base definition
4. Enrich with AI reasoning
5. Format response

**Bot Response:**

* Error description
* Likely causes (bullets)
* Recommended checks/fixes

---

## 6. Data Model (Initial)

### obd_codes

* code (string)
* description (text)
* common_causes (text)
* generic_fix (text)

### requests_log

* id
* phone_number
* message
* response
* timestamp

---

## 7. AI Prompt Strategy

**System Prompt:**
"You are an automotive diagnostics assistant for mechanics. Give concise, actionable repair guidance."

**User Context Passed to LLM:**

* Error code
* Vehicle make/model/year
* Base OBD description

---

## 8. Phase 2 Enhancements

* Image recognition for car parts
* VIN-based vehicle lookup
* Multi-language support
* Offline caching
* Workshop analytics dashboard

---

## 9. Risks & Mitigation

| Risk              | Mitigation                          |
| ----------------- | ----------------------------------- |
| Incorrect advice  | Add disclaimer + confidence scoring |
| Legal issues      | Use public/licensed data only       |
| Internet downtime | Cache common codes                  |

---

## 10. Development Roadmap

**Week 1**

* Set up FastAPI
* WhatsApp webhook integration

**Week 2**

* OBD code database
* Core response logic

**Week 3**

* AI integration
* Prompt tuning

**Week 4**

* Testing with real mechanics
* UX improvements

---

## 11. Success Metric

* Response time < 5s
* Accurate interpretation for common OBD-II codes
* Positive mechanic feedback

---

## 12. Next Step

Implement backend webhook + OBD code lookup, then plug in AI reasoning.

For scaffolding the initial codebase quickly, use the copy-paste-ready Windsurf prompt: [Windsurf Prompt](./windsurf-prompt.md).
