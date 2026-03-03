"""
Forja Viral — License Client (online check on every app open)

Design:
- Zero-cost server compatible (simple HTTP JSON API)
- Online required: if API is unreachable => NOT licensed (per your requirement)
- 1 PC binding via HWID hash (no raw identifiers stored/sent)
- Token is Ed25519-signed by server; client verifies signature offline (integrity)
- Server still must be reachable on app open to pass (anti-crack)

Expected server endpoints:
POST {base_url}/check
  req: { "license_key": "...", "hwid": "...", "app": "forja-viral", "ver": "x.y.z" }
  resp (success): { "ok": true, "token": "<base64url>", "sig": "<base64url>", "exp": 1735689600 }
  resp (fail):    { "ok": false, "reason": "expired|not_found|hwid_mismatch|banned|server_error" }

Token payload (JSON, bytes) is signed (sig) using Ed25519.
Client verifies (pubkey) and checks token fields match license_key + hwid + exp.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import requests

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except Exception as e:  # pragma: no cover
    Ed25519PublicKey = None  # type: ignore


# =========================
# Config
# =========================

APP_ID = "forja-viral"

# Put your Ed25519 PUBLIC KEY (base64) here (32 bytes).
# Example (placeholder): "M0X3...=="
PUBLIC_KEY_B64 = "tcS+ltV825xY+xAejyE8TSBDok0nfi6YI4lMUws87Mg="

# If you want to rotate keys later, you can add a list of keys and accept any.
PUBLIC_KEYS_B64 = [PUBLIC_KEY_B64]

# Network timeouts (seconds)
HTTP_TIMEOUT = 8

# Store last successful token (optional) — still requires online check every open per policy.
# This is useful for debugging / support.
def _license_store_path() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA", str(Path.home()))
        return Path(base) / "ForjaViral" / "license.json"
    if platform.system().lower() == "darwin":
        return Path.home() / "Library" / "Application Support" / "ForjaViral" / "license.json"
    return Path.home() / ".forja_viral" / "license.json"


# =========================
# HWID (hash)
# =========================

def _read_machine_id_linux() -> str:
    for p in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            if os.path.exists(p):
                return Path(p).read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            pass
    return ""

def _read_registry_machine_guid_windows() -> str:
    # Optional: more stable on Windows. No external deps.
    try:
        import winreg  # type: ignore
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
        val, _ = winreg.QueryValueEx(key, "MachineGuid")
        return str(val).strip()
    except Exception:
        return ""

def compute_hwid_hash() -> str:
    """
    Computes a privacy-preserving HWID hash (sha256 hex).
    Uses multiple stable signals; does NOT send/store raw values.
    """
    sysname = platform.system().lower()
    parts = []

    # Cross-platform signals
    parts.append(sysname)
    parts.append(platform.machine() or "")
    parts.append(platform.processor() or "")
    parts.append(platform.node() or "")  # hostname (can change)
    parts.append(str(uuid.getnode()))    # MAC-ish (can be randomized on some systems)

    if sysname == "windows":
        parts.append(_read_registry_machine_guid_windows())
    elif sysname == "linux":
        parts.append(_read_machine_id_linux())
    elif sysname == "darwin":
        # macOS stable-ish: use platform UUID signals + node
        parts.append(platform.platform() or "")

    # Normalize + hash
    raw = "|".join([p for p in parts if p]).encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()


# =========================
# Token verification
# =========================

def _b64url_decode(s: str) -> bytes:
    s = s.strip().replace("-", "+").replace("_", "/")
    pad = "=" * ((4 - (len(s) % 4)) % 4)
    return base64.b64decode(s + pad)

def _load_public_keys() -> list:
    keys = []
    if Ed25519PublicKey is None:
        return keys
    for k in PUBLIC_KEYS_B64:
        if not k or "REPLACE_ME" in k:
            continue
        try:
            kb = base64.b64decode(k)
            keys.append(Ed25519PublicKey.from_public_bytes(kb))
        except Exception:
            continue
    return keys

def verify_token(token_b64url: str, sig_b64url: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Returns (ok, payload_dict, reason)
    """
    pubkeys = _load_public_keys()
    if not pubkeys:
        return False, None, "public_key_not_configured"

    try:
        token_bytes = _b64url_decode(token_b64url)
        sig_bytes = _b64url_decode(sig_b64url)
    except Exception:
        return False, None, "bad_base64"

    verified = False
    for pk in pubkeys:
        try:
            pk.verify(sig_bytes, token_bytes)
            verified = True
            break
        except Exception:
            continue

    if not verified:
        return False, None, "bad_signature"

    try:
        payload = json.loads(token_bytes.decode("utf-8", errors="strict"))
        if not isinstance(payload, dict):
            return False, None, "bad_payload"
        return True, payload, "ok"
    except Exception:
        return False, None, "bad_payload_json"


