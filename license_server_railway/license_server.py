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
from contextlib import contextmanager
import html
import hmac
import json
import os
import time
import re
from typing import Any, Dict, Optional
from urllib.parse import parse_qs

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

APP_ID = os.environ.get("APP_ID", "forja-viral").strip()
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "").strip()
PRIVATE_KEY_B64 = os.environ.get("FORJA_PRIVATE_KEY_B64", "").strip()
DEBUG_ERRORS = (os.environ.get("DEBUG_ERRORS", "0").strip() == "1")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL env var missing (postgres connection string).")
if len(ADMIN_TOKEN) < 32:
    raise RuntimeError("ADMIN_TOKEN must be configured with at least 32 characters.")


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


_DB_POOL_MAX = max(2, min(int(os.environ.get("DB_POOL_MAX", "10")), 30))
_DB_POOL = ThreadedConnectionPool(
    1,
    _DB_POOL_MAX,
    DATABASE_URL,
    cursor_factory=psycopg2.extras.RealDictCursor,
    connect_timeout=5,
    options="-c statement_timeout=8000 -c lock_timeout=5000",
    application_name="forja-license-api",
)


@contextmanager
def _db():
    con = _DB_POOL.getconn()
    try:
        with con:
            yield con
    finally:
        _DB_POOL.putconn(con, close=bool(con.closed))


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
        "DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='licenses_credits_nonnegative') THEN ALTER TABLE licenses ADD CONSTRAINT licenses_credits_nonnegative CHECK (credits >= 0) NOT VALID; END IF; END $$;",
        "CREATE TABLE IF NOT EXISTS license_creation_operations (operation_id TEXT PRIMARY KEY, license_key TEXT UNIQUE NOT NULL, credits INT NOT NULL CHECK (credits >= 0), days INT NOT NULL CHECK (days > 0), plan TEXT NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);",
        "CREATE TABLE IF NOT EXISTS credit_operations (operation_id TEXT PRIMARY KEY, license_key TEXT NOT NULL, amount INT NOT NULL CHECK (amount > 0), credits_after INT NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);",
        "CREATE INDEX IF NOT EXISTS credit_operations_license_idx ON credit_operations (license_key, created_at);",
        "CREATE TABLE IF NOT EXISTS consumption_operations (operation_id TEXT PRIMARY KEY, license_key TEXT NOT NULL, amount INT NOT NULL CHECK (amount > 0), refunded INT NOT NULL DEFAULT 0 CHECK (refunded >= 0), credits_after INT NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);",
        "ALTER TABLE consumption_operations ADD COLUMN IF NOT EXISTS refunded INT NOT NULL DEFAULT 0 CHECK (refunded >= 0);",
        "CREATE INDEX IF NOT EXISTS consumption_operations_license_idx ON consumption_operations (license_key, created_at);",
        "CREATE TABLE IF NOT EXISTS refund_operations (refund_operation_id TEXT PRIMARY KEY, operation_id TEXT NOT NULL, license_key TEXT NOT NULL, amount INT NOT NULL CHECK (amount > 0), credits_after INT NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);",
    ]
    with _db() as con:
        with con.cursor() as cur:
            cur.execute(ddl_create)
            for stmt in ddl_alter:
                cur.execute(stmt)


_migrate()


def _require_admin(req: Request) -> str:
    tok = req.headers.get("x-admin-token") or ""
    if not hmac.compare_digest(tok, ADMIN_TOKEN):
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


@app.on_event("shutdown")
def _close_db_pool() -> None:
    _DB_POOL.closeall()


@app.get("/health")
def health() -> JSONResponse:
    try:
        with _db() as con:
            with con.cursor() as cur:
                cur.execute("SELECT 1")
        return JSONResponse({"ok": True, "app": APP_ID, "ts": _now()})
    except Exception:
        return JSONResponse({"ok": False, "app": APP_ID, "reason": "database_unavailable"}, status_code=503)


@app.post("/check")
def check(data: Dict[str, Any]) -> JSONResponse:
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
def activate(data: Dict[str, Any]) -> JSONResponse:
    return check(data)


@app.post("/api/license/check")
def api_license_check(data: Dict[str, Any]) -> JSONResponse:
    return check(data)


