"""
License Server (PG + Credits) with Version Lock
Drop-in: replace license_server.py
Based on admin SSR v2 (no python-multipart) + delete.
Adds:
- Column min_version (per license key) + global_min_version in table settings (optional)
- /check and /consume require client_version >= min_version
Client must send "ver" in JSON (already in license_client / gate).
"""
from __future__ import annotations

import base64, html, json, os, time
from typing import Any, Dict, Optional
from urllib.parse import parse_qs

import psycopg2
import psycopg2.extras
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

APP_ID = os.environ.get("APP_ID", "forja-viral").strip()
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "").strip()
PRIVATE_KEY_B64 = os.environ.get("FORJA_PRIVATE_KEY_B64", "").strip()
DEBUG_ERRORS = (os.environ.get("DEBUG_ERRORS", "0").strip() == "1")
DEFAULT_MIN_VERSION = os.environ.get("FORJA_MIN_VERSION", "1.0.0").strip()  # global default

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var missing.")

def _now() -> int:
    return int(time.time())

def _load_private_key() -> Ed25519PrivateKey:
    if not PRIVATE_KEY_B64:
        raise RuntimeError("FORJA_PRIVATE_KEY_B64 env var missing.")
    seed = base64.b64decode(PRIVATE_KEY_B64)
    if len(seed) != 32:
        raise RuntimeError("FORJA_PRIVATE_KEY_B64 must be 32 bytes base64.")
    return Ed25519PrivateKey.from_private_bytes(seed)

_PRIV = _load_private_key()

def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")

def _sign_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    token_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sig = _PRIV.sign(token_bytes)
    return {"token": _b64url_encode(token_bytes), "sig": _b64url_encode(sig),
            "exp": int(payload.get("exp") or 0), "credits": int(payload.get("credits") or 0),
            "plan": payload.get("plan") or ""}

def _db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)

def _migrate():
    with _db() as con:
        with con.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id SERIAL PRIMARY KEY,
                license_key TEXT UNIQUE NOT NULL,
                hwid TEXT,
                exp BIGINT NOT NULL,
                credits INT NOT NULL,
                plan TEXT,
                status TEXT DEFAULT 'active',
                min_version TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cur.execute("ALTER TABLE licenses ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
            cur.execute("ALTER TABLE licenses ADD COLUMN IF NOT EXISTS min_version TEXT;")

_migrate()

def _require_admin(req: Request) -> str:
    if not ADMIN_TOKEN:
        raise HTTPException(500, "ADMIN_TOKEN not set")
    tok = req.query_params.get("token") or req.headers.get("x-admin-token") or ""
    if tok != ADMIN_TOKEN:
        raise HTTPException(401, "unauthorized")
    return tok

def _reason(reason: str, detail: str = "") -> JSONResponse:
    payload: Dict[str, Any] = {"ok": False, "reason": reason}
    if DEBUG_ERRORS and detail:
        payload["detail"] = detail[:300]
    return JSONResponse(payload)

def _semver_tuple(v: str) -> tuple:
    parts = [p for p in (v or "").strip().split(".") if p != ""]
    out = []
    for p in parts[:3]:
        try:
            out.append(int(re.sub(r'[^0-9].*$', '', p)))
        except Exception:
            out.append(0)
    while len(out) < 3:
        out.append(0)
    return tuple(out)

def _version_ok(client_ver: str, min_ver: str) -> bool:
    try:
        return _semver_tuple(client_ver) >= _semver_tuple(min_ver)
    except Exception:
        return False

def _issue_token(row: Dict[str, Any], hwid: str) -> JSONResponse:
    payload = {
        "app": APP_ID,
        "license_key": row["license_key"],
        "hwid": hwid,
        "exp": int(row["exp"]),
        "credits": int(row["credits"]),
        "plan": row.get("plan") or "",
        "status": row.get("status") or "active",
        "iat": _now(),
        "min_version": row.get("min_version") or DEFAULT_MIN_VERSION,
    }
    signed = _sign_payload(payload)
    return JSONResponse({"ok": True, **signed})

def _load_row_for_update(cur, license_key: str) -> Optional[Dict[str, Any]]:
    cur.execute("SELECT license_key, hwid, exp, credits, plan, status, min_version FROM licenses WHERE license_key=%s FOR UPDATE", (license_key,))
    row = cur.fetchone()
    return dict(row) if row else None

def _validate_row(row: Dict[str, Any], hwid: str, client_ver: str) -> Optional[str]:
    status = (row.get("status") or "active").lower()
    if status != "active":
        return "blocked"
    if int(row["exp"]) <= _now():
        return "expired"
    if row.get("hwid") and row["hwid"] != hwid:
        return "hwid_mismatch"
    min_ver = row.get("min_version") or DEFAULT_MIN_VERSION
    if client_ver and not _version_ok(client_ver, min_ver):
        return "version_blocked"
    return None

app = FastAPI(title="Forja Viral License Server (PG + Credits + Version Lock)")

@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"ok": True, "app": APP_ID, "ts": _now(), "min_version": DEFAULT_MIN_VERSION})

