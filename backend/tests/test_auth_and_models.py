from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import UserRole
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import UserResponse


def test_password_hashing():
    pwd = "SecureStudentPass123!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_rs256_jwt_token_generation_and_decoding():
    user_id = uuid4()
    tenant_id = uuid4()
    data = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": UserRole.STUDENT.value,
        "email": "student@university.edu",
    }
    token = create_access_token(data)
    assert isinstance(token, str)

    payload = decode_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["role"] == UserRole.STUDENT.value
    assert payload["token_type"] == "access"
    assert "exp" in payload
    assert "iat" in payload


def test_refresh_token_family_generation():
    user_id = uuid4()
    family_id = uuid4()
    raw_token, token_hash = create_refresh_token(user_id, family_id)

    assert raw_token.startswith(f"rft_{user_id}_{family_id}_")
    assert hash_refresh_token(raw_token) == token_hash


def test_student_schema_excludes_cognitive_internals():
    """Verify that UserResponse does not leak cognitive internals."""
    now = datetime.now(timezone.utc)
    user_data = {
        "id": uuid4(),
        "institution_id": uuid4(),
        "email": "test@university.edu",
        "full_name": "Test Student",
        "role": UserRole.STUDENT,
        "is_active": True,
        "is_verified": True,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
        "profile_data": {},
    }
    user_resp = UserResponse.model_validate(user_data)
    dumped = user_resp.model_dump()

    # Invariants
    for forbidden in ["iori", "hmm_probabilities", "alpha_post", "beta_post", "mentor_notes", "referral_data"]:
        assert forbidden not in dumped
