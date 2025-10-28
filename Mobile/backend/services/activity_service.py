from datetime import datetime, date
from typing import Optional, Dict
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..model.activity_model import Activity
from ..model.notification_model import Notification

# Hệ số MET cho từng hoạt động
MET_VALUES = {
    0: 1.3,  # Đứng
    1: 1.0,  # Ngồi
    2: 7.0,  # Chạy
    3: 3.5,  # Đi bộ
    4: 3.5   # Leo xuống cầu thang
}

# In-memory map of currently open activities per user (not yet persisted)
active_activities: Dict[int, Activity] = {}


def calculate_calories(action_label: int, weight_kg: float, duration_sec: float) -> float:
    """Calculate calories burned for an activity using MET value."""
    met = MET_VALUES.get(action_label, 1.0)  # default to 1.0 if action not found
    duration_hours = duration_sec / 3600.0  # convert seconds to hours
    return met * weight_kg * duration_hours


def process_detected_action(db: Session, user_id: int, action_label: int, weight_kg: float, timestamp: Optional[datetime] = None) -> Activity:
    """
    Handle a newly detected action for a user and calculate calories burned.
    Also checks for prolonged sitting when activity changes.
    """
    now = timestamp or datetime.utcnow()
    current = active_activities.get(user_id)

    if current is None:
        # Start new in-memory activity (do not persist yet)
        in_memory = Activity(user_id=user_id, action=action_label, start_time=now)
        active_activities[user_id] = in_memory
        return in_memory

    # There is an active in-memory activity
    if current.action == action_label:
        # same action continues -> nothing to persist yet
        return current

    # Action changed -> persist the old activity to DB with calories calculation
    old = Activity(user_id=current.user_id, action=current.action, start_time=current.start_time)
    old.end_time = now
    old.duration = (old.end_time - old.start_time).total_seconds()
    old.calories_burned = calculate_calories(old.action, weight_kg, old.duration)
    
    db.add(old)
    db.commit()
    db.refresh(old)

    # Check for prolonged sitting notification
    check_and_create_notification(db, user_id, old)

    # start new in-memory activity
    new_act = Activity(user_id=user_id, action=action_label, start_time=now)
    active_activities[user_id] = new_act
    return new_act


def persist_open_activity(db: Session, user_id: int, weight_kg: float, timestamp: Optional[datetime] = None) -> Optional[Activity]:
    """
    Persist open activity with calories calculation and sitting notification check.
    """
    now = timestamp or datetime.utcnow()
    current = active_activities.pop(user_id, None)
    if current is None:
        return None

    act = Activity(user_id=current.user_id, action=current.action, start_time=current.start_time)
    act.end_time = now
    act.duration = (act.end_time - act.start_time).total_seconds()
    act.calories_burned = calculate_calories(act.action, weight_kg, act.duration)
    
    db.add(act)
    db.commit()
    db.refresh(act)

    # Check for prolonged sitting notification when closing activity
    check_and_create_notification(db, user_id, act)
    
    return act


def check_and_create_notification(db: Session, user_id: int, activity: Activity) -> None:
    """
    Create notification if user has been sitting for more than 1 hour.
    Called when an activity ends (either by new action or by closing).
    """
    # Only check sitting activity (action = 1) that lasted more than 1 hour
    if activity.action == 1 and activity.duration > 3600:
        notification = Notification(
            user_id=user_id,
            notification_type="sitting_warning",
            title="Cảnh báo ngồi quá lâu",
            message=f"Bạn đã ngồi liên tục {activity.duration / 3600:.1f} giờ. Hãy đứng dậy hoạt động!",
            activity_id=activity.id
        )
        db.add(notification)
        db.commit()


def get_calories_by_date(db: Session, user_id: int, target_date: Optional[date] = None) -> dict:
    """
    Get calories statistics for a specific date.
    Returns total calories and breakdown by activity type.
    """
    if target_date is None:
        target_date = date.today()
    
    # Query activities for the given date
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())
    
    activities = db.query(Activity).filter(
        Activity.user_id == user_id,
        Activity.start_time >= start_datetime,
        Activity.start_time <= end_datetime
    ).all()
    
    # Calculate total calories
    total_calories = sum(act.calories_burned or 0 for act in activities)
    
    # Group by action and sum calories
    action_names = {
        0: "Đứng",
        1: "Ngồi", 
        2: "Chạy",
        3: "Đi bộ",
        4: "Leo cầu thang",
        "standing": "Đứng",
        "sitting": "Ngồi",
        "running": "Chạy",
        "walking": "Đi bộ",
        "stair_down": "Leo cầu thang"
    }
    
    breakdown = {}
    for act in activities:
        action_name = action_names.get(act.action, f"Hoạt động {act.action}")
        if action_name not in breakdown:
            breakdown[action_name] = {
                "calories": 0,
                "duration": 0,
                "count": 0
            }
        breakdown[action_name]["calories"] += act.calories_burned or 0
        breakdown[action_name]["duration"] += act.duration or 0
        breakdown[action_name]["count"] += 1
    
    return {
        "date": target_date.isoformat(),
        "total_calories": round(total_calories, 2),
        "activities": breakdown
    }


def get_activity_history(db: Session, user_id: int, target_date: Optional[date] = None) -> dict:
    """
    Get activity history for a specific date, sorted by start time.
    Returns list of activities with start_time, end_time, duration, action.
    """
    if target_date is None:
        target_date = date.today()
    
    # Query activities for the given date, ordered by start_time
    start_datetime = datetime.combine(target_date, datetime.min.time())
    end_datetime = datetime.combine(target_date, datetime.max.time())
    
    activities = db.query(Activity).filter(
        Activity.user_id == user_id,
        Activity.start_time >= start_datetime,
        Activity.start_time <= end_datetime
    ).order_by(Activity.start_time.asc()).all()
    
    # Map action names
    action_names = {
        0: "Đứng",
        1: "Ngồi", 
        2: "Chạy",
        3: "Đi bộ",
        4: "Leo cầu thang",
        "standing": "Đứng",
        "sitting": "Ngồi",
        "running": "Chạy",
        "walking": "Đi bộ",
        "stair_down": "Leo cầu thang"
    }
    
    # Format activities
    history = []
    for act in activities:
        history.append({
            "id": act.id,
            "action": action_names.get(act.action, str(act.action)),
            "start_time": act.start_time.strftime("%H:%M:%S") if act.start_time else None,
            "end_time": act.end_time.strftime("%H:%M:%S") if act.end_time else None,
            "duration": round(act.duration / 60, 1) if act.duration else 0,  # Convert to minutes
            "calories_burned": round(act.calories_burned, 1) if act.calories_burned else 0
        })
    
    return {
        "date": target_date.isoformat(),
        "total_activities": len(history),
        "activities": history
    }
