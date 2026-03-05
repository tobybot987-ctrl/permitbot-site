# PermitBot QA MVP – Automated Pre-Submittal Compliance Checks

PermitBot QA is the internal runner for building and validating evidence-backed compliance checks before a civil submittal leaves the office. Every feature is written to feel like a senior reviewer, not an "AI guess."

## Product Framing
- **Audience:** Civil PMs, discipline leads, and principals who need reviewer-ready evidence.
- **Output:** PASS / WARN / FAIL / UNKNOWN findings with citations to rule packs and sheet excerpts.
- **Guardrails:** No approval/compliance language, no live scraping during runtime, UNKNOWN whenever evidence is missing.

## Three-Layer Architecture
1. **Layer 1 – Hard Rule Inspection**  
   Codifies statutes, ordinances, and handbook clauses (e.g., Volusia County LDC §72, SJRWMD ERP). Deterministic math/text checks provide certainty with explicit citations.
2. **Layer 2 – Plan Consistency Scan**  
   Cross-checks values across plan sets, drainage reports, details, and calcs to flag mismatches (FFE, routing, structure IDs, sheet references).
3. **Layer 3 – Reviewer Pattern Library**  
   Captures recurring comment themes (missing maintenance notes, unlabeled drainage arrows, etc.) from actual review letters so teams can address them pre-submittal.

> **Status:** The current MVP executes Layer 1 via Check 01 (storm_event_retention). Layers 2 and 3 are scaffolded and will plug into the same report structure.

## Non-Negotiables (implemented)
- Deterministic, evidence-based findings
- UNKNOWN when evidence is missing or parsing fails
- Versioned rule packs only (no runtime scraping)
- Outputs are "pre-submittal QA" only — never "approval" language

## Key Modules
- `models.py` – Pydantic definitions for packs, rules, claims, findings, run results
- `pack_builder/` – Converts curated citations into versioned packs under `packs/<name>/<version>`
- `ingest/` – PDF parsing + claim extraction utilities
- `engine/` – Check implementations (currently `check01.py`)
- `report/` – HTML/JSON rendering + optional S3/database hooks
- `ui/` – CLI + FastAPI runner with Supabase auth
- `tests/` – Regression coverage for precedence/UNKNOWN behavior
- `infra/terraform/` – Early AWS scaffold (S3, SQS, future compute modules)

## Workflow
1. Build or refresh a jurisdiction pack (`permitbot build-pack ...`).
2. Upload 1–3 PDFs via CLI or web runner.
3. Parse PDFs into claims (plan metadata, calculations, citations).
4. Run Check 01 against primary + optional secondary packs.
5. Emit findings with citations + doc evidence.
6. Save HTML + JSON reports (and optionally upload to S3/report DB).

## Commands
From `permitbot_qa/`:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e . pytest

# Build sample pack
permitbot build-pack --name sample-fl --sources samples/sources.sample.json

# Run check against PDFs (comma-separated)
permitbot run-check --jurisdiction sample-fl \
  --pdfs ../samples/drainage.pdf,../samples/calcs.pdf \
  --check storm_event_retention

# Tests
pytest
```

## Runtime Notes
- Rule packs live in `packs/<name>/<version>/pack.json`
- Run artifacts land in `runs/<run_id>/{result.json,report.html}`
- `uvicorn ui.web:app --reload --port 8080` launches the FastAPI runner (Supabase-auth protected)
- Optional AWS env vars (`S3_BUCKET`, `DATABASE_URL`, etc.) activate artifact upload + persistence

## Roadmap Hooks
- Supabase run history table + UI listing (in progress)
- Plan consistency + reviewer-pattern checks feeding the same reporting stack
- Additional jurisdiction packs (Volusia County, SJRWMD, municipal LDCs)

PermitBot QA should always feel like "spellcheck for civil plans" — deterministic, cited, and defensible.
