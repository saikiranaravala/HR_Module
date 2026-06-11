"""Field-level envelope encryption stub (TECH-7, partial — local scope).

Interface is final; the key provider is not. Locally a static KEK from the
environment wraps per-value data keys (AES-256-GCM). The cloud phase swaps
LocalKeyProvider for a KMS-backed provider without touching callers.
DEV KEK ONLY — never reuse this pattern with a hardcoded key in production.
"""
import base64
import hashlib
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_DEV_KEK_SEED = "meridian-local-dev-kek-not-for-production"


class LocalKeyProvider:
    """KEK from MERIDIAN_LOCAL_KEK (hex, 64 chars) or a derived dev default."""

    def kek(self) -> bytes:
        raw = os.environ.get("MERIDIAN_LOCAL_KEK")
        if raw:
            return bytes.fromhex(raw)
        return hashlib.sha256(_DEV_KEK_SEED.encode()).digest()


def encrypt_field(plaintext: str, provider: LocalKeyProvider | None = None) -> str:
    """Envelope-encrypt one field value → opaque base64 token."""
    provider = provider or LocalKeyProvider()
    dek = AESGCM.generate_key(bit_length=256)
    data_nonce = os.urandom(12)
    ciphertext = AESGCM(dek).encrypt(data_nonce, plaintext.encode(), None)
    kek_nonce = os.urandom(12)
    wrapped_dek = AESGCM(provider.kek()).encrypt(kek_nonce, dek, None)
    envelope = {
        "v": 1,
        "wdek": base64.b64encode(wrapped_dek).decode(),
        "kn": base64.b64encode(kek_nonce).decode(),
        "dn": base64.b64encode(data_nonce).decode(),
        "ct": base64.b64encode(ciphertext).decode(),
    }
    return base64.b64encode(json.dumps(envelope).encode()).decode()


def decrypt_field(token: str, provider: LocalKeyProvider | None = None) -> str:
    provider = provider or LocalKeyProvider()
    envelope = json.loads(base64.b64decode(token))
    if envelope.get("v") != 1:
        raise ValueError("unknown envelope version")
    dek = AESGCM(provider.kek()).decrypt(
        base64.b64decode(envelope["kn"]), base64.b64decode(envelope["wdek"]), None
    )
    plaintext = AESGCM(dek).decrypt(
        base64.b64decode(envelope["dn"]), base64.b64decode(envelope["ct"]), None
    )
    return plaintext.decode()
