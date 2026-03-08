import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.schemas.auth import GoogleLoginRequest, AuthResponse, UserResponse
from app.db.session import get_db
from app.db.models import User
from app.core.config import settings
from app.core.security import create_access_token
from app.core.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/guest", response_model=AuthResponse)
def guest_login(db: Session = Depends(get_db)):
    user = User(
        id=str(uuid.uuid4()),
        is_guest=True,
        name="Guest",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            is_guest=user.is_guest,
        ),
    )


@router.post("/google", response_model=AuthResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    if not payload.credential:
        raise HTTPException(status_code=400, detail="Missing Google credential")

    try:
        info = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.google_client_id,
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    google_sub = info.get("sub")
    email = info.get("email")
    name = info.get("name")

    if not google_sub or not email:
        raise HTTPException(status_code=401, detail="Invalid Google user info")

    user = db.query(User).filter(User.google_sub == google_sub).first()

    if not user:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            name=name,
            google_sub=google_sub,
            is_guest=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.email = email
        user.name = name
        user.google_sub = google_sub
        user.is_guest = False
        db.commit()
        db.refresh(user)

    token = create_access_token(user.id)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            is_guest=user.is_guest,
        ),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        is_guest=current_user.is_guest,
    )