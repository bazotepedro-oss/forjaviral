"""
Forja Viral — License Gate (Simple & Reliable)

Behavior (as you asked):
- Before processing, check current credits from server
- If credits >= required_n: debit required_n (atomically) and allow run
- Else: raise "Sem créditos" and block
- UI always opens; only Generate/Export blocked by gate wrappers

This is *prepay* by requested amount (segments/clips asked), not by actual outputs.
It's the simplest model and prevents "run with 3 credits to generate 4 clips".
"""

from __future__ import annotations

import inspect
import json
import os
import platform
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

import requests

try:
    import gradio as gr
except Exception:  # pragma: no cover
    gr = None  # type: ignore

try:
    from webui.license_client import check_license_online, compute_hwid_hash, verify_token
except Exception:
    from license_client import check_license_online, compute_hwid_hash, verify_token

HTTP_TIMEOUT = 10


def _store_path() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA", str(Path.home()))
        return Path(base) / "ForjaViral" / "license_settings.json"
    if platform.system().lower() == "darwin":
        return Path.home() / "Library" / "Application Support" / "ForjaViral" / "license_settings.json"
    return Path.home() / ".forja_viral" / "license_settings.json"


@dataclass
class GateState:
    ok: bool = False
    reason: str = "not_checked"
    exp: int = 0
    credits: int = 0
    checked_at: int = 0
    hwid: str = ""
    payload: Optional[Dict[str, Any]] = None


