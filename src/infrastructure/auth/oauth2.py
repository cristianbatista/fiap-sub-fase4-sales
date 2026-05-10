import os
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    secret_key = os.environ["JWT_SECRET_KEY"]
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")

    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise _credentials_exception()
        return {"sub": sub}
    except JWTError as err:
        raise _credentials_exception() from err


def create_access_token(subject: str) -> str:
    secret_key = os.environ["JWT_SECRET_KEY"]
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    expire_minutes = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    payload = {
        "sub": subject,
        "exp": datetime.now(UTC) + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def make_service_token() -> str:
    secret_key = os.environ["JWT_SECRET_KEY"]
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    payload = {
        "sub": "sales-service",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas.",
        headers={"WWW-Authenticate": "Bearer"},
    )