@app.post("/consume_n")
def consume_n(data: Dict[str, Any], idempotency_key: Optional[str] = Header(default=None)) -> JSONResponse:
    license_key = str((data or {}).get("license_key") or "").strip()
    hwid = str((data or {}).get("hwid") or "").strip()
    operation_id = str((data or {}).get("operation_id") or idempotency_key or "").strip()
    try:
        n = int((data or {}).get("n") or 0)
    except (TypeError, ValueError):
        return _reason("bad_request")
    if not license_key or not hwid or not operation_id or n <= 0 or n > 5000:
        return _reason("missing_fields")
    if len(operation_id) > 128 or not re.fullmatch(r"[A-Za-z0-9._:-]+", operation_id):
        return _reason("bad_request")

    try:
        with _db() as con:
            with con.cursor() as cur:
                row = _load_row_for_update(cur, license_key)
                if not row:
                    return _reason("not_found")

                reason = _validate_row(row, hwid)
                if reason:
                    return _reason(reason)

                cur.execute(
                    "SELECT license_key, amount FROM consumption_operations WHERE operation_id=%s",
                    (operation_id,),
                )
                previous = cur.fetchone()
                if previous:
                    if previous["license_key"] != license_key or int(previous["amount"]) != n:
                        return _reason("idempotency_conflict")
                    return _issue_token(row, hwid)

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
                cur.execute(
                    "INSERT INTO consumption_operations (operation_id, license_key, amount, credits_after) VALUES (%s,%s,%s,%s)",
                    (operation_id, license_key, n, row["credits"]),
                )

        return _issue_token(row, hwid)
    except Exception as e:
        print("[/consume_n] error:", repr(e))
        return _reason("server_error", detail=str(e))


@app.post("/refund_n")
def refund_n(data: Dict[str, Any], idempotency_key: Optional[str] = Header(default=None)) -> JSONResponse:
    license_key = str((data or {}).get("license_key") or "").strip()
    hwid = str((data or {}).get("hwid") or "").strip()
    operation_id = str((data or {}).get("operation_id") or "").strip()
    refund_operation_id = str((data or {}).get("refund_operation_id") or idempotency_key or "").strip()
    try:
        n = int((data or {}).get("n") or 0)
    except (TypeError, ValueError):
        return _reason("bad_request")
    if not license_key or not hwid or not operation_id or not refund_operation_id or n <= 0 or n > 5000:
        return _reason("missing_fields")
    if any(len(value) > 128 or not re.fullmatch(r"[A-Za-z0-9._:-]+", value) for value in (operation_id, refund_operation_id)):
        return _reason("bad_request")

    try:
        with _db() as con:
            with con.cursor() as cur:
                row = _load_row_for_update(cur, license_key)
                if not row:
                    return _reason("not_found")
                # A refund is settlement of an already accepted debit; it remains valid
                # if the license expires or is blocked while local rendering is running.
                if row.get("hwid") and row["hwid"] != hwid:
                    return _reason("hwid_mismatch")

                cur.execute(
                    "SELECT operation_id, license_key, amount, refunded FROM consumption_operations WHERE operation_id=%s FOR UPDATE",
                    (operation_id,),
                )
                debit = cur.fetchone()
                if not debit or debit["license_key"] != license_key:
                    return _reason("debit_not_found")

                cur.execute(
                    "SELECT operation_id, license_key, amount FROM refund_operations WHERE refund_operation_id=%s",
                    (refund_operation_id,),
                )
                prior_refund = cur.fetchone()
                if prior_refund:
                    if (prior_refund["operation_id"] != operation_id or
                            prior_refund["license_key"] != license_key or int(prior_refund["amount"]) != n):
                        return _reason("idempotency_conflict")
                    return _issue_token(row, hwid)

                if int(debit["refunded"]) + n > int(debit["amount"]):
                    return _reason("refund_exceeds_debit")

                cur.execute(
                    "UPDATE licenses SET credits=credits+%s, updated_at=NOW() WHERE license_key=%s RETURNING credits",
                    (n, license_key),
                )
                row["credits"] = int(cur.fetchone()["credits"])
                cur.execute(
                    "UPDATE consumption_operations SET refunded=refunded+%s WHERE operation_id=%s",
                    (n, operation_id),
                )
                cur.execute(
                    "INSERT INTO refund_operations (refund_operation_id, operation_id, license_key, amount, credits_after) VALUES (%s,%s,%s,%s,%s)",
                    (refund_operation_id, operation_id, license_key, n, row["credits"]),
                )
        return _issue_token(row, hwid)
    except Exception as e:
        print("[/refund_n] error:", repr(e))
        return _reason("server_error", detail=str(e))


