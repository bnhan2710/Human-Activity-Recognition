from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from ..services.auth_service import AuthService
from ..model.notification_model import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


async def get_current_user_dependency(request: Request):
    """Extract and validate user from JWT token"""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")
    
    token = auth_header.split(" ", 1)[1]
    try:
        payload = AuthService.decode_token(token)
        user = AuthService.get_user_from_payload(payload)
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")


@router.get("")
async def get_notifications(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_dependency)
):
    """Get latest 10 notifications for current user"""
    user_id = user["id"]
    
    notifications = db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    result = []
    for notif in notifications:
        result.append({
            "id": notif.id,
            "notification_type": notif.notification_type,
            "title": notif.title,
            "message": notif.message,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat() if notif.created_at else None
        })
    
    return {"notifications": result, "total": len(result)}


@router.put("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_dependency)
):
    """Mark a notification as read"""
    user_id = user["id"]
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    
    return {"success": True, "message": "Notification marked as read"}
