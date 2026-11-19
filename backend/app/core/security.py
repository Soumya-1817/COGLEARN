from datetime import datetime, timedelta, timezone
import hashlib
import logging
import secrets
from uuid import UUID, uuid4
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fallback in-memory RSA keypair for dev environment when keys are not explicitly set
_dev_private_key_pem: str | None = None
_dev_public_key_pem: str | None = None


def _get_dev_rsa_keypair() -> tuple[str, str]:
    global _dev_private_key_pem, _dev_public_key_pem
    if _dev_private_key_pem is None or _dev_public_key_pem is None:
        logger.warning(
            "JWT_PRIVATE_KEY or JWT_PUBLIC_KEY is not set. Generating ephemeral 2048-bit RSA keypair for development."
        )
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        _dev_private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")
        _dev_public_key_pem = (
            private_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("utf-8")
        )
    return _dev_private_key_pem, _dev_public_key_pem


def get_private_key() -> str:
    key = settings.jwt_private_key.strip()
    if key and "BEGIN" in key:
        return key
    dev_priv, _ = _get_dev_rsa_keypair()
    return dev_priv


def get_public_key() -> str:
    key = settings.jwt_public_key.strip()
    if key and "BEGIN" in key:
        return key
    _, dev_pub = _get_dev_rsa_keypair()
    return dev_pub


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Creates an RS256 signed JWT access token.
    Token claims include:
    - sub (user_id)
    - tenant_id
    - role
    - permissions
    - session_id
    - iat
    - exp
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "token_type": "access",
    })

    if "session_id" not in to_encode:
        to_encode["session_id"] = str(uuid4())

    private_key = get_private_key()
    encoded_jwt = jwt.encode(to_encode, private_key, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: UUID, family_id: UUID) -> tuple[str, str]:
    """
    Creates a secure refresh token and its SHA-256 hash for database storage.
    Returns:
        tuple[str, str]: (raw_token, token_hash)
    """
    random_entropy = secrets.token_urlsafe(64)
    raw_token = f"rft_{user_id}_{family_id}_{random_entropy}"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return raw_token, token_hash


def hash_refresh_token(raw_token: str) -> str:
    """Computes SHA-256 hash of a raw refresh token."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def decode_token(token: str) -> dict:
    """
    Decodes and verifies an RS256 JWT using the RSA public key.
    Raises JWTError if invalid or expired.
    """
    public_key = get_public_key()
    payload = jwt.decode(
        token,
        public_key,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return payload
