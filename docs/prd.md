# WhatsApp Vehicle Diagnosis Assistant – Product Requirements Document (PRD)

## 1. Product Overview

### Product Name

WhatsApp Vehicle Diagnosis Assistant

### Problem Statement

Vehicle diagnostics today rely on expensive OBD scanners and manual online searches. Small and mid-sized workshops struggle with slow diagnostics, fragmented information, and limited access to manufacturer knowledge.

### Solution

A WhatsApp-based AI assistant that interprets OBD-II error codes and vehicle information, returning clear explanations, likely causes, and actionable repair guidance directly inside WhatsApp.

### Target Users

* Independent mechanics
* Small auto repair workshops
* Mobile mechanics

### Value Proposition

* Faster diagnostics
* Reduced tooling costs
* Clear, structured repair guidance
* Works on any smartphone via WhatsApp

---

## 2. Goals & Non-Goals

### Goals

* Deliver accurate OBD-II code explanations in <5 seconds
* Provide actionable repair steps
* Require minimal user input
* Be usable in noisy, fast-paced workshop environments

### Non-Goals (Phase 1)

* Full ECU programming
* Real-time vehicle sensor streaming
* OEM dealer-level diagnostics

---

## 3. User Stories

### Core User Story

> As a mechanic, I want to send an OBD error code via WhatsApp and quickly receive clear repair guidance so I can fix the vehicle faster.

### Supporting Stories

* As a mechanic, I want causes ranked by likelihood
* As a mechanic, I want simple language, not engineering jargon
* As a mechanic, I want guidance without needing another app

---

## 4. Functional Requirements

### 4.1 Input Handling

* Accept text messages via WhatsApp
* Parse:

  * OBD-II code (e.g., P0171)
  * Vehicle make
  * Model
  * Year
  * Engine (optional)

### 4.2 Diagnostic Logic

* Validate OBD-II code format
* Lookup generic OBD-II definition
* Enrich output using AI reasoning
* Rank causes by probability

### 4.3 Output Response

Responses must include:

* Error code meaning
* Symptoms
* Likely causes (bullet list)
* Recommended checks / fixes
* Safety disclaimer

### 4.4 Error Handling

* Unknown codes → request clarification
* Missing vehicle data → prompt user
* API failures → fallback generic response

---

## 5. Non-Functional Requirements

### Performance

* Response time < 5 seconds

### Reliability

* 99% uptime target

### Scalability

* Handle 1k+ concurrent conversations

### Security

* No storage of personal data beyond phone number
* Encrypted API communication

---

## 6. UX & Conversation Design

### Conversation Principles

* Short responses
* Bullet points
* Clear headings
* Workshop-friendly language

### Example Conversation

**User:**

```
P0300
Toyota Hilux 2016 2.7L
```

**Bot:**

* *Meaning:* Random/multiple cylinder misfire
* *Likely causes:* Spark plugs, ignition coils, vacuum leak
* *Recommended checks:* Inspect plugs, test coils, check intake leaks

---

## 7. Technical Architecture

### System Flow

WhatsApp → Webhook → Backend API →

* OBD database lookup
* AI reasoning
  → Structured response → WhatsApp

### Tech Stack

* WhatsApp Business API (Twilio / Meta)
* Backend: Python + FastAPI
* Database: PostgreSQL
* AI: LLM via API

---

## 8. Data Model

### obd_codes

* code (string, PK)
* description (text)
* symptoms (text)
* common_causes (text)
* generic_fixes (text)

### message_logs

* id
* phone_number
* request_text
* response_text
* timestamp

---

## 9. Risks & Mitigation

| Risk              | Mitigation                               |
| ----------------- | ---------------------------------------- |
| Incorrect advice  | Clear disclaimer + conservative language |
| Legal liability   | Informational-only positioning           |
| Poor data quality | Use verified public datasets             |

---

## 10. KPIs

* Avg response time
* % successful code interpretations
* Repeat mechanic usage

---

## 11. Roadmap

### Phase 1 (MVP)

* Text-based diagnostics
* Generic OBD-II codes

### Phase 2

* Image recognition
* Manufacturer-specific codes

### Phase 3

* VIN decoding
* Workshop analytics

---

## 12. Appendix A – Windsurf Prompt

For the canonical, copy-paste-ready prompt, see: [Windsurf Prompt](./windsurf-prompt.md).

### Windsurf System Prompt

You are a senior full-stack engineer and product architect.
You are building a production-ready WhatsApp Vehicle Diagnosis Assistant.
Your output must be clean, modular, and scalable.
Use best practices and explain assumptions.

### Windsurf Task Prompt

Build a WhatsApp-based Vehicle Diagnosis Assistant with the following requirements:

* Backend: FastAPI (Python)
* Input: WhatsApp text messages containing OBD-II codes and vehicle details
* Logic:

  1. Parse and validate OBD-II codes
  2. Lookup code definitions from a database
  3. Use AI reasoning to enrich causes and fixes
* Output:

  * Clear, structured diagnostic response optimized for mechanics
* Constraints:

  * Low latency
  * Stateless requests
  * Easy extensibility for images and VIN lookup

Deliver:

* Backend folder structure
* Webhook handler code
* OBD code lookup logic
* AI prompt templates
* Example WhatsApp responses

Think like a startup shipping an MVP that can scale to production.
