from __future__ import annotations

from pathlib import Path
import typer

from pack_builder.build_pack import build_pack
from ingest.pdf_ingest import extract_claims, parse_pdfs
from engine.check01 import run_check
from report.generate import write_reports
from models import Pack
from jobs.pack_refresh import ensure_pack, load_jurisdiction
from ui.observability import init_sentry

app = typer.Typer()
init_sentry()


@app.command("build-pack")
def build_pack_cmd(name: str, sources: str):
    out = build_pack(name=name, sources_json=sources, out_root=Path("packs"))
    typer.echo(f"built pack at {out}")


@app.command("run-check")
def run_check_cmd(
    pdfs: str,
    check: str = "storm_event_retention",
    project_type: str = "all",
    jurisdiction: str = typer.Option(..., help="Jurisdiction key from config/jurisdictions.yaml"),
    refresh_pack: bool = typer.Option(False, help="Refresh jurisdiction pack before running"),
    secondary_packs: str = typer.Option("", help="Optional comma-separated secondary pack refs name@version"),
):
    config_path = Path("config/jurisdictions.yaml")
    j = load_jurisdiction(jurisdiction, config_path)

    selected_pack = ensure_pack(jurisdiction, refresh_pack, config_path, Path("packs"))
    typer.echo(f"using primary pack: {selected_pack}")

    pack_name, version = selected_pack.split("@")
    p = Path("packs") / pack_name / version / "pack.json"
    pack_obj = Pack.model_validate_json(p.read_text())

    secondary_objs: list[Pack] = []
    if secondary_packs.strip():
        for ref in [x.strip() for x in secondary_packs.split(",") if x.strip()]:
            n, v = ref.split("@")
            sec_file = Path("packs") / n / v / "pack.json"
            secondary_objs.append(Pack.model_validate_json(sec_file.read_text()))

    if not refresh_pack:
        typer.echo(f"note: runtime scraping disabled. using versioned artifacts only. jurisdiction={j['display_name']}")

    pdf_list = [s.strip() for s in pdfs.split(",") if s.strip()]
    pages = parse_pdfs(pdf_list)
    claims = extract_claims(pages)
    run = run_check(pack_obj, secondary_objs, claims, project_type)
    json_path, html_path = write_reports(run, Path("runs") / run.run_id)
    typer.echo(f"json={json_path}")
    typer.echo(f"html={html_path}")


if __name__ == "__main__":
    app()
