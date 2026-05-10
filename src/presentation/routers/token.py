import os

from fastapi import APIRouter, Form, HTTPException, status
from fastapi.responses import JSONResponse

from infrastructure.auth.oauth2 import create_access_token

router = APIRouter(tags=["auth"])


@router.post("/token")
def issue_token(
    client_id: str = Form(...),
    client_secret: str = Form(...),
) -> JSONResponse:
    expected_id = os.environ.get("OAUTH2_CLIENT_ID", "")
    expected_secret = os.environ.get("OAUTH2_CLIENT_SECRET", "")

    if not (client_id == expected_id and client_secret == expected_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="client_id ou client_secret inválidos.",
        )

    token = create_access_token(subject=client_id)
    return JSONResponse({"access_token": token, "token_type": "bearer"})
