"""Destructive integration smoke test; only permits explicit local test servers."""
from __future__ import annotations

import os
import secrets
import json
import base64
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


BASE_URL = os.environ.get("FORJA_TEST_SERVER_URL", "").rstrip("/")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
PUBLIC_KEY_B64 = os.environ.get("FORJA_PUBLIC_KEY_B64", "")
ALLOW = os.environ.get("ALLOW_LICENSE_MUTATION_TESTS") == "YES"


def main() -> None:
    host = urlparse(BASE_URL).hostname
    if not ALLOW or host not in {"localhost", "127.0.0.1", "::1"}:
        raise SystemExit("Set FORJA_TEST_SERVER_URL to localhost and ALLOW_LICENSE_MUTATION_TESTS=YES")
    if len(ADMIN_TOKEN) < 32:
        raise SystemExit("Set the test server's ADMIN_TOKEN (at least 32 characters)")
    if not PUBLIC_KEY_B64:
        raise SystemExit("Set the staging FORJA_PUBLIC_KEY_B64 to verify signed license tokens")

    repo_root = Path(__file__).resolve().parents[2]
    for relative in ("scripts/license_client.py", "webui/license_client.py", "forja-license-main/license_client.py"):
        source = (repo_root / relative).read_text(encoding="utf-8")
        match = re.search(r'^PUBLIC_KEY_B64\s*=\s*["\']([^"\']+)["\']', source, re.MULTILINE)
        assert match and match.group(1) == PUBLIC_KEY_B64, f"Client public key mismatch in {relative}"

    suffix = secrets.token_hex(5).upper()
    license_key = f"FC-TST-{suffix}"
    hwid = secrets.token_hex(32)
    headers = {"x-admin-token": ADMIN_TOKEN}
    create_op = f"test-create-{suffix}"
    common = {"license_key": license_key, "hwid": hwid}

    def post(path: str, body: dict, request_headers: dict[str, str], form: bool = False) -> dict:
        payload = (
            "&".join(f"{key}={value}" for key, value in body.items()).encode("utf-8")
            if form else json.dumps(body).encode("utf-8")
        )
        headers_for_request = dict(request_headers)
        headers_for_request["Content-Type"] = "application/x-www-form-urlencoded" if form else "application/json"
        request = Request(f"{BASE_URL}{path}", data=payload, headers=headers_for_request, method="POST")
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    create_body = {
        "license_key": license_key,
        "credits": 1,
        "days": 1,
        "plan": "concurrency-smoke",
        "operation_id": create_op,
    }
    created = post(
        "/admin/api/licenses/create",
        create_body,
        headers,
    )
    assert created.get("ok") is True, created
    created_retry = post("/admin/api/licenses/create", create_body, headers)
    assert created_retry.get("duplicate") is True, created_retry

    operations = [f"test-consume-a-{suffix}", f"test-consume-b-{suffix}"]

    def consume(operation_id: str) -> dict:
        return post(
            "/api/license/consume",
            {**common, "n": 1, "operation_id": operation_id},
            {"Idempotency-Key": operation_id},
        )

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(consume, operations))
        assert sum(bool(result.get("ok")) for result in results) == 1, results
        winner = operations[0] if results[0].get("ok") else operations[1]
        assert consume(winner).get("ok") is True, "Retrying the winning operation charged twice or failed"

        refund_id = f"test-refund-{suffix}"
        refund_body = {
            **common,
            "operation_id": winner,
            "refund_operation_id": refund_id,
            "n": 1,
        }
        first_refund = post("/api/license/refund", refund_body, {"Idempotency-Key": refund_id})
        second_refund = post("/api/license/refund", refund_body, {"Idempotency-Key": refund_id})
        assert first_refund.get("ok") and second_refund.get("ok"), (first_refund, second_refund)
        assert first_refund.get("credits") == second_refund.get("credits") == 1

        over_refund = post(
            "/api/license/refund",
            {**refund_body, "refund_operation_id": f"test-refund-extra-{suffix}"},
            {"Idempotency-Key": f"test-refund-extra-{suffix}"},
        )
        assert over_refund.get("reason") == "refund_exceeds_debit", over_refund

        credit_operation_id = f"test-credit-{suffix}"
        credit_body = {"license_key": license_key, "add": 1, "operation_id": credit_operation_id}
        first_credit = post(
            "/admin/api/credits/add",
            credit_body,
            {**headers, "Idempotency-Key": credit_operation_id},
        )
        second_credit = post(
            "/admin/api/credits/add",
            credit_body,
            {**headers, "Idempotency-Key": credit_operation_id},
        )
        assert first_credit.get("credits") == second_credit.get("credits") == 2, (first_credit, second_credit)

        checked = post("/api/license/check", common, {})
        token = str(checked.get("token") or "")
        signature = str(checked.get("sig") or "")
        token_bytes = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        signature_bytes = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBLIC_KEY_B64))
        public_key.verify(signature_bytes, token_bytes)
        signed_payload = json.loads(token_bytes.decode("utf-8"))
        assert checked.get("ok") and signed_payload.get("hwid") == hwid
        assert signed_payload.get("credits") == 2 and signed_payload.get("status") == "active"
        print("PASS: concurrent debit, create/credit/refund idempotency, refund cap, and Ed25519 token verification")
    finally:
        post(
            "/admin/action",
            {"action": "delete", "license_key": license_key},
            {**headers, "Accept": "application/json"},
            form=True,
        )


if __name__ == "__main__":
    main()
