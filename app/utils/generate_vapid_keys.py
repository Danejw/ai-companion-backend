from cryptography.hazmat.primitives.asymmetric import ec
import base64

def to_base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

# Generate EC (elliptic curve) private key
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# Export public key in uncompressed form
public_numbers = public_key.public_numbers()
x = public_numbers.x.to_bytes(32, "big")
y = public_numbers.y.to_bytes(32, "big")
uncompressed_key = b"\x04" + x + y

# Encode keys
vapid_public_key = to_base64url(uncompressed_key)
vapid_private_key = to_base64url(
    private_key.private_numbers().private_value.to_bytes(32, "big")
)

print("VAPID_PUBLIC_KEY:", vapid_public_key)
print("VAPID_PRIVATE_KEY:", vapid_private_key)