@app.post("/consume")
def consume(data: Dict[str, Any], idempotency_key: Optional[str] = Header(default=None)) -> JSONResponse:
    # debit exactly 1 (safe fallback)
    license_key = str((data or {}).get("license_key") or "").strip()
    hwid = str((data or {}).get("hwid") or "").strip()
    if not license_key or not hwid:
        return _reason("missing_fields")
    # route to consume_n by creating a new local dict
    operation_id = idempotency_key or str((data or {}).get("operation_id") or "")
    if not operation_id:
        return _reason("missing_idempotency_key")
    return consume_n({"license_key": license_key, "hwid": hwid, "n": 1, "operation_id": operation_id}, operation_id)


@app.post("/api/license/consume")
def api_license_consume(data: Dict[str, Any], idempotency_key: Optional[str] = Header(default=None)) -> JSONResponse:
    return consume_n(data, idempotency_key)


@app.post("/api/license/refund")
def api_license_refund(data: Dict[str, Any], idempotency_key: Optional[str] = Header(default=None)) -> JSONResponse:
    return refund_n(data, idempotency_key)


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


@app.get("/admin/api/licenses")
async def admin_api_licenses(req: Request) -> JSONResponse:
    tok = _require_admin(req)
    q = (req.query_params.get("q") or "").strip().lower()
    limit = int(req.query_params.get("limit") or 1000)

    with _db() as con:
        with con.cursor() as cur:
            if q:
                cur.execute(
                    "SELECT license_key, hwid, exp, credits, plan, status, created_at, updated_at FROM licenses "
                    "WHERE lower(license_key) LIKE %s OR lower(coalesce(hwid,'')) LIKE %s "
                    "ORDER BY created_at DESC LIMIT %s",
                    (f"%{q}%", f"%{q}%", limit),
                )
            else:
                cur.execute(
                    "SELECT license_key, hwid, exp, credits, plan, status, created_at, updated_at FROM licenses "
                    "ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
            rows = [dict(x) for x in (cur.fetchall() or [])]
            for r in rows:
                if r.get("created_at"):
                    r["created_at"] = str(r["created_at"])
                if r.get("updated_at"):
                    r["updated_at"] = str(r["updated_at"])

    return JSONResponse({"ok": True, "licenses": rows})


@app.post("/admin/api/credits/add")
def admin_add_credits(data: Dict[str, Any], req: Request) -> JSONResponse:
    _require_admin(req)
    try:
        form = data
        license_key = str(form.get("license_key") or "").strip()
        operation_id = str(form.get("operation_id") or req.headers.get("Idempotency-Key") or "").strip()
        amount = int(form.get("add") or 0)
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "reason": "bad_request"}, status_code=400)

    if not license_key or not operation_id or amount <= 0 or amount > 5000:
        return JSONResponse({"ok": False, "reason": "invalid_fields"}, status_code=400)
    if len(operation_id) > 128 or not re.fullmatch(r"[A-Za-z0-9._:-]+", operation_id):
        return JSONResponse({"ok": False, "reason": "bad_operation_id"}, status_code=400)

    try:
        with _db() as con:
            with con.cursor() as cur:
                cur.execute(
                    "SELECT license_key, amount, credits_after FROM credit_operations WHERE operation_id=%s",
                    (operation_id,),
                )
                previous = cur.fetchone()
                if previous:
                    if previous["license_key"] != license_key or int(previous["amount"]) != amount:
                        return JSONResponse({"ok": False, "reason": "idempotency_conflict"}, status_code=409)
                    return JSONResponse({
                        "ok": True,
                        "duplicate": True,
                        "credits": int(previous["credits_after"]),
                    })

                cur.execute(
                    "SELECT license_key FROM licenses WHERE license_key=%s FOR UPDATE",
                    (license_key,),
                )
                if not cur.fetchone():
                    return JSONResponse({"ok": False, "reason": "not_found"}, status_code=404)

                cur.execute(
                    "UPDATE licenses SET credits=credits+%s, updated_at=NOW() WHERE license_key=%s RETURNING credits",
                    (amount, license_key),
                )
                updated = cur.fetchone()
                credits_after = int(updated["credits"])
                cur.execute(
                    "INSERT INTO credit_operations (operation_id, license_key, amount, credits_after) VALUES (%s,%s,%s,%s)",
                    (operation_id, license_key, amount, credits_after),
                )
        return JSONResponse({"ok": True, "duplicate": False, "credits": credits_after})
    except Exception as e:
        print("[/admin/api/credits/add] error:", repr(e))
        return JSONResponse({"ok": False, "reason": "server_error"}, status_code=500)


