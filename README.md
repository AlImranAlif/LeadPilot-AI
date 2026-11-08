# LeadPilot AI — Explainable CRM Automation Engine

A **working backend-first Credosis Phase 02 demo**. It turns unstructured customer inquiries into structured leads, uses **transparent business rules** to qualify them, persists CRM records, and automatically creates a follow-up task for high-priority leads.

> **Accuracy note:** Out of the box, `EXTRACTION_PROVIDER=demo` uses a local regex/keyword extractor for reliable, no-key demonstration. This is **not an AI model**. Set `EXTRACTION_PROVIDER=gemini` with your own `GEMINI_API_KEY` to use genuine LLM-based structured extraction. Lead scoring itself is intentionally deterministic in both modes.

## Scope checklist

- **Core:** Extract requirements → validate → calculate explainable score → save lead
- **Supporting 1:** Lead listing, filtering, status updates and explanation endpoint
- **Supporting 2:** Persistent automated follow-up tasks for complete high-scoring leads
- **Supporting 3:** Human-review flags, strict input validation, controlled LLM errors and idempotent webhook intake
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

Visit [http://127.0.0.1:8000/ ](https://leadpilot-ai-9wls.onrender.com/)for the dashboard or [https://leadpilot-ai-9wls.onrender.com/docs](https://leadpilot-ai-9wls.onrender.com/docs) for Swagger.

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

Other useful calls: `GET /api/leads`, `GET /api/leads/{id}/explanation`, `GET /api/follow-ups`, `PATCH /api/leads/{id}` with `{"status":"CONTACTED"}`, `GET /api/analytics/summary`.

**Webhook idempotency:** `POST /api/webhooks/inquiries` accepts the same fields plus a unique `event_id`. Repeating the same event ID returns the original lead with `replayed=true`, without a second follow-up.

## Real AI mode (optional)

1. Obtain a Gemini API key from your own account.
2. Add `EXTRACTION_PROVIDER=gemini` and `GEMINI_API_KEY=...` to `.env`.
3. Set `GEMINI_MODEL` to a model your API key can access (the example value may need updating).
4. Restart the server. `/health` will show `"extractor":"gemini"`.

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
  config.py        # environment-driven configuration
  database.py      # SQLAlchemy engine and session
  models.py        # leads, follow_ups, webhook_receipts
  schemas.py       # Pydantic validation and responses
  extraction.py    # demo rules and optional Gemini extraction
  scoring.py       # testable qualification policy
  main.py          # REST API, CRUD, idempotency, analytics
  static/index.html # optional interactive demo console
tests/test_api.py  # automated API and scoring tests
examples/          # sample inquiry fixtures
Dockerfile         # container deployment
render.yaml        # deployment blueprint
```

## Verification

```bash
pytest -q
```

## Deploy

1. Push the folder to a **public GitHub repository** (exclude `.env`, the `.db` file, and API keys).
2. Create a PostgreSQL database on Neon, Supabase, Render, or another provider.
3. Deploy this repository as a Docker web service using `Dockerfile`. Set `DATABASE_URL` to the persistent PostgreSQL connection string.
4. Leave `EXTRACTION_PROVIDER=demo` for a dependable no-key demonstration or configure Gemini separately.
5. Configure `API_KEY` for any publicly exposed instance. Access authenticated requests using `X-API-Key`. The included dashboard has a field to supply this key per browser session. Do **not** put credentials in repository code.
6. Open `/docs` and `/` at the generated deployment URL, test both, then put the exact links in the submission.

**Deployment limits:** This is a small demonstration, not production CRM infrastructure. The API key is a simple shared secret; use a proper identity provider, HTTPS, user isolation, request throttling, audit logging, database migrations, and structured monitoring for production. Use a persistent hosted database; local SQLite files on ephemeral hosts may be lost after restarts.

## Phase 02 walkthrough (3–5 minutes)

1. **0:00–0:35:** Introduce the business problem and LeadPilot AI.
2. **0:35–1:10:** Show `/docs`, explain API-first architecture and database models.
3. **1:10–2:00:** Analyze an example inquiry; explain parsed fields, score, reasons and follow-up task.
4. **2:00–2:45:** Submit an incomplete inquiry; show human-review flag and why no follow-up is created.
5. **2:45–3:30:** Replay webhook with same `event_id` and demonstrate deduplication.
6. **3:30–4:20:** Show persisted records, update status, and demonstrate a validation error.
7. **4:20–4:45:** Explain challenges, trade-offs, and optional genuine Gemini mode.

**Submit:** GitHub repository URL + deployed `/docs` URL (if available) + recorded walkthrough video. Ensure sharing permissions work in a private browser window.

**Important:** The internship invitation says Phase 02 should be based on the Phase 01 idea. Verify that this project is compatible with the original idea or obtain approval for changing it before submitting.
