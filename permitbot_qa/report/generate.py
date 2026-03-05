from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from jinja2 import Template

from models import RunResult
from report.storage import upload_if_configured

HTML_TEMPLATE = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>PermitBot QA Report</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <style>
    body { background:#F7F4EC; color:#111827; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; margin:0; }
    .wrap { max-width: 800px; margin: 0 auto; padding: 32px 20px 60px; }
    header { margin-bottom: 24px; }
    .pill { font-size: 11px; letter-spacing: 0.3em; text-transform: uppercase; color:#475467; }
    .summary { display:flex; flex-wrap:wrap; gap:12px; margin:20px 0; }
    .summary-card { flex:1; min-width:150px; background:#fff; border:1px solid #E2E8F0; border-radius:16px; padding:16px; }
    .summary-card h3 { margin:0; font-size:32px; }
    .summary-card span { font-size:12px; color:#475467; }
    .note { background:#fff7e6; border:1px solid #fed7aa; border-radius:16px; padding:16px; font-size:13px; color:#7a4b00; }
    .finding { background:#fff; border:1px solid #E2E8F0; border-radius:20px; padding:20px; margin-top:20px; }
    .sev { display:inline-block; font-size:11px; font-weight:600; text-transform:uppercase; padding:4px 10px; border-radius:999px; margin-bottom:8px; }
    .sev-FAIL { background:#fee2e2; color:#b91c1c; }
    .sev-WARN { background:#fef3c7; color:#92400e; }
    .sev-UNKNOWN { background:#e0f2fe; color:#075985; }
    .sev-PASS { background:#dcfce7; color:#15803d; }
    dl { display:grid; grid-template-columns:120px 1fr; gap:6px 12px; font-size:13px; margin:12px 0 0; }
    dt { font-weight:600; color:#475467; }
    dd { margin:0; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <header>
      <span class=\"pill\">Pre-submittal compliance check</span>
      <h1>PermitBot QA Report</h1>
      <p>Run {{ run.run_id }} · Generated {{ run.created_at.strftime('%Y-%m-%d %H:%M UTC') }}</p>
      <p>PermitBot QA organizes findings into three layers: Hard Rule Inspection, Plan Consistency Scan, and Reviewer Pattern Library. This report captures evidence so PMs can address likely reviewer comments before the submittal leaves the office.</p>
    </header>

    <section class=\"summary\">
      <div class=\"summary-card\"><span>FAIL</span><h3>{{ counts['FAIL'] }}</h3></div>
      <div class=\"summary-card\"><span>WARN</span><h3>{{ counts['WARN'] }}</h3></div>
      <div class=\"summary-card\"><span>UNKNOWN</span><h3>{{ counts['UNKNOWN'] }}</h3></div>
      <div class=\"summary-card\"><span>PASS</span><h3>{{ counts['PASS'] }}</h3></div>
    </section>

    <div class=\"note\">
      <strong>Trust-first framing.</strong> Findings are evidence-backed QA guidance, not approvals. UNKNOWN means we could not confirm the requirement with the provided documents.
    </div>

    {% for f in run.findings %}
    <article class=\"finding\">
      <div class=\"sev sev-{{ f.severity.value }}\">{{ f.severity.value }}</div>
      <h3>{{ f.title }}</h3>
      <p>{{ f.description }}</p>
      <p><strong>Comparison:</strong> {{ f.comparison_logic }}</p>
      <p><strong>Recommended action:</strong> {{ f.recommended_action }}</p>
      <dl>
        <dt>Rule evidence</dt>
        <dd>{% if f.rule_evidence %}{{ f.rule_evidence[0].excerpt }}{% else %}—{% endif %}</dd>
        <dt>Rule source</dt>
        <dd>{% if f.rule_evidence and f.rule_evidence[0].source_url %}{{ f.rule_evidence[0].source_url }}{% else %}—{% endif %}</dd>
        <dt>Document page</dt>
        <dd>{% if f.doc_evidence and f.doc_evidence[0].page %}Page {{ f.doc_evidence[0].page }}{% else %}N/A{% endif %}</dd>
        <dt>Document excerpt</dt>
        <dd>{% if f.doc_evidence %}{{ f.doc_evidence[0].excerpt }}{% else %}—{% endif %}</dd>
      </dl>
    </article>
    {% endfor %}
  </div>
</body>
</html>
"""


def write_reports(run: RunResult, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "result.json"
    html_path = out_dir / "report.html"

    json_path.write_text(run.model_dump_json(indent=2))
    counts = Counter([f.severity.value for f in run.findings])
    for key in ["FAIL", "WARN", "UNKNOWN", "PASS"]:
        counts.setdefault(key, 0)
    html = Template(HTML_TEMPLATE).render(run=run, counts=counts)
    html_path.write_text(html)

    upload_if_configured(json_path, f"runs/{run.run_id}/result.json")
    upload_if_configured(html_path, f"runs/{run.run_id}/report.html")

    return json_path, html_path
