import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
from database import get_db

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 12

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_token(user: models.User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user.id), "username": user.username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _decode(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    """Returns the authenticated user, or None if no/invalid token. Never raises —
    endpoints that require auth call `require_user` on top of this."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    payload = _decode(header[len("Bearer "):])
    if not payload:
        return None
    user = db.get(models.User, int(payload["sub"]))
    if user is None or not user.active:
        return None
    return user


def require_user(user: Optional[models.User] = Depends(get_current_user)) -> models.User:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_roles(*role_names: str):
    """Dependency factory: 401 if unauthenticated, 403 if role doesn't match."""

    def _dependency(user: models.User = Depends(require_user)) -> models.User:
        user_role = user.role.name if user.role else None
        if user_role not in role_names:
            raise HTTPException(
                status_code=403,
                detail=f"Requires one of roles: {', '.join(role_names)}",
            )
        return user

    return _dependency