@app.post("/check")
async def check(req: Request) -> JSONResponse:
    try:
        data = await req.json()
    except Exception:
        return _reason("bad_request")
    license_key = str((data or {}).get("license_key") or "").strip()
    hwid = str((data or {}).get("hwid") or "").strip()
    client_ver = str((data or {}).get("ver") or "").strip() or "0.0.0"
    if not license_key or not hwid:
        return _reason("missing_fields")
    try:
        with _db() as con:
            with con.cursor() as cur:
                row = _load_row_for_update(cur, license_key)
                if not row:
                    return _reason("not_found")
                reason = _validate_row(row, hwid, client_ver)
                if reason:
                    return _reason(reason)
                if not row.get("hwid"):
                    cur.execute("UPDATE licenses SET hwid=%s, updated_at=NOW() WHERE license_key=%s", (hwid, license_key))
                    row["hwid"] = hwid
        return _issue_token(row, hwid)
    except Exception as e:
        print("[/check] error:", repr(e))
        return _reason("server_error", detail=str(e))

@app.post("/activate")
async def activate(req: Request) -> JSONResponse:
    return await check(req)

@app.post("/consume_n")
async def consume_n(req: Request) -> JSONResponse:
    try:
        data = await req.json()
    except Exception:
        return _reason("bad_request")
    license_key = str((data or {}).get("license_key") or "").strip()
    hwid = str((data or {}).get("hwid") or "").strip()
    client_ver = str((data or {}).get("ver") or "").strip() or "0.0.0"
    n = int((data or {}).get("n") or 0)
    if not license_key or not hwid or n <= 0:
        return _reason("missing_fields")
    try:
        with _db() as con:
            with con.cursor() as cur:
                row = _load_row_for_update(cur, license_key)
                if not row:
                    return _reason("not_found")
                reason = _validate_row(row, hwid, client_ver)
                if reason:
                    return _reason(reason)
                if not row.get("hwid"):
                    cur.execute("UPDATE licenses SET hwid=%s, updated_at=NOW() WHERE license_key=%s", (hwid, license_key))
                    row["hwid"] = hwid
                credits = int(row.get("credits") or 0)
                if credits < n:
                    return _reason("no_credits")
                cur.execute("UPDATE licenses SET credits=credits-%s, updated_at=NOW() WHERE license_key=%s RETURNING credits, exp, plan, status, min_version", (n, license_key))
                upd = cur.fetchone()
                row.update(dict(upd))
        return _issue_token(row, hwid)
    except Exception as e:
        print("[/consume_n] error:", repr(e))
        return _reason("server_error", detail=str(e))

@app.post("/consume")
async def consume(req: Request) -> JSONResponse:
    try:
        data = await req.json()
    except Exception:
        return _reason("bad_request")
    license_key = str((data or {}).get("license_key") or "").strip()
    hwid = str((data or {}).get("hwid") or "").strip()
    ver = str((data or {}).get("ver") or "").strip() or "0.0.0"
    if not license_key or not hwid:
        return _reason("missing_fields")
    class _FakeReq:
        async def json(self):
            return {"license_key": license_key, "hwid": hwid, "n": 1, "ver": ver}
    return await consume_n(_FakeReq())  # type: ignore

# Admin SSR (minimal) - list + set min_version per key
def _parse_form_bytes(body: bytes) -> Dict[str, str]:
    qs = parse_qs(body.decode("utf-8", errors="ignore"), keep_blank_values=True)
    return {k: (v[0] if v else "") for k, v in qs.items()}

def _fmt_ts(ts: int) -> str:
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(ts)))
    except Exception:
        return str(ts)

