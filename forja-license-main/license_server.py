"""
Forja Viral License Server (PostgreSQL + Credits) — SSR Admin v2 (NO python-multipart)

Fixes random {ok:false, reason:"server_error"} by:
- Removing dependency on `await req.form()` (requires python-multipart)
- Parsing x-www-form-urlencoded manually
- Adding clearer error logging to console
- Keeping core API stable: /health, /check, /activate, /consume, /consume_n
- SSR Admin at /admin and actions at /admin/action

ENV:
  DATABASE_URL=postgresql://user:pass@host:5432/db
  FORJA_PRIVATE_KEY_B64=... (32-byte seed base64)
  ADMIN_TOKEN=...
  DEBUG_ERRORS=1   (optional) include short error detail in JSON `detail` for server_error
"""

from __future__ import annotations

import base64
import html
import json
import os
import time
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

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var missing (postgres connection string).")


def _now() -> int:
    return int(time.time())


def _load_private_key() -> Ed25519PrivateKey:
    if not PRIVATE_KEY_B64:
        raise RuntimeError("FORJA_PRIVATE_KEY_B64 env var missing (base64 of 32-byte Ed25519 private seed).")
    try:
        seed = base64.b64decode(PRIVATE_KEY_B64)
        if len(seed) != 32:
            raise ValueError(f"Private key seed must be 32 bytes, got {len(seed)}.")
        return Ed25519PrivateKey.from_private_bytes(seed)
    except Exception as e:
        raise RuntimeError(f"Invalid FORJA_PRIVATE_KEY_B64: {e}")


_PRIV = _load_private_key()


def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")


def _sign_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    token_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sig = _PRIV.sign(token_bytes)
    return {
        "token": _b64url_encode(token_bytes),
        "sig": _b64url_encode(sig),
        "exp": int(payload.get("exp") or 0),
        "credits": int(payload.get("credits") or 0),
        "plan": payload.get("plan") or "",
    }


