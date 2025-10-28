from typing import Optional, Dict, Any
from fastapi import WebSocket, Request, HTTPException, status, WebSocketDisconnect
from jose import JWTError, jwt
from . import config


async def get_current_user(websocket: Optional[WebSocket] = None, request: Optional[Request] = None) -> Dict[str, Any]:
    """
    Dependency to obtain current user from a JWT access token.
    Works for WebSocket (reads ?token= or Authorization header) and HTTP Request (Authorization header).
    Returns a dict like: {"id": ..., "email": ..., "username": ...}
    If token is missing/invalid: for WebSocket it will close the socket and raise WebSocketDisconnect;
    for HTTP it will raise HTTPException 401.
    """
    token: Optional[str] = None

    # WebSocket context: prefer query param 'token', fall back to Authorization header
    if websocket is not None:
        token = websocket.query_params.get("token")
        if not token:
            auth = websocket.headers.get("authorization")
            if auth and auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1]

    # HTTP request context: read Authorization header
    if token is None and request is not None:
        auth = request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]

    if not token:
        if websocket is not None:
            # close websocket then raise disconnect so endpoint can handle it
            await websocket.close(code=1008)
            raise WebSocketDisconnect()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id = payload.get("sub") or payload.get("user_id")
        if user_id is None:
            raise JWTError("Missing user identifier in token")

        return {"id": user_id, "email": payload.get("email"), "username": payload.get("username")}
    except JWTError:
        if websocket is not None:
            await websocket.close(code=1008)
            raise WebSocketDisconnect()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