@app.post("/admin/api/licenses/create")
def admin_create_license(data: Dict[str, Any], req: Request) -> JSONResponse:
    _require_admin(req)
    try:
        operation_id = str(data.get("operation_id") or "").strip()
        license_key = str(data.get("license_key") or "").strip().upper()
        credits = int(data.get("credits") or 0)
        days = int(data.get("days") or 0)
        plan = str(data.get("plan") or "custom").strip() or "custom"
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "reason": "bad_request"}, status_code=400)

    if (not operation_id or len(operation_id) > 128 or
            not re.fullmatch(r"[A-Za-z0-9._:-]+", operation_id) or
            not license_key or len(license_key) > 80 or credits < 0 or credits > 1_000_000 or
            days <= 0 or days > 3650):
        return JSONResponse({"ok": False, "reason": "invalid_fields"}, status_code=400)

    try:
        with _db() as con:
            with con.cursor() as cur:
                cur.execute(
                    "SELECT operation_id, license_key, credits, days, plan FROM license_creation_operations WHERE operation_id=%s",
                    (operation_id,),
                )
                previous = cur.fetchone()
                if previous:
                    same_request = (
                        previous["license_key"] == license_key and
                        int(previous["credits"]) == credits and
                        int(previous["days"]) == days and
                        previous["plan"] == plan
                    )
                    if not same_request:
                        return JSONResponse({"ok": False, "reason": "idempotency_conflict"}, status_code=409)
                    return JSONResponse({"ok": True, "duplicate": True, "license_key": license_key})

                cur.execute("SELECT 1 FROM licenses WHERE license_key=%s FOR UPDATE", (license_key,))
                if cur.fetchone():
                    return JSONResponse({"ok": False, "reason": "license_key_exists"}, status_code=409)

                exp = _now() + days * 86400
                cur.execute(
                    "INSERT INTO licenses (license_key, exp, credits, plan, status) VALUES (%s,%s,%s,%s,'active')",
                    (license_key, exp, credits, plan),
                )
                # Remove registros de operacao orfaos de uma chave que foi apagada
                # anteriormente; sem isso o UNIQUE(license_key) impede recria-la.
                cur.execute("DELETE FROM license_creation_operations WHERE license_key=%s", (license_key,))
                cur.execute(
                    "INSERT INTO license_creation_operations (operation_id, license_key, credits, days, plan) VALUES (%s,%s,%s,%s,%s)",
                    (operation_id, license_key, credits, days, plan),
                )
        return JSONResponse({"ok": True, "duplicate": False, "license_key": license_key})
    except Exception as e:
        print("[/admin/api/licenses/create] error:", repr(e))
        return JSONResponse({"ok": False, "reason": "server_error"}, status_code=500)


@app.post("/admin/action")
async def admin_action(req: Request):
    tok = _require_admin(req)
    body = await req.body()
    form = _parse_form_bytes(body)
    action = str(form.get("action") or "").strip()

    def _redir(success: bool = False):
        if "application/json" in req.headers.get("accept", "") or req.headers.get("x-admin-token"):
            return JSONResponse({"ok": success}, status_code=200 if success else 400)
        return RedirectResponse(url="/admin", status_code=303)

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
                        # Idempotent create retry: never fail a retried fulfillment silently.
                        return _redir(True)
                    cur.execute(
                        "INSERT INTO licenses (license_key, exp, credits, plan, status) VALUES (%s,%s,%s,%s,'active')",
                        (lk, exp, credits, plan),
                    )

                elif action == "add_credits":
                    lk = str(form.get("license_key") or "").strip()
                    add = int(form.get("add") or 0)
                    if not lk or add <= 0:
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

        return _redir(True)
    except Exception as e:
        print("[/admin/action] error:", repr(e))
        return _redir()
