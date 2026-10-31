"""
Derive PUBLIC_KEY_B64 from your server PRIVATE_KEY_B64 (Ed25519 seed).

Use this when client shows: Reason: bad_signature

Run (Windows CMD) in the SAME environment where you start the server:

1) If your start_server.bat sets FORJA_PRIVATE_KEY_B64, then:
   python derive_public_from_private.py

2) Or pass it explicitly:
   python derive_public_from_private.py --private-b64 YOUR_PRIVATE_B64

It prints PUBLIC_KEY_B64 you must paste into Forja Viral's license_client.py.
"""

import argparse
import base64
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--private-b64", default=None, help="Ed25519 private seed (32 bytes) base64")
    args = ap.parse_args()

    priv_b64 = args.private_b64
    if not priv_b64:
        import os
        priv_b64 = os.environ.get("FORJA_PRIVATE_KEY_B64", "")

    if not priv_b64:
        raise SystemExit("Missing private key. Provide --private-b64 or set FORJA_PRIVATE_KEY_B64.")

    try:
        seed = base64.b64decode(priv_b64)
    except Exception as e:
        raise SystemExit(f"Invalid base64 private key: {e}")

    if len(seed) != 32:
        raise SystemExit(f"Private seed must be 32 bytes, got {len(seed)} bytes.")

    priv = Ed25519PrivateKey.from_private_bytes(seed)
    pub = priv.public_key().public_bytes_raw()
    pub_b64 = base64.b64encode(pub).decode("utf-8")

    print("\nPUBLIC_KEY_B64 (paste into license_client.py):")
    print(pub_b64)
    print("\nDone.")


if __name__ == "__main__":
    main()
