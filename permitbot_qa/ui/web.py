from __future__ import annotations

from pathlib import Path
import tempfile

import yaml
from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from models import Pack
from ingest.pdf_ingest import parse_pdfs, extract_claims
from engine.check01 import run_check
from jobs.pack_refresh import ensure_pack
from report.generate import write_reports

app = FastAPI(title="PermitBot QA MVP")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
RUNS_DIR = Path("runs")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    cfg = yaml.safe_load(Path("config/jurisdictions.yaml").read_text())
    jurisdictions = sorted(cfg.get("jurisdictions", {}).keys())
    return templates.TemplateResponse("index.html", {"request": request, "jurisdictions": jurisdictions})


@app.get("/permitbot-logo.svg")
def logo():
    # repo-level logo
    candidate = Path(__file__).resolve().parents[2] / "permitbot-logo.svg"
    if candidate.exists():
        return FileResponse(candidate)
    return FileResponse(Path(__file__).resolve().parents[2] / "permitbot-logo.svg")


@app.get("/runs/{run_id}/report.html")
def report_html(run_id: str):
    return FileResponse(RUNS_DIR / run_id / "report.html")


@app.get("/runs/{run_id}/result.json")
def report_json(run_id: str):
    return FileResponse(RUNS_DIR / run_id / "result.json", media_type="application/json", filename=f"{run_id}.json")


@app.post("/run", response_class=HTMLResponse)
async def run(
    request: Request,
    jurisdiction: str = Form(...),
    project_type: str = Form("all"),
    secondary_packs: str = Form(""),
    refresh_pack: str | None = Form(None),
    pdfs: list[UploadFile] = File(...),
):
    with tempfile.TemporaryDirectory() as td:
        pdf_paths = []
        for f in pdfs[:3]:
            out = Path(td) / f.filename
            out.write_bytes(await f.read())
            pdf_paths.append(str(out))

        selected_pack = ensure_pack(
            jurisdiction=jurisdiction,
            refresh=bool(refresh_pack),
            config_path=Path("config/jurisdictions.yaml"),
            packs_root=Path("packs"),
        )

        pn, pv = selected_pack.split("@")
        primary = Pack.model_validate_json((Path("packs") / pn / pv / "pack.json").read_text())

        secondary_objs = []
        if secondary_packs.strip():
            for ref in [x.strip() for x in secondary_packs.split(",") if x.strip()]:
                n, v = ref.split("@")
                secondary_objs.append(Pack.model_validate_json((Path("packs") / n / v / "pack.json").read_text()))

        pages = parse_pdfs(pdf_paths)
        claims = extract_claims(pages)
        result = run_check(primary, secondary_objs, claims, project_type)
        write_reports(result, RUNS_DIR / result.run_id)

    return templates.TemplateResponse("result.html", {"request": request, "run_id": result.run_id})
