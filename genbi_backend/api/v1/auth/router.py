from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Optional

from core.database import get_auth_conn
from core.exceptions import AuthError
from api.v1.auth.schemas import LoginRequest, TokenResponse, UserInfo
from api.v1.auth.service import login, me, refresh

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _require_bearer(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant ou format invalide.")
    return authorization[len("Bearer "):]


@router.post("/login", response_model=TokenResponse)
def login_endpoint(body: LoginRequest, conn=Depends(get_auth_conn)):
    try:
        return login(body.email, body.password, conn)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.get("/me", response_model=UserInfo)
def me_endpoint(token: str = Depends(_require_bearer)):
    try:
        return me(token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/refresh", response_model=TokenResponse)
def refresh_endpoint(token: str = Depends(_require_bearer)):
    try:
        return refresh(token)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