def _admin_html(token: str, items: list[dict], meta: dict) -> str:
    esc = html.escape
    rows=[]
    for it in items:
        lk=esc(str(it.get("license_key","")))
        rows.append(f"<tr><td class='k'>{lk}</td><td>{esc(str(it.get('plan') or ''))}</td>"
                    f"<td><b>{esc(str(it.get('credits') or 0))}</b></td>"
                    f"<td class='k'>{esc(_fmt_ts(int(it.get('exp') or 0)))}</td>"
                    f"<td class='k'>{esc(str(it.get('hwid') or ''))}</td>"
                    f"<td>{esc(str(it.get('status') or 'active'))}</td>"
                    f"<td class='k'>{esc(str(it.get('min_version') or DEFAULT_MIN_VERSION))}</td>"
                    f"<td class='actions'>"
                    f"<form method='post' action='/admin/action?token={esc(token)}'>"
                    f"<input type='hidden' name='action' value='delete'><input type='hidden' name='license_key' value='{lk}'>"
                    f"<button class='danger' onclick=\"return confirm('Excluir?')\">Excluir</button></form>"
                    f"</td></tr>")
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>Forja Viral — Admin</title>
    <style>
    body{{background:#0f1115;color:#e9edf5;font-family:system-ui;margin:0}}
    .wrap{{max-width:1200px;margin:0 auto;padding:18px}}
    .card{{background:#14161b;border:1px solid rgba(255,255,255,.10);border-radius:16px;padding:14px}}
    input,button{{padding:10px 12px;border-radius:12px;border:1px solid rgba(255,255,255,.10);background:rgba(255,255,255,.04);color:#e9edf5}}
    button{{font-weight:800;cursor:pointer}}
    .danger{{background:rgba(239,68,68,.16);border-color:rgba(239,68,68,.35)}}
    table{{width:100%;border-collapse:collapse;margin-top:12px}}
    th,td{{padding:10px;border-bottom:1px solid rgba(255,255,255,.08);font-size:12px;text-align:left}}
    th{{opacity:.75}}
    .k{{font-family:ui-monospace,Menlo,Consolas,monospace}}
    .row{{display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
    </style></head><body>
    <div class='wrap'>
      <div class='card'>
        <div class='row' style='justify-content:space-between'>
          <div><b>Forja Viral — Admin</b><div style='opacity:.75;font-size:12px'>DB: {esc(str(meta.get('db')))} • keys: {esc(str(meta.get('count')))} • global min: {esc(DEFAULT_MIN_VERSION)}</div></div>
          <a style='color:#e9edf5;text-decoration:none' href='/admin?token={esc(token)}'>Atualizar</a>
        </div>
        <hr style='border:0;border-top:1px solid rgba(255,255,255,.08);margin:12px 0'>
        <form class='row' method='post' action='/admin/action?token={esc(token)}'>
          <input type='hidden' name='action' value='set_min_version'>
          <input name='license_key' placeholder='license_key' class='k' style='min-width:240px'>
          <input name='min_version' placeholder='min_version ex: 1.0.2' value='{esc(DEFAULT_MIN_VERSION)}' style='min-width:160px'>
          <button type='submit'>Setar min_version</button>
        </form>
        <table><thead><tr><th>license_key</th><th>plan</th><th>credits</th><th>exp</th><th>hwid</th><th>status</th><th>min_version</th><th>ações</th></tr></thead>
        <tbody>{''.join(rows) if rows else "<tr><td colspan='8' style='opacity:.75'>Sem itens</td></tr>"}</tbody></table>
      </div>
    </div></body></html>"""

@app.get("/admin", response_class=HTMLResponse)
async def admin(req: Request) -> HTMLResponse:
    tok=_require_admin(req)
    with _db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT current_database() AS db;")
            db=(cur.fetchone() or {}).get("db")
            cur.execute("SELECT COUNT(*)::int AS count FROM licenses;")
            count=(cur.fetchone() or {}).get("count",0)
            cur.execute("SELECT license_key, hwid, exp, credits, plan, status, min_version FROM licenses ORDER BY created_at DESC LIMIT 1000;")
            items=[dict(x) for x in (cur.fetchall() or [])]
    return HTMLResponse(_admin_html(tok, items, {"db":db, "count":count}))

@app.post("/admin/action")
async def admin_action(req: Request) -> RedirectResponse:
    tok=_require_admin(req)
    form=_parse_form_bytes(await req.body())
    action=(form.get("action") or "").strip()
    lk=(form.get("license_key") or "").strip()
    try:
        with _db() as con:
            with con.cursor() as cur:
                if action=="delete" and lk:
                    cur.execute("DELETE FROM licenses WHERE license_key=%s", (lk,))
                elif action=="set_min_version" and lk:
                    mv=(form.get("min_version") or "").strip()
                    if mv:
                        cur.execute("UPDATE licenses SET min_version=%s, updated_at=NOW() WHERE license_key=%s", (mv, lk))
    except Exception as e:
        print("[/admin/action] error:", repr(e))
    return RedirectResponse(url=f"/admin?token={tok}", status_code=303)
