from __future__ import annotations

from pathlib import Path
import tempfile

import yaml
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

from models import Pack
from ingest.pdf_ingest import parse_pdfs, extract_claims
from engine.check01 import run_check
from jobs.pack_refresh import ensure_pack
from report.generate import write_reports

app = FastAPI(title="PermitBot QA MVP")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    cfg = yaml.safe_load(Path("config/jurisdictions.yaml").read_text())
    jurisdictions = sorted(cfg.get("jurisdictions", {}).keys())
    return templates.TemplateResponse("index.html", {"request": request, "jurisdictions": jurisdictions})


@app.post("/run", response_class=HTMLResponse)
async def run(
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
        json_path, html_path = write_reports(result, Path("runs") / result.run_id)

    html = html_path.read_text()
    return HTMLResponse(html)
