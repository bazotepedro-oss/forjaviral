from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import base64

private_key = Ed25519PrivateKey.generate()
private_bytes = private_key.private_bytes_raw()
public_key = private_key.public_key().public_bytes_raw()

print("PRIVATE_KEY_B64:")
print(base64.b64encode(private_bytes).decode())

print("\nPUBLIC_KEY_B64:")
print(base64.b64encode(public_key).decode())
