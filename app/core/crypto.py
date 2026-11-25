"""
Symmetric Encryption Helper for Client Secrets
Using Cryptography Fernet (AES-128-CBC with HMAC-SHA256 authentication)
"""

from cryptography.fernet import Fernet
from app.core.config import settings

_fernet = Fernet(settings.ENCRYPTION_SECRET_KEY.encode("utf-8"))


def encrypt_secret(raw_secret: str) -> str:
    """对称加密敏感凭据"""
    if not raw_secret:
        return ""
    # 如果已经是加密串，避免双重加密
    if raw_secret.startswith("gAAAAA"):
        return raw_secret
    encrypted_bytes = _fernet.encrypt(raw_secret.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_secret(encrypted_secret: str) -> str:
    """解密敏感凭据"""
    if not encrypted_secret:
        return ""
    if not encrypted_secret.startswith("gAAAAA"):
        return encrypted_secret
    try:
        decrypted_bytes = _fernet.decrypt(encrypted_secret.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception:
        # 解密失败降级返回原值
        return encrypted_secret

