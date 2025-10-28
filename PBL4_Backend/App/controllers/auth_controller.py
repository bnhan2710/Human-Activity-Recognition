from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..schema.auth_schema import RegisterRequest, LoginRequest, TokenResponse
from ..services.auth_service import register_user, login_user, AuthService
from fastapi import WebSocket, Request, HTTPException, status, WebSocketDisconnect
from typing import Optional, Dict, Any

router = APIRouter(prefix="/auth", tags=["Auth"])

async def get_current_user(websocket: Optional[WebSocket] = None, request: Optional[Request] = None) -> Dict[str, Any]:
    token: Optional[str] = None

    if websocket is not None:
        token = websocket.query_params.get("token")
        if not token:
            auth = websocket.headers.get("authorization")
            if auth and auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1]

    if token is None and request is not None:
        auth = request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]

    if not token:
        if websocket is not None:
            await websocket.close(code=1008)
            raise WebSocketDisconnect()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = AuthService.decode_token(token)
        return AuthService.get_user_from_payload(payload)
    except Exception:
        if websocket is not None:
            await websocket.close(code=1008)
            raise WebSocketDisconnect()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

@router.post("/register", response_model=TokenResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, data.email, data.username, data.password, data.weight)
    token = login_user(db, data.email, data.password)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    token = login_user(db, data.email, data.password)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def get_current_user_profile(request: Request):
    """Get current user profile from JWT token"""
    try:
        user = get_current_user(request=request)
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