# =========================
# Server check
# =========================

@dataclass
class LicenseStatus:
    ok: bool
    reason: str
    exp: int = 0
    payload: Optional[Dict[str, Any]] = None

def check_license_online(
    base_url: str,
    license_key: str,
    hwid: Optional[str] = None,
    app_version: str = "0.0.0",
) -> LicenseStatus:
    """
    Online-required check (per your policy).
    If server unreachable or any error -> returns ok=False.
    """
    base_url = base_url.rstrip("/")
    hwid = hwid or compute_hwid_hash()

    url = f"{base_url}/check"
    body = {
        "license_key": license_key.strip(),
        "hwid": hwid,
        "app": APP_ID,
        "ver": app_version,
        "ts": int(time.time()),
    }

    try:
        r = requests.post(url, json=body, timeout=HTTP_TIMEOUT)
        data = r.json() if r.headers.get("content-type", "").lower().startswith("application/json") else {}
    except Exception:
        return LicenseStatus(ok=False, reason="server_unreachable")

    if not isinstance(data, dict):
        return LicenseStatus(ok=False, reason="bad_server_response")

    if not data.get("ok"):
        return LicenseStatus(ok=False, reason=str(data.get("reason") or "not_ok"))

    token = str(data.get("token") or "")
    sig = str(data.get("sig") or "")
    exp = int(data.get("exp") or 0)

    ok, payload, reason = verify_token(token, sig)
    if not ok or not payload:
        return LicenseStatus(ok=False, reason=reason)

    # Validate payload content
    if payload.get("license_key") != license_key.strip():
        return LicenseStatus(ok=False, reason="token_mismatch_license")
    if payload.get("hwid") != hwid:
        return LicenseStatus(ok=False, reason="token_mismatch_hwid")

    exp_payload = int(payload.get("exp") or 0)
    if exp_payload <= int(time.time()):
        return LicenseStatus(ok=False, reason="expired", exp=exp_payload, payload=payload)

    # Server exp must align with payload exp
    if exp and exp != exp_payload:
        # Not fatal, but indicates mismatch; keep payload as source of truth
        pass

    # Save last token (debug/support). Still requires online check every open.
    try:
        p = _license_store_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"token": token, "sig": sig, "payload": payload}, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    return LicenseStatus(ok=True, reason="ok", exp=exp_payload, payload=payload)


# =========================
# Minimal helper for UI gating
# =========================

def must_block_generation(status: LicenseStatus) -> bool:
    """
    Your policy: if not OK => block Generate/Export.
    """
    return not bool(status.ok)


# =========================
# CLI quick test
# =========================

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True, help="e.g. https://license.yourdomain.com")
    ap.add_argument("--license-key", required=True, help="Your license key")
    ap.add_argument("--ver", default="0.0.0")
    args = ap.parse_args()

    hwid = compute_hwid_hash()
    print("HWID:", hwid)

    st = check_license_online(args.base_url, args.license_key, hwid=hwid, app_version=args.ver)
    print("OK:", st.ok)
    print("Reason:", st.reason)
    if st.payload:
        print("Exp:", st.payload.get("exp"))
        print("Plan:", st.payload.get("plan"))
