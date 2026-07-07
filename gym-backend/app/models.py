from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    type = Column(String, index=True)  # 'upper', 'lower', 'full', 'group_a/b/c', 'run', 'cycle', 'hike', 'swim', 'free', 'breathwork'
    difficulty = Column(String, nullable=True)  # 'beginner', 'intermediate', 'advanced'
    goal = Column(String, nullable=True)  # 'strength', 'hypertrophy', 'endurance'
    unit = Column(String, nullable=True)  # 'lb', 'kg'
    session_lp = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    exercises = relationship("Exercise", back_populates="session", cascade="all, delete-orphan")
    cardio = relationship("CardioSession", back_populates="session", uselist=False, cascade="all, delete-orphan")
    free = relationship("FreeSession", back_populates="session", uselist=False, cascade="all, delete-orphan")

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    name = Column(String, index=True)
    order = Column(Integer)

    session = relationship("Session", back_populates="exercises")
    sets = relationship("Set", back_populates="exercise", cascade="all, delete-orphan")

class Set(Base):
    __tablename__ = "sets"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), index=True)
    weight = Column(String, nullable=True)  # Store as string to preserve user input (e.g., "185.5")
    reps = Column(String, nullable=True)    # Store as string to support ranges (e.g., "8-12")
    order = Column(Integer)

    exercise = relationship("Exercise", back_populates="sets")

class CardioSession(Base):
    __tablename__ = "cardio_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), unique=True)
    distance = Column(Float)
    distance_unit = Column(String)  # 'mi', 'km', 'm'
    duration_hours = Column(Integer, default=0)
    duration_minutes = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    elevation = Column(Float, nullable=True)
    elevation_unit = Column(String, nullable=True)  # 'ft', 'm'
    heart_rate = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    session = relationship("Session", back_populates="cardio")

class FreeSession(Base):
    __tablename__ = "free_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), unique=True)
    duration_minutes = Column(Integer)
    rpe = Column(Integer, nullable=True)  # Rate of Perceived Exertion (1-10), free only
    average_heart_rate = Column(Integer, nullable=True)  # free only
    pattern = Column(String, nullable=True)  # 'box', '478', 'sigh' — breathwork only
    rounds = Column(Integer, nullable=True)  # breathwork only
    notes = Column(Text, nullable=True)

    session = relationship("Session", back_populates="free")