class LicenseGate:
    def __init__(self, base_url: str, app_version: str = "0.0.0") -> None:
        self.base_url = (base_url or "").strip()
        self.app_version = app_version
        self.license_key: str = ""
        self.hwid: str = compute_hwid_hash()
        self.state = GateState(hwid=self.hwid)

    # ---- persistence ----
    def load_local(self) -> None:
        p = _store_path()
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.base_url = str(data.get("base_url") or self.base_url).strip()
                    self.license_key = str(data.get("license_key") or "").strip()
        except Exception:
            pass

    def save_local(self) -> None:
        p = _store_path()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(
                json.dumps({"base_url": self.base_url, "license_key": self.license_key}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    # ---- check ----
    def check_now(self) -> GateState:
        if not self.base_url:
            self.state = GateState(ok=False, reason="missing_base_url", hwid=self.hwid, checked_at=int(time.time()))
            return self.state
        if not self.license_key:
            self.state = GateState(ok=False, reason="missing_license_key", hwid=self.hwid, checked_at=int(time.time()))
            return self.state

        st = check_license_online(
            base_url=self.base_url,
            license_key=self.license_key,
            hwid=self.hwid,
            app_version=self.app_version,
        )

        credits = 0
        if st.payload and isinstance(st.payload, dict):
            credits = int(st.payload.get("credits") or 0)

        self.state = GateState(
            ok=bool(st.ok),
            reason=str(st.reason),
            exp=int(st.exp or 0),
            credits=credits,
            checked_at=int(time.time()),
            hwid=self.hwid,
            payload=st.payload,
        )
        return self.state

    def check_on_start(self) -> GateState:
        # online check on every open
        return self.check_now()

    # ---- token update helper ----
    def _update_from_signed(self, data: Dict[str, Any]) -> bool:
        token = str(data.get("token") or "")
        sig = str(data.get("sig") or "")
        ok, payload, reason = verify_token(token, sig)
        if not ok or not payload:
            self.state.ok = False
            self.state.reason = reason
            return False

        if payload.get("license_key") != self.license_key.strip():
            self.state.ok = False
            self.state.reason = "token_mismatch_license"
            return False
        if payload.get("hwid") != self.hwid:
            self.state.ok = False
            self.state.reason = "token_mismatch_hwid"
            return False

        exp_payload = int(payload.get("exp") or 0)
        if exp_payload <= int(time.time()):
            self.state.ok = False
            self.state.reason = "expired"
            self.state.exp = exp_payload
            self.state.payload = payload
            self.state.credits = int(payload.get("credits") or 0)
            return False

        self.state.ok = True
        self.state.reason = "ok"
        self.state.exp = exp_payload
        self.state.payload = payload
        self.state.credits = int(payload.get("credits") or 0)
        self.state.checked_at = int(time.time())
        return True

    # ---- debit N credits (prepay) ----
    def consume_n(self, n: int) -> bool:
        """
        Atomically debit N credits via /consume_n.
        Requires server endpoint /consume_n.
        """
        if n <= 0:
            return True
        if not self.base_url or not self.license_key:
            self.state.ok = False
            self.state.reason = "missing_fields"
            return False

        url = self.base_url.rstrip("/") + "/consume_n"
        body = {"license_key": self.license_key.strip(), "hwid": self.hwid, "n": int(n)}
        try:
            r = requests.post(url, json=body, timeout=HTTP_TIMEOUT)
            data = r.json() if r.headers.get("content-type", "").lower().startswith("application/json") else {}
        except Exception:
            self.state.ok = False
            self.state.reason = "server_unreachable"
            return False

        if not isinstance(data, dict) or not data.get("ok"):
            self.state.ok = False
            self.state.reason = str((data or {}).get("reason") or "not_ok")
            return False

        return self._update_from_signed(data)

    # ---- display helpers ----
    def is_ok(self) -> bool:
        return bool(self.state.ok)

    def _fmt_exp(self, exp: int) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(exp)) if exp else "-"

    def status_text(self) -> str:
        if self.state.ok:
            plan = ""
            if isinstance(self.state.payload, dict):
                plan = str(self.state.payload.get("plan") or "")
            return f"✅ Licença ativa ({plan or 'plan'}) • créditos: {self.state.credits} • expira em {self._fmt_exp(self.state.exp)}"

        m = {
            "missing_license_key": "Cole sua chave de licença para ativar.",
            "missing_base_url": "Servidor de licença não configurado.",
            "server_unreachable": "Sem conexão com o servidor de licença. (online obrigatório)",
            "expired": "Licença expirada. Renove para continuar.",
            "not_found": "Chave inválida.",
            "hwid_mismatch": "Chave já está ativada em outro PC.",
            "blocked": "Licença bloqueada.",
            "bad_signature": "Assinatura inválida (servidor/app com chaves diferentes).",
            "no_credits": "Sem créditos. Recarregue para continuar.",
            "server_error": "Erro no servidor de licença. Tente novamente.",
        }
        return "⛔ " + m.get(self.state.reason, f"Bloqueado: {self.state.reason}")

    def set_license_key(self, k: str) -> None:
        self.license_key = (k or "").strip()
        self.save_local()

    def set_base_url(self, url: str) -> None:
        self.base_url = (url or "").strip()
        self.save_local()

    def _raise_block(self) -> None:
        msg = self.status_text()
        if gr is not None:
            raise gr.Error(msg)
        raise RuntimeError(msg)

    # ---- wrapper: precheck + prepay ----
    def require_precheck_and_prepay(self, fn: Callable[..., Any], required_n_getter: Callable[[Tuple[Any, ...], Dict[str, Any]], int]) -> Callable[..., Any]:
        """
        - Online check must be OK
        - Determine required credits (segments asked)
        - If credits < required: block
        - Else: debit required credits via /consume_n and run fn
        Supports generator functions (yield).
        """
        if inspect.isgeneratorfunction(fn):
            def _wrapped(*args: Any, **kwargs: Any):
                self.check_now()
                if not self.is_ok():
                    self._raise_block()

                required = int(required_n_getter(args, kwargs) or 0)
                if required < 1:
                    required = 1

                if int(self.state.credits or 0) < required:
                    self.state.ok = False
                    self.state.reason = "no_credits"
                    self._raise_block()

                ok = self.consume_n(required)
                if not ok:
                    self._raise_block()

                yield from fn(*args, **kwargs)
            return _wrapped

        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            self.check_now()
            if not self.is_ok():
                self._raise_block()

            required = int(required_n_getter(args, kwargs) or 0)
            if required < 1:
                required = 1

            if int(self.state.credits or 0) < required:
                self.state.ok = False
                self.state.reason = "no_credits"
                self._raise_block()

            ok = self.consume_n(required)
            if not ok:
                self._raise_block()

            return fn(*args, **kwargs)

        return _wrapped

    # ---- UI block ----
    def ui_block(self) -> Tuple[Any, Any, Any, Any]:
        if gr is None:
            return None, None, None, None  # type: ignore

        status_md = gr.Markdown(self.status_text())

        with gr.Row():
            base_url_txt = gr.Textbox(
                label="Servidor de licença",
                value=self.base_url,
                placeholder="http://127.0.0.1:8787",
                scale=2,
            )
            license_key_txt = gr.Textbox(
                label="Chave de licença",
                value=self.license_key,
                placeholder="FV-XXXX-XX",
                scale=2,
            )

        check_btn = gr.Button("Verificar / Ativar", variant="primary")

        def _do_check(url: str, key: str) -> str:
            self.set_base_url(url)
            self.set_license_key(key)
            self.check_now()
            return self.status_text()

        check_btn.click(fn=_do_check, inputs=[base_url_txt, license_key_txt], outputs=[status_md])
        return status_md, base_url_txt, license_key_txt, check_btn
