from __future__ import annotations

import json
from pathlib import Path
import typer

from pack_builder.build_pack import build_pack
from ingest.pdf_ingest import extract_claims, parse_pdfs
from engine.check01 import run_check
from report.generate import write_reports
from models import Pack

app = typer.Typer()


@app.command("build-pack")
def build_pack_cmd(name: str, sources: str):
    out = build_pack(name=name, sources_json=sources, out_root=Path("packs"))
    typer.echo(f"built pack at {out}")


@app.command("run-check")
def run_check_cmd(pack: str, pdfs: str, check: str = "storm_event_retention", project_type: str = "all"):
    pack_name, version = pack.split("@")
    p = Path("packs") / pack_name / version / "pack.json"
    if not p.exists():
        raise typer.Exit(f"Pack not found: {p}")
    pack_obj = Pack.model_validate_json(p.read_text())

    pdf_list = [s.strip() for s in pdfs.split(",") if s.strip()]
    pages = parse_pdfs(pdf_list)
    claims = extract_claims(pages)
    run = run_check(pack_obj, [], claims, project_type)
    json_path, html_path = write_reports(run, Path("runs") / run.run_id)
    typer.echo(f"json={json_path}")
    typer.echo(f"html={html_path}")


if __name__ == "__main__":
    app()