def _db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _migrate() -> None:
    ddl_create = """
    CREATE TABLE IF NOT EXISTS licenses (
        id SERIAL PRIMARY KEY,
        license_key TEXT UNIQUE NOT NULL,
        hwid TEXT,
        exp BIGINT NOT NULL,
        credits INT NOT NULL,
        plan TEXT,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    ddl_alter = [
        "ALTER TABLE licenses ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
        "ALTER TABLE licenses ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';",
        "ALTER TABLE licenses ADD COLUMN IF NOT EXISTS plan TEXT;",
        "ALTER TABLE licenses ADD COLUMN IF NOT EXISTS hwid TEXT;",
        "ALTER TABLE licenses ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;",
    ]
    with _db() as con:
        with con.cursor() as cur:
            cur.execute(ddl_create)
            for stmt in ddl_alter:
                cur.execute(stmt)


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
    }
    signed = _sign_payload(payload)
    return JSONResponse({"ok": True, **signed})


def _load_row_for_update(cur, license_key: str) -> Optional[Dict[str, Any]]:
    cur.execute(
        "SELECT license_key, hwid, exp, credits, plan, status FROM licenses WHERE license_key=%s FOR UPDATE",
        (license_key,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def _validate_row(row: Dict[str, Any], hwid: str) -> Optional[str]:
    status = (row.get("status") or "active").lower()
    if status != "active":
        return "blocked"
    if int(row["exp"]) <= _now():
        return "expired"
    if row.get("hwid") and row["hwid"] != hwid:
        return "hwid_mismatch"
    return None


app = FastAPI(title="Forja Viral License Server (PG + Credits) — SSR Admin v2")


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"ok": True, "app": APP_ID, "ts": _now()})


@app.post("/check")
async def check(req: Request) -> JSONResponse:
    try:
        data = await req.json()
    except Exception:
        return _reason("bad_request")

    license_key = str((data or {}).get("license_key") or "").strip()
    hwid = str((data or {}).get("hwid") or "").strip()
    if not license_key or not hwid:
        return _reason("missing_fields")

    try:
        with _db() as con:
            with con.cursor() as cur:
                row = _load_row_for_update(cur, license_key)
                if not row:
                    return _reason("not_found")

                reason = _validate_row(row, hwid)
                if reason:
                    return _reason(reason)

                if not row.get("hwid"):
                    cur.execute(
                        "UPDATE licenses SET hwid=%s, updated_at=NOW() WHERE license_key=%s",
                        (hwid, license_key),
                    )
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
    n = int((data or {}).get("n") or 0)
    if not license_key or not hwid or n <= 0:
        return _reason("missing_fields")

    try:
        with _db() as con:
            with con.cursor() as cur:
                row = _load_row_for_update(cur, license_key)
                if not row:
                    return _reason("not_found")

                reason = _validate_row(row, hwid)
                if reason:
                    return _reason(reason)

                if not row.get("hwid"):
                    cur.execute(
                        "UPDATE licenses SET hwid=%s, updated_at=NOW() WHERE license_key=%s",
                        (hwid, license_key),
                    )
                    row["hwid"] = hwid

                credits = int(row.get("credits") or 0)
                if credits < n:
                    return _reason("no_credits")

                cur.execute(
                    "UPDATE licenses SET credits=credits-%s, updated_at=NOW() WHERE license_key=%s "
                    "RETURNING credits, exp, plan, status",
                    (n, license_key),
                )
                upd = cur.fetchone()
                row["credits"] = int(upd["credits"])
                row["exp"] = int(upd["exp"])
                row["plan"] = upd.get("plan") or ""
                row["status"] = upd.get("status") or "active"

        return _issue_token(row, hwid)
    except Exception as e:
        print("[/consume_n] error:", repr(e))
        return _reason("server_error", detail=str(e))


@app.post("/consume")
async def consume(req: Request) -> JSONResponse:
    # debit exactly 1 (safe fallback)
    try:
        data = await req.json()
    except Exception:
        return _reason("bad_request")
    license_key = str((data or {}).get("license_key") or "").strip()
    hwid = str((data or {}).get("hwid") or "").strip()
    if not license_key or not hwid:
        return _reason("missing_fields")
    # route to consume_n by creating a new local dict
    class _FakeReq:
        async def json(self):
            return {"license_key": license_key, "hwid": hwid, "n": 1}
    return await consume_n(_FakeReq())  # type: ignore


# ----------------------------
# SSR Admin
# ----------------------------
def _fmt_ts(ts: int) -> str:
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(ts)))
    except Exception:
        return str(ts)


def _admin_page_html(token: str, q: str, limit: int, items: list[dict], meta: dict) -> str:
    esc = html.escape
    rows = []
    for it in items:
        lk = esc(str(it.get("license_key") or ""))
        plan = esc(str(it.get("plan") or ""))
        credits = esc(str(it.get("credits") if it.get("credits") is not None else ""))
        exp = esc(_fmt_ts(int(it.get("exp") or 0)))
        hwid = esc(str(it.get("hwid") or ""))
        status = esc(str(it.get("status") or "active"))
        badge = "ok" if status == "active" else "bad"
        rows.append(f"""
        <tr>
          <td class="k">{lk}</td>
          <td>{plan}</td>
          <td><b>{credits}</b></td>
          <td class="k">{exp}</td>
          <td class="k">{hwid}</td>
          <td><span class="badge {badge}">{status}</span></td>
          <td class="actions">
            <form method="post" action="/admin/action?token={esc(token)}">
              <input type="hidden" name="license_key" value="{lk}">
              <input type="hidden" name="action" value="unbind">
              <button class="secondary">Unbind</button>
            </form>
            <form method="post" action="/admin/action?token={esc(token)}">
              <input type="hidden" name="license_key" value="{lk}">
              <input type="hidden" name="action" value="toggle">
              <button class="{ 'danger' if status == 'active' else 'ok' }">{'Bloquear' if status=='active' else 'Ativar'}</button>
            </form>

            <form method="post" action="/admin/action?token={esc(token)}" onsubmit="return confirm('Excluir esta key? Essa ação é permanente.');">
              <input type="hidden" name="license_key" value="{lk}">
              <input type="hidden" name="action" value="delete">
              <button class="danger">Excluir</button>
            </form>
          </td>
        </tr>
        """)

    db = esc(str(meta.get("db") or ""))
    schema = esc(str(meta.get("schema") or ""))
    count = esc(str(meta.get("count") or 0))

    return f"""
