from passlib.context import CryptContext
from sqlalchemy.orm import Session
from ..model.user_model import User
from ..auth.jwt_handler import create_access_token
from fastapi import HTTPException, status
from typing import Dict, Any
from jose import JWTError, jwt
from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)

def register_user(db: Session, email: str, username: str, password: str, weight: float):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(
        email=email,
        username=username,
        hashed_password=hash_password(password),
        weight=weight
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def login_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": user.email, "user_id": user.id, "username": user.username})
    return access_token

class AuthService:
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode JWT token and return the payload. May raise JWTError."""
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    @staticmethod
    def get_user_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a user dict from decoded payload. Raises JWTError if missing id."""
        user_id = payload.get("user_id") or payload.get("id")
        if user_id is None:
            raise JWTError("Missing user identifier in token payload")
        return {"id": user_id, "email": payload.get("email") or payload.get("sub"), "username": payload.get("username")}
