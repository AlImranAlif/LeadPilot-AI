# LeadPilot AI — Explainable CRM Automation Engine

A **working backend-first Credosis Phase 02 demo**. It turns unstructured customer inquiries into structured leads, uses **transparent business rules** to qualify them, persists CRM records, and automatically creates a follow-up task for high-priority leads.

> **Accuracy note:** Out of the box, `EXTRACTION_PROVIDER=demo` uses a local regex/keyword extractor for reliable, no-key demonstration. This is **not an AI model**. Set `EXTRACTION_PROVIDER=gemini` with your own `GEMINI_API_KEY` to use genuine LLM-based structured extraction. Lead scoring itself is intentionally deterministic in both modes.

## Scope checklist

- **Core:** Extract requirements → validate → calculate explainable score → save lead
- **Supporting 1:** Lead listing, filtering, status updates, and explanation endpoint
- **Supporting 2:** Persistent automated follow-up tasks for complete high-scoring leads
- **Supporting 3:** Human-review flags, strict input validation, controlled LLM errors, and idempotent webhook intake
- Swagger UI at `/docs`, ReDoc at `/redoc`, optional visual console at `/`

## Quick start

Requires **Python 3.11+**.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env  # On Windows, use: copy .env.example .env
uvicorn app.main:app --reload
```

- **Local console:** `http://127.0.0.1:8000` (Swagger UI at `http://127.0.0.1:8000/docs`)
- **Live demo:** [Dashboard](https://leadpilot-ai-9wls.onrender.com/) | [Swagger UI](https://leadpilot-ai-9wls.onrender.com/docs)

The SQLite database `leadpilot.db` is created automatically on first launch. Use PostgreSQL in deployment by setting `DATABASE_URL=postgresql+psycopg://user:password@host:5432/database` (URL-encode special characters in credentials).

## Test the API

Open `/docs` and run **POST /api/leads/analyze**:

```json
{
  "customer_name": "Ayesha",
  "message": "I need an e-commerce website for my shop. Budget is 80000 BDT and I need it within 3 weeks. Please send a quotation."
}
```

Expected in demo mode: service `E-commerce development`, budget `80000`, deadline `21`, score `100`, priority `HIGH`, `review_required=false`, and `follow_up_created=true`.

Other useful calls:
- `GET /api/leads`
- `GET /api/leads/{id}/explanation`
- `GET /api/follow-ups`
- `PATCH /api/leads/{id}` with `{"status": "CONTACTED"}`
- `GET /api/analytics/summary`

**Webhook idempotency:** `POST /api/webhooks/inquiries` accepts the same fields plus a unique `event_id`. Repeating the same event ID returns the original lead with `replayed=true`, without creating a duplicate follow-up.

## Real AI mode (Gemini API)

### 1. How to generate a Gemini API key

1. Go to [Google AI Studio](https://aistudio.google.com/api-keys) and sign in with your Google account.
2. Accept the Terms of Service if prompted.
3. Click **Get API key** in the menu, then click **Create API key**.
4. Choose **Create API key in new project** (free tier works for testing without a credit card) or select an existing Google Cloud project.
5. Copy the generated key (it starts with `AIza...`). Keep it secret and **never commit it to GitHub**.

### 2. Enable Gemini in your `.env` file

Open your local `.env` file (created from `.env.example`) and update these lines:

```env
EXTRACTION_PROVIDER=gemini
GEMINI_API_KEY=your_copied_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

> **Note:** Make sure `GEMINI_MODEL` points to an active model your key can access (such as `gemini-3.5-flash-lite` or `gemini-3.8-flash` — older models like `gemini-2.0-flash` are retired).

### 3. Restart and verify

Restart the server (`uvicorn app.main:app --reload`) and visit `/health`. It should now return `"extractor": "gemini"`.

Gemini is used **only to extract fields**; scoring and follow-ups remain controlled by the backend. If the LLM is unavailable, requests fail with an explicit `502` instead of quietly pretending local rules are AI. No customer data is sent to an LLM in demo mode.

## Scoring logic

| Condition | Points |
|---|---:|
| Recognized service | +25 |
| Budget >= 50,000 BDT (+15 for >= 15,000) | +30 |
| Deadline <= 30 days (+10 for <= 90) | +20 |
| Explicit purchasing/quotation intent (+10 for general inquiry) | +25 |

**HIGH:** score >= 75 and service, budget, and intent present; **MEDIUM:** score >= 45 (or high-scoring but incomplete); otherwise **LOW**. Missing critical information triggers `review_required=true`. HIGH creates one persistent `CONTACT_HIGH_PRIORITY_LEAD` task. These are illustrative rules, not a validated prediction of conversion likelihood.

## Project structure

```text
app/
  config.py         # environment-driven configuration
  database.py       # SQLAlchemy engine and session
  models.py         # leads, follow_ups, webhook_receipts
  schemas.py        # Pydantic validation and responses
  extraction.py     # demo rules and optional Gemini extraction
  scoring.py        # testable qualification policy
  main.py           # REST API, CRUD, idempotency, analytics
  static/index.html # optional interactive demo console
tests/test_api.py   # automated API and scoring tests
examples/           # sample inquiry fixtures
Dockerfile          # container deployment
render.yaml         # deployment blueprint
```

## Verification

```bash
pytest -q
```
