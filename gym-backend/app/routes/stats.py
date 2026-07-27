from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Session as SessionModel, Exercise, Set, CardioSession, FreeSession
from app.utils import convert_weight

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("/volume")
def get_volume_by_exercise(
    session_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, float]:
    """Get total volume (weight × reps) per exercise."""
    query = db.query(SessionModel).filter(
        SessionModel.type.in_(["upper", "lower", "full", "group_a", "group_b", "group_c"])
    )

    if session_type:
        query = query.filter(SessionModel.type == session_type)

    if start_date:
        query = query.filter(SessionModel.date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(SessionModel.date <= datetime.fromisoformat(end_date))

    sessions = query.all()
    volume_by_exercise: Dict[str, float] = {}

    for session in sessions:
        unit = session.unit or "lb"
        for exercise in session.exercises:
            if exercise.name not in volume_by_exercise:
                volume_by_exercise[exercise.name] = 0

            for s in exercise.sets:
                try:
                    weight = float(s.weight or 0)
                    reps_str = s.reps or "0"
                    # Handle ranges like "8-12"
                    reps = float(reps_str.split("-")[0])
                    volume = weight * reps

                    # Normalize to lb if needed
                    if unit == "kg":
                        volume = volume * 2.20462

                    volume_by_exercise[exercise.name] += volume
                except (ValueError, IndexError):
                    pass

    return volume_by_exercise

@router.get("/load")
def get_load_trend(
    days: int = 28,
    db: Session = Depends(get_db)
) -> Dict[str, List]:
    """Get training load points trend over N days."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    sessions = db.query(SessionModel).filter(
        SessionModel.date >= cutoff_date
    ).order_by(SessionModel.date).all()

    daily_load: Dict[str, float] = {}
    for session in sessions:
        date_key = session.date.strftime("%Y-%m-%d")
        if date_key not in daily_load:
            daily_load[date_key] = 0
        daily_load[date_key] += session.session_lp

    return {
        "daily": [
            {"date": date, "load_points": lp}
            for date, lp in sorted(daily_load.items())
        ]
    }

@router.get("/calendar")
def get_calendar_data(
    month: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict:
    """Get workout days for a month."""
    if not month:
        month = datetime.utcnow().strftime("%Y-%m")

    # Parse month (format: YYYY-MM)
    month_date = datetime.strptime(month, "%Y-%m")
    month_start = month_date.replace(day=1)
    # Get next month's first day, then subtract 1 day
    if month_date.month == 12:
        month_end = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)

    sessions = db.query(SessionModel).filter(
        SessionModel.date >= month_start,
        SessionModel.date <= month_end
    ).all()

    workout_days = {}
    for session in sessions:
        date_key = session.date.strftime("%Y-%m-%d")
        if date_key not in workout_days:
            workout_days[date_key] = []
        workout_days[date_key].append({
            "type": session.type,
            "load_points": session.session_lp
        })

    return {
        "month": month,
        "workout_days": workout_days
    }
