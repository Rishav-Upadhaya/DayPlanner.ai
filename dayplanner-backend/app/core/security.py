from datetime import datetime, timedelta, timezone
import base64
import hashlib
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

ALGORITHM = 'HS256'
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def create_access_token(subject: str, expires_delta_minutes: int | None = None) -> str:
    settings = get_settings()
    minutes = expires_delta_minutes or settings.app_access_token_expire_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    payload: dict[str, Any] = {'sub': subject, 'exp': expire}
    return jwt.encode(payload, settings.app_secret_key, algorithm=ALGORITHM)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def _get_aes_key() -> bytes:
    raw_key = get_settings().encryption_key.strip()
    if not raw_key:
        return bytes.fromhex('0' * 64)

    try:
        if len(raw_key) >= 64:
            return bytes.fromhex(raw_key[:64])
    except ValueError:
        pass

    try:
        decoded = base64.b64decode(raw_key.encode(), validate=True)
        if len(decoded) in {16, 24, 32}:
            return decoded
        if len(decoded) > 32:
            return decoded[:32]
    except Exception:
        pass

    raw_bytes = raw_key.encode()
    if len(raw_bytes) in {16, 24, 32}:
        return raw_bytes

    return hashlib.sha256(raw_bytes).digest()


def encrypt_token(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt_token(encoded: str) -> str:
    if not encoded:
        return encoded
    try:
        raw = base64.b64decode(encoded.encode())
        key = _get_aes_key()
        aesgcm = AESGCM(key)
        nonce, ciphertext = raw[:12], raw[12:]
        return aesgcm.decrypt(nonce, ciphertext, None).decode()
    except Exception:
        return encoded
