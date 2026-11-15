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
