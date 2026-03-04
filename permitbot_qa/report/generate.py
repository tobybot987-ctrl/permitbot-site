from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from jinja2 import Template

from models import RunResult
from report.storage import upload_if_configured

HTML_TEMPLATE = """
<html><body>
<h1>PermitBot QA Report</h1>
<p>Run {{ run.run_id }}</p>
<h2>Executive Summary</h2>
<ul>
<li>FAIL: {{ counts['FAIL'] }}</li><li>WARN: {{ counts['WARN'] }}</li>
<li>UNKNOWN: {{ counts['UNKNOWN'] }}</li><li>PASS: {{ counts['PASS'] }}</li>
</ul>
{% for f in run.findings %}
<hr/>
<h3>[{{ f.severity }}] {{ f.title }}</h3>
<p>{{ f.description }}</p>
<p><b>Logic:</b> {{ f.comparison_logic }}</p>
<p><b>Action:</b> {{ f.recommended_action }}</p>
<p><b>Rule Evidence:</b> {{ f.rule_evidence[0].excerpt if f.rule_evidence else '' }}</p>
<p><b>Doc Page:</b> {{ f.doc_evidence[0].page if f.doc_evidence else 'N/A' }}</p>
{% endfor %}
</body></html>
"""


def write_reports(run: RunResult, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "result.json"
    html_path = out_dir / "report.html"

    json_path.write_text(run.model_dump_json(indent=2))
    counts = Counter([f.severity.value for f in run.findings])
    html = Template(HTML_TEMPLATE).render(run=run, counts=counts)
    html_path.write_text(html)

    upload_if_configured(json_path, f"runs/{run.run_id}/result.json")
    upload_if_configured(html_path, f"runs/{run.run_id}/report.html")

    return json_path, html_path
