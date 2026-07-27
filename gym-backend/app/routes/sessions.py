from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models import Session as SessionModel, Exercise, Set, CardioSession, FreeSession
from app.schemas import SessionCreate, SessionResponse, SessionListResponse, SessionUpdate, ExerciseSchema, SetSchema, CardioSessionSchema, FreeSessionSchema
from app.utils import calc_load_points

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

@router.get("", response_model=List[SessionListResponse])
def list_sessions(
    skip: int = 0,
    limit: int = 100,
    session_type: Optional[str] = None,
    days: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List sessions with optional filtering."""
    query = db.query(SessionModel).order_by(desc(SessionModel.date))

    if session_type:
        query = query.filter(SessionModel.type == session_type)

    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(SessionModel.date >= cutoff_date)

    sessions = query.offset(skip).limit(limit).all()
    return sessions

@router.post("", response_model=SessionResponse)
def create_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    """Create a new session."""
    # Calculate load points if not provided
    lp = session_data.session_lp
    if lp == 0:
        lp = calc_load_points(session_data.model_dump())

    # Create session record
    db_session = SessionModel(
        type=session_data.type,
        difficulty=session_data.difficulty,
        goal=session_data.goal,
        unit=session_data.unit,
        session_lp=lp,
        date=session_data.date or datetime.utcnow(),
    )
    db.add(db_session)
    db.flush()  # Get the session ID without committing

    # Add exercises if gym session
    if session_data.exercises:
        for ex_idx, ex_data in enumerate(session_data.exercises):
            db_exercise = Exercise(
                session_id=db_session.id,
                name=ex_data.name,
                order=ex_idx,
            )
            db.add(db_exercise)
            db.flush()

            # Add sets
            for set_idx, set_data in enumerate(ex_data.sets):
                db_set = Set(
                    exercise_id=db_exercise.id,
                    weight=set_data.weight,
                    reps=set_data.reps,
                    order=set_idx,
                )
                db.add(db_set)

    # Add cardio data if cardio session
    if session_data.cardio:
        db_cardio = CardioSession(
            session_id=db_session.id,
            distance=session_data.cardio.distance,
            distance_unit=session_data.cardio.distance_unit,
            duration_hours=session_data.cardio.duration_hours,
            duration_minutes=session_data.cardio.duration_minutes,
            duration_seconds=session_data.cardio.duration_seconds,
            elevation=session_data.cardio.elevation,
            elevation_unit=session_data.cardio.elevation_unit,
            heart_rate=session_data.cardio.heart_rate,
            notes=session_data.cardio.notes,
        )
        db.add(db_cardio)

    # Add free session data if free/breathwork
    if session_data.free:
        db_free = FreeSession(
            session_id=db_session.id,
            duration_minutes=session_data.free.duration_minutes,
            rpe=session_data.free.rpe,
            average_heart_rate=session_data.free.average_heart_rate,
            pattern=session_data.free.pattern,
            rounds=session_data.free.rounds,
            notes=session_data.free.notes,
        )
        db.add(db_free)

    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Get a session by ID."""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return db_session

@router.put("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: int,
    session_update: SessionUpdate,
    db: Session = Depends(get_db)
):
    """Update a session."""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update basic fields
    if session_update.type is not None:
        db_session.type = session_update.type
    if session_update.difficulty is not None:
        db_session.difficulty = session_update.difficulty
    if session_update.goal is not None:
        db_session.goal = session_update.goal
    if session_update.unit is not None:
        db_session.unit = session_update.unit
    if session_update.session_lp is not None:
        db_session.session_lp = session_update.session_lp

    # Update exercises if provided
    if session_update.exercises is not None:
        # Clear existing exercises
        db.query(Exercise).filter(Exercise.session_id == session_id).delete()

        # Add new exercises
        for ex_idx, ex_data in enumerate(session_update.exercises):
            db_exercise = Exercise(
                session_id=db_session.id,
                name=ex_data.name,
                order=ex_idx,
            )
            db.add(db_exercise)
            db.flush()

            for set_idx, set_data in enumerate(ex_data.sets):
                db_set = Set(
                    exercise_id=db_exercise.id,
                    weight=set_data.weight,
                    reps=set_data.reps,
                    order=set_idx,
                )
                db.add(db_set)

    db.commit()
    db.refresh(db_session)
    return db_session

@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    """Delete a session."""
    db_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(db_session)
    db.commit()
    return {"detail": "Session deleted"}
