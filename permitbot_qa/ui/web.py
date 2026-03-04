from __future__ import annotations

from pathlib import Path
import tempfile
import secrets
import os

import yaml
from fastapi import FastAPI, File, Form, UploadFile, Request, Depends, HTTPException, status, Response, Cookie
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from models import Pack
from ingest.pdf_ingest import parse_pdfs, extract_claims
from engine.check01 import run_check
from jobs.pack_refresh import ensure_pack
from report.generate import write_reports
from report.notify import send_resend_notification
from report.db import save_run_summary
from ui.observability import init_sentry
from ui.supabase_auth import enabled as supabase_enabled, password_sign_in, token_user

app = FastAPI(title="PermitBot QA MVP")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
RUNS_DIR = Path("runs")
init_sentry()

security = HTTPBasic()


def require_auth(
    request: Request,
    credentials: HTTPBasicCredentials | None = Depends(security),
    sb_access_token: str | None = Cookie(default=None),
):
    if supabase_enabled():
        token = sb_access_token
        if token:
            user = token_user(token)
            if user:
                return user.get("email", "supabase-user")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )

    user = os.getenv("APP_BASIC_USER", "master")
    pwd = os.getenv("APP_BASIC_PASS", "permitbot")
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    ok_user = secrets.compare_digest(credentials.username, user)
    ok_pass = secrets.compare_digest(credentials.password, pwd)
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if not supabase_enabled():
        return HTMLResponse("<p>Supabase auth not enabled. Use basic auth.</p>")
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login_submit(email: str = Form(...), password: str = Form(...)):
    token = password_sign_in(email, password)
    if not token:
        return HTMLResponse("<p>Login failed</p><a href='/login'>Try again</a>", status_code=401)
    resp = RedirectResponse(url="/", status_code=303)
    resp.set_cookie("sb_access_token", token, httponly=True, secure=False, samesite="lax")
    return resp


@app.get("/", response_class=HTMLResponse)
def home(request: Request, _user: str = Depends(require_auth)):
    cfg = yaml.safe_load(Path("config/jurisdictions.yaml").read_text())
    jurisdictions = sorted(cfg.get("jurisdictions", {}).keys())
    return templates.TemplateResponse("index.html", {"request": request, "jurisdictions": jurisdictions})


@app.get("/permitbot-logo.svg")
def logo():
    candidate = Path(__file__).resolve().parents[2] / "permitbot-logo.svg"
    return FileResponse(candidate)


@app.get("/runs/{run_id}/report.html")
def report_html(run_id: str, _user: str = Depends(require_auth)):
    return FileResponse(RUNS_DIR / run_id / "report.html")


@app.get("/runs/{run_id}/result.json")
def report_json(run_id: str, _user: str = Depends(require_auth)):
    return FileResponse(RUNS_DIR / run_id / "result.json", media_type="application/json", filename=f"{run_id}.json")


@app.post("/run", response_class=HTMLResponse)
async def run(
    request: Request,
    _user: str = Depends(require_auth),
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
        save_run_summary(result.run_id, result.project_type, len(result.findings))
        send_resend_notification(subject=f"PermitBot QA run {result.run_id}", html=f"<p>Run complete: {result.run_id}</p><p>Findings: {len(result.findings)}</p>")

    return templates.TemplateResponse("result.html", {"request": request, "run_id": result.run_id})
