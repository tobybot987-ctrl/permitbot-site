# PermitBot QA MVP (Rule-Pack Discrepancy Detector)

## Non-negotiables implemented
- Deterministic, evidence-based findings
- No compliance/approval language
- No runtime live scraping
- UNKNOWN when evidence is missing

## Pydantic Schemas
Defined in `models.py`:
- `Rule`
- `Pack`
- `Claim`
- `Finding`
- `RunResult`

## Repo Tree
```
permitbot_qa/
  pyproject.toml
  README.md
  models.py
  pack_builder/
    build_pack.py
  packs/
  ingest/
    pdf_ingest.py
  engine/
    check01.py
  report/
    generate.py
  ui/
    cli.py
  tests/
    test_engine.py
  samples/
    sources.sample.json
```

## Build Plan
1. Build versioned rule pack from curated sources (`build-pack`).
2. Parse uploaded PDFs with page mapping.
3. Extract Check-01 claims from docs.
4. Load selected pack(s), apply precedence/stricter-of comparisons.
5. Emit deterministic findings with citations or UNKNOWN.
6. Render HTML + JSON report.
7. Add tests for UNKNOWN + precedence behavior.

## Commands
From `permitbot_qa/`:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e . pytest

# Build sample pack
permitbot build-pack --name sample-fl --sources samples/sources.sample.json

# Run check against PDFs (comma-separated)
permitbot run-check --jurisdiction sample-fl --pdfs ../samples/drainage.pdf,../samples/calcs.pdf --check storm_event_retention

# Tests
pytest
```

## Notes
- Pack artifacts write to `packs/<name>/<version>/pack.json`
- Run output writes to `runs/<run_id>/{result.json,report.html}`
- Current extraction is deterministic regex-based MVP for Check 01.


### New runtime behavior
- User selects `--jurisdiction` (required).
- Default uses latest versioned pack for that jurisdiction.
- `--refresh-pack` triggers an ingestion/build step before checks.
- Runtime check engine still uses only versioned artifacts (no direct live-scrape during compare).


## Minimal Web UI
Run locally:
```bash
source .venv/bin/activate
uvicorn ui.web:app --reload --port 8080
```
Then open http://localhost:8080 and upload PDFs, choose jurisdiction, and run Check 01.


## AWS Baseline (started)
Infrastructure scaffolding is in `infra/terraform/` for:
- S3 artifact storage
- SQS job queues
- module placeholders for VPC/DB/compute

Runtime supports optional AWS integrations today:
- `S3_BUCKET` (+ `AWS_REGION`, `S3_PREFIX`) for report artifact upload
- `DATABASE_URL` for run summary persistence

If these env vars are absent, app falls back to local disk-only mode.
