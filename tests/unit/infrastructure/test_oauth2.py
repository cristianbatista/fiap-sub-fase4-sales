import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from jose import jwt

SECRET = "test-secret"
ALGORITHM = "HS256"


def _make_token(payload: dict) -> str:
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGORITHM)


async def test_valid_token_returns_payload():
    from infrastructure.auth.oauth2 import get_current_user

    token = _make_token({"sub": "operator-1"})
    result = await get_current_user(token=token)

    assert result["sub"] == "operator-1"


async def test_expired_token_raises_401():
    from jose import jwt as jose_jwt

    from infrastructure.auth.oauth2 import get_current_user

    import time

    expired_token = jose_jwt.encode(
        {"sub": "op", "exp": int(time.time()) - 10},
        SECRET,
        algorithm=ALGORITHM,
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=expired_token)

    assert exc_info.value.status_code == 401


async def test_missing_sub_claim_raises_401():
    from infrastructure.auth.oauth2 import get_current_user

    token = _make_token({"role": "operator"})

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token)

    assert exc_info.value.status_code == 401


async def test_invalid_token_raises_401():
    from infrastructure.auth.oauth2 import get_current_user

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token="not.a.valid.token")

    assert exc_info.value.status_code == 401