<!doctype html>
<html><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Forja Viral — Admin</title>
<style>
:root{{--bg:#0f1115;--panel:#14161b;--text:#e9edf5;--muted:rgba(255,255,255,.7);--border:rgba(255,255,255,.10);
--brand1:#ff5c00;--brand2:#ff004c;--ok:#22c55e;--bad:#ef4444;}}
*{{box-sizing:border-box;}}
body{{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;background:var(--bg);color:var(--text);}}
.wrap{{max-width:1200px;margin:0 auto;padding:22px;}}
.top{{border:1px solid var(--border);background:linear-gradient(135deg,rgba(255,92,0,.18),rgba(255,0,76,.16));
border-radius:18px;padding:18px 16px;display:flex;align-items:center;justify-content:space-between;gap:12px;box-shadow:0 14px 40px rgba(0,0,0,.35);}}
.brand{{display:flex;align-items:center;gap:12px;}}
.mark{{width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,var(--brand1),var(--brand2));
display:flex;align-items:center;justify-content:center;font-weight:900;border:1px solid rgba(255,255,255,.14);}}
h1{{margin:0;font-size:18px;}}
.sub{{color:var(--muted);font-size:13px;margin-top:4px;}}
.chip{{padding:8px 10px;border-radius:999px;border:1px solid var(--border);background:rgba(255,255,255,.05);font-size:12px;font-weight:800;}}
.card{{margin-top:14px;border:1px solid var(--border);background:var(--panel);border-radius:18px;padding:14px;box-shadow:0 10px 28px rgba(0,0,0,.28);}}
input,button{{padding:10px 12px;border-radius:12px;border:1px solid var(--border);background:rgba(255,255,255,.04);color:var(--text);font-size:13px;outline:none;}}
button{{cursor:pointer;font-weight:900;letter-spacing:.2px;background:linear-gradient(135deg,rgba(255,92,0,.22),rgba(255,0,76,.18));}}
button.secondary{{background:rgba(255,255,255,.06);}}
button.ok{{background:rgba(34,197,94,.16);border-color:rgba(34,197,94,.30);}}
button.danger{{background:rgba(239,68,68,.16);border-color:rgba(239,68,68,.35);}}
.row{{display:flex;gap:10px;flex-wrap:wrap;align-items:center;}}
table{{width:100%;border-collapse:collapse;margin-top:12px;}}
th,td{{text-align:left;padding:10px 10px;border-bottom:1px solid rgba(255,255,255,.06);font-size:12px;vertical-align:top;}}
th{{color:rgba(255,255,255,.72);font-weight:900;}}
.k{{font-family:ui-monospace,Menlo,Consolas,monospace;}}
.badge{{display:inline-block;padding:6px 10px;border-radius:999px;border:1px solid rgba(255,255,255,.10);font-weight:900;}}
.badge.ok{{color:var(--ok);}}
.badge.bad{{color:var(--bad);}}
.actions{{display:flex;gap:8px;flex-wrap:wrap;}}
form{{margin:0;}}
hr{{border:0;border-top:1px solid rgba(255,255,255,.08);margin:14px 0;}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="brand">
      <div class="mark">FV</div>
      <div>
        <h1>Forja Viral — Admin</h1>
        <div class="sub">DB: {db} • schema: {schema} • keys: {count}</div>
      </div>
    </div>
    <div class="row">
      <span class="chip">SSR (sem JS)</span>
      <a class="chip" style="text-decoration:none;color:inherit;" href="/admin?token={esc(token)}&q={esc(q)}&limit={limit}">Atualizar</a>
    </div>
  </div>

  <div class="card">
    <form class="row" method="get" action="/admin">
      <input type="hidden" name="token" value="{esc(token)}">
      <input name="q" value="{esc(q)}" placeholder="buscar por key/hwid" style="min-width:280px;">
      <input name="limit" value="{limit}" placeholder="limit" style="width:120px;">
      <button class="secondary" type="submit">Filtrar</button>
    </form>

    <hr>

    <form class="row" method="post" action="/admin/action?token={esc(token)}">
      <input type="hidden" name="action" value="create">
      <input name="license_key" placeholder="license_key" class="k">
      <input name="credits" placeholder="credits" value="60" style="width:120px;">
      <input name="days" placeholder="days" value="30" style="width:120px;">
      <input name="plan" placeholder="plan" value="starter" style="width:160px;">
      <button type="submit">Criar</button>
    </form>

    <form class="row" method="post" action="/admin/action?token={esc(token)}" style="margin-top:10px;">
      <input type="hidden" name="action" value="add_credits">
      <input name="license_key" placeholder="license_key" class="k">
      <input name="add" placeholder="+credits" value="100" style="width:140px;">
      <button class="ok" type="submit">Adicionar créditos</button>
    </form>

    <form class="row" method="post" action="/admin/action?token={esc(token)}" style="margin-top:10px;">
      <input type="hidden" name="action" value="extend_days">
      <input name="license_key" placeholder="license_key" class="k">
      <input name="days" placeholder="+days" value="30" style="width:140px;">
      <button class="secondary" type="submit">Estender expiração</button>
    </form>

    <table>
      <thead><tr>
        <th>license_key</th><th>plan</th><th>credits</th><th>exp</th><th>hwid</th><th>status</th><th>ações</th>
      </tr></thead>
      <tbody>
        {''.join(rows) if rows else '<tr><td colspan="7" style="color:rgba(255,255,255,.7);">Nenhum item encontrado.</td></tr>'}
      </tbody>
    </table>
  </div>
</div>
</body></html>
"""


def _parse_form_bytes(body: bytes) -> Dict[str, str]:
    # x-www-form-urlencoded (no python-multipart dependency)
    try:
        qs = parse_qs(body.decode("utf-8", errors="ignore"), keep_blank_values=True)
        out: Dict[str, str] = {}
        for k, v in qs.items():
            if not v:
                out[k] = ""
            else:
                out[k] = str(v[0])
        return out
    except Exception:
        return {}


@app.get("/admin", response_class=HTMLResponse)
async def admin(req: Request) -> HTMLResponse:
    tok = _require_admin(req)
    q = (req.query_params.get("q") or "").strip().lower()
    limit = int(req.query_params.get("limit") or 500)
    limit = max(1, min(limit, 5000))

    with _db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT current_database() AS db, current_schema() AS schema;")
            info = cur.fetchone() or {}
            cur.execute("SELECT COUNT(*)::int AS count FROM licenses;")
            cnt = cur.fetchone() or {}
            meta = {"db": info.get("db"), "schema": info.get("schema"), "count": cnt.get("count", 0)}

            if q:
                cur.execute(
                    "SELECT license_key, hwid, exp, credits, plan, status FROM licenses "
                    "WHERE lower(license_key) LIKE %s OR lower(coalesce(hwid,'')) LIKE %s "
                    "ORDER BY created_at DESC LIMIT %s",
                    (f"%{q}%", f"%{q}%", limit),
                )
            else:
                cur.execute(
                    "SELECT license_key, hwid, exp, credits, plan, status FROM licenses "
                    "ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
            items = [dict(x) for x in (cur.fetchall() or [])]

    return HTMLResponse(_admin_page_html(tok, q, limit, items, meta))


@app.post("/admin/action")
async def admin_action(req: Request) -> RedirectResponse:
    tok = _require_admin(req)
    body = await req.body()
    form = _parse_form_bytes(body)
    action = str(form.get("action") or "").strip()

    def _redir() -> RedirectResponse:
        return RedirectResponse(url=f"/admin?token={tok}", status_code=303)

    try:
        with _db() as con:
            with con.cursor() as cur:
                if action == "create":
                    lk = str(form.get("license_key") or "").strip()
                    credits = int(form.get("credits") or 0)
                    days = int(form.get("days") or 0)
                    plan = str(form.get("plan") or "custom").strip() or "custom"
                    exp = _now() + (days * 86400)
                    if not lk or credits < 0 or days <= 0:
                        return _redir()
                    cur.execute("SELECT 1 FROM licenses WHERE license_key=%s", (lk,))
                    if cur.fetchone():
                        return _redir()
                    cur.execute(
                        "INSERT INTO licenses (license_key, exp, credits, plan, status) VALUES (%s,%s,%s,%s,'active')",
                        (lk, exp, credits, plan),
                    )

                elif action == "add_credits":
                    lk = str(form.get("license_key") or "").strip()
                    add = int(form.get("add") or 0)
                    if not lk or add == 0:
                        return _redir()
                    cur.execute(
                        "UPDATE licenses SET credits=credits+%s, updated_at=NOW() WHERE license_key=%s",
                        (add, lk),
                    )

                elif action == "extend_days":
                    lk = str(form.get("license_key") or "").strip()
                    days = int(form.get("days") or 0)
                    if not lk or days == 0:
                        return _redir()
                    cur.execute(
                        "UPDATE licenses SET exp=exp+(%s*86400), updated_at=NOW() WHERE license_key=%s",
                        (days, lk),
                    )

                elif action == "unbind":
                    lk = str(form.get("license_key") or "").strip()
                    if not lk:
                        return _redir()
                    cur.execute(
                        "UPDATE licenses SET hwid=NULL, updated_at=NOW() WHERE license_key=%s",
                        (lk,),
                    )

                elif action == "toggle":
                    lk = str(form.get("license_key") or "").strip()
                    if not lk:
                        return _redir()
                    cur.execute("SELECT status FROM licenses WHERE license_key=%s", (lk,))
                    row = cur.fetchone()
                    if not row:
                        return _redir()
                    status = str(row.get("status") or "active").lower()
                    new_status = "blocked" if status == "active" else "active"
                    cur.execute(
                        "UPDATE licenses SET status=%s, updated_at=NOW() WHERE license_key=%s",
                        (new_status, lk),
                    )

                elif action == "delete":
                    lk = str(form.get("license_key") or "").strip()
                    if not lk:
                        return _redir()
                    cur.execute("DELETE FROM licenses WHERE license_key=%s", (lk,))

        return _redir()
    except Exception as e:
        print("[/admin/action] error:", repr(e))
        return _redir()
