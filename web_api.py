"""Same-origin HTTP adapter for the existing Vault security boundary."""
import base64
import binascii
import csv
import hmac
import io
import json
import os
import secrets
import time
import tomllib
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import pyotp
from fastapi import Cookie, Depends, FastAPI, File, Header, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from security_analytics import synthetic_demo
from vault import Vault, VaultError


app = FastAPI(title="CipherVault API", docs_url=None, redoc_url=None)
COOKIE = "cv_session"


@app.middleware("http")
async def private_api_responses(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        # Vercel proxies this API. Authenticated data and enrollment material
        # must never be cached by a CDN, proxy, or shared browser cache.
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/healthz", include_in_schema=False)
def health():
    return {"status": "ok"}


def config(name, default=""):
    if name in os.environ:
        return os.environ[name]
    path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if path.is_file():
        return tomllib.loads(path.read_text(encoding="utf-8")).get(name, default)
    return default


@lru_cache(maxsize=1)
def get_vault():
    master = config("VAULT_MASTER_KEY")
    if not master:
        raise HTTPException(503, "VAULT_MASTER_KEY is not configured")
    return Vault(config("VAULT_DATA_DIR", "data"), master)


@app.exception_handler(VaultError)
async def vault_error(_request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


def session(token: str | None = Cookie(default=None, alias=COOKIE)):
    if not token:
        raise HTTPException(401, "Sign in required")
    try:
        get_vault().user(token)
    except VaultError:
        raise HTTPException(401, "Session expired. Sign in again.") from None
    return token


def csrf(token: str = Depends(session), supplied: str | None = Header(default=None, alias="X-CSRF-Token")):
    expected = hmac.digest(get_vault().key, b"web-csrf-v1:" + token.encode(), "sha256").hex()
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(403, "Invalid request token")
    return token


def csrf_for(token):
    return hmac.digest(get_vault().key, b"web-csrf-v1:" + token.encode(), "sha256").hex()


def set_session_cookie(response, token):
    response.set_cookie(COOKIE, token, max_age=1800, httponly=True, secure=config("VAULT_COOKIE_SECURE") == "1",
                        samesite="strict", path="/")


class Login(BaseModel):
    username: str
    password: str
    code: str


class SetupBegin(BaseModel):
    bootstrap_token: str


class SetupComplete(Login):
    bootstrap_token: str
    enrollment: str


class Sharing(BaseModel):
    shared: bool


class Member(BaseModel):
    username: str
    password: str
    role: str


class Active(BaseModel):
    active: bool


class Checkpoint(BaseModel):
    id: int
    mac: str
    signature: str


def verify_bootstrap(value):
    expected = config("VAULT_BOOTSTRAP_TOKEN")
    if not expected or not hmac.compare_digest(value, expected):
        raise HTTPException(403, "Invalid bootstrap token")


@app.get("/api/status")
def status():
    vault = get_vault()
    return {"initialized": not vault.is_empty()}


@app.post("/api/setup/begin")
def setup_begin(body: SetupBegin):
    verify_bootstrap(body.bootstrap_token)
    vault = get_vault()
    if not vault.is_empty():
        raise HTTPException(409, "Vault is already initialized")
    secret = pyotp.random_base32()
    payload = json.dumps({"secret": secret, "expires": int(time.time()) + 600}, separators=(",", ":")).encode()
    encoded = base64.urlsafe_b64encode(payload).decode()
    signature = hmac.digest(vault.key, b"web-setup-v1:" + encoded.encode(), "sha256").hex()
    return {"secret": secret, "uri": pyotp.TOTP(secret).provisioning_uri("administrator", issuer_name="CipherVault"),
            "enrollment": encoded + "." + signature}


@app.post("/api/setup/complete")
def setup_complete(body: SetupComplete):
    verify_bootstrap(body.bootstrap_token)
    try:
        encoded, signature = body.enrollment.rsplit(".", 1)
        expected = hmac.digest(get_vault().key, b"web-setup-v1:" + encoded.encode(), "sha256").hex()
        if not hmac.compare_digest(signature, expected):
            raise ValueError()
        payload = json.loads(base64.urlsafe_b64decode(encoded))
        if payload["expires"] < time.time():
            raise ValueError()
        secret = payload["secret"]
    except (ValueError, KeyError, TypeError, binascii.Error, UnicodeError):
        raise HTTPException(400, "Enrollment expired or invalid") from None
    get_vault().bootstrap(body.username, body.password, secret, body.code)
    return {"created": True}


@app.post("/api/login")
def login(body: Login, response: Response):
    token = get_vault().login(body.username, body.password, body.code)
    set_session_cookie(response, token)
    vault = get_vault()
    return {"user": vault.user(token), "csrf": csrf_for(token), "summary": vault.security_summary(token)}


@app.get("/api/session")
def current(token: str = Depends(session)):
    vault = get_vault()
    return {"user": vault.user(token), "csrf": csrf_for(token), "summary": vault.security_summary(token)}


@app.post("/api/logout")
def logout(response: Response, token: str = Depends(csrf)):
    get_vault().logout(token)
    response.delete_cookie(COOKIE, path="/")
    return {"signed_out": True}


@app.get("/api/overview")
def overview(token: str = Depends(session)):
    vault = get_vault()
    return {"files": vault.files(token), "activity": vault.activity(token, 10), "summary": vault.security_summary(token)}


@app.get("/api/files")
def files(token: str = Depends(session)):
    return get_vault().files(token)


@app.post("/api/files")
async def upload(file: UploadFile = File(...), shared: bool = False, token: str = Depends(csrf)):
    data = await file.read(Vault.MAX_FILE + 1)
    file_id = get_vault().upload(token, file.filename or "", data, shared)
    return {"id": file_id}


@app.get("/api/files/{file_id}/download")
def download(file_id: str, token: str = Depends(session)):
    name, data = get_vault().download(token, file_id)
    return Response(data, media_type="application/octet-stream",
                    headers={"Content-Disposition": "attachment; filename*=UTF-8''" + quote(name),
                             "Cache-Control": "no-store"})


@app.post("/api/files/{file_id}/verify")
def verify(file_id: str, token: str = Depends(csrf)):
    return get_vault().verify(token, file_id)


@app.patch("/api/files/{file_id}/sharing")
def sharing(file_id: str, body: Sharing, token: str = Depends(csrf)):
    get_vault().set_shared(token, file_id, body.shared)
    return {"shared": body.shared}


@app.delete("/api/files/{file_id}")
def delete_file(file_id: str, token: str = Depends(csrf)):
    get_vault().delete(token, file_id)
    return {"deleted": True}


@app.get("/api/users")
def users(token: str = Depends(session)):
    return get_vault().users(token)


@app.post("/api/users")
def create_user(body: Member, token: str = Depends(csrf)):
    secret = get_vault().create_user(token, body.username, body.password, body.role)
    return {"username": body.username, "totp_secret": secret,
            "uri": pyotp.TOTP(secret).provisioning_uri(body.username, issuer_name="CipherVault")}


@app.patch("/api/users/{user_id}")
def set_active(user_id: str, body: Active, token: str = Depends(csrf)):
    get_vault().set_active(token, user_id, body.active)
    return {"active": body.active}


@app.get("/api/activity")
def activity(limit: int = 30, token: str = Depends(session)):
    return get_vault().activity(token, limit)


@app.get("/api/audit")
def audit(token: str = Depends(session)):
    return get_vault().logs(token)


@app.get("/api/audit/status")
def audit_status(token: str = Depends(session)):
    return get_vault().verify_audit(token)


@app.get("/api/audit/checkpoint")
def audit_checkpoint(token: str = Depends(session)):
    return get_vault().audit_checkpoint(token)


@app.post("/api/audit/verify")
def audit_verify(body: Checkpoint, token: str = Depends(csrf)):
    return get_vault().verify_audit(token, body.model_dump())


@app.get("/api/monitoring")
def monitoring(token: str = Depends(session)):
    return get_vault().anomaly_report(token)


@app.get("/api/monitoring/demo")
def monitoring_demo(token: str = Depends(session)):
    get_vault().require(token, ("Admin",), "view_anomalies")
    return synthetic_demo()


@app.get("/api/sessions")
def own_sessions(token: str = Depends(session)):
    return get_vault().own_sessions(token)


@app.post("/api/sessions/revoke-others")
def revoke_sessions(token: str = Depends(csrf)):
    return {"revoked": get_vault().revoke_other_sessions(token)}


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    root = Path(__file__).parent / "web" / "dist"
    target = (root / path).resolve()
    if target.is_relative_to(root.resolve()) and target.is_file():
        return FileResponse(target)
    if (root / "index.html").is_file():
        return FileResponse(root / "index.html")
    raise HTTPException(404, "Build the web frontend first")
