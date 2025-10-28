from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
from ..db import get_db
from ..services.auth_service import AuthService
from ..services.activity_service import get_calories_by_date, get_activity_history

router = APIRouter(prefix="/activities", tags=["Activities"])


async def get_current_user_dependency(request: Request):
    """Extract and validate user from JWT token in Authorization header"""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid authorization header")
    
    token = auth_header.split(" ", 1)[1]
    
    try:
        payload = AuthService.decode_token(token)
        user = AuthService.get_user_from_payload(payload)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")


@router.get("/calories")
async def get_calories(
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_dependency)
):
    """Get calories statistics for a specific date"""
    user_id = user["id"]
    print(f"DEBUG: user_id from token = {user_id}")  # Debug log
    
    # Parse date if provided, otherwise use today
    parsed_date = None
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}
    
    result = get_calories_by_date(db, user_id, parsed_date)
    print(f"DEBUG: result = {result}")  # Debug log
    return result


@router.get("/history")
async def get_history(
    target_date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_dependency)
):
    """Get activity history for a specific date, sorted by time"""
    user_id = user["id"]
    print(f"DEBUG history: user_id = {user_id}, target_date = {target_date}")
    
    # Parse date if provided, otherwise use today
    parsed_date = None
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}
    
    result = get_activity_history(db, user_id, parsed_date)
    print(f"DEBUG history result: {result}")
    return result
