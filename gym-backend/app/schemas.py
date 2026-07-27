from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class SetSchema(BaseModel):
    weight: Optional[str] = None
    reps: Optional[str] = None
    order: int

    class Config:
        from_attributes = True

class ExerciseSchema(BaseModel):
    name: str
    order: int
    sets: List[SetSchema]

    class Config:
        from_attributes = True

class CardioSessionSchema(BaseModel):
    distance: float
    distance_unit: str
    duration_hours: int
    duration_minutes: int
    duration_seconds: int
    elevation: Optional[float] = None
    elevation_unit: Optional[str] = None
    heart_rate: Optional[int] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class FreeSessionSchema(BaseModel):
    duration_minutes: int
    rpe: Optional[int] = None
    average_heart_rate: Optional[int] = None
    pattern: Optional[str] = None
    rounds: Optional[int] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class SessionBase(BaseModel):
    type: str  # 'upper', 'lower', 'full', 'group_a/b/c', 'run', 'cycle', 'hike', 'swim', 'free', 'breathwork'
    difficulty: Optional[str] = None
    goal: Optional[str] = None
    unit: Optional[str] = None
    session_lp: float = 0.0
    date: Optional[datetime] = None

class SessionCreate(SessionBase):
    exercises: Optional[List[ExerciseSchema]] = None
    cardio: Optional[CardioSessionSchema] = None
    free: Optional[FreeSessionSchema] = None

class SessionUpdate(BaseModel):
    type: Optional[str] = None
    difficulty: Optional[str] = None
    goal: Optional[str] = None
    unit: Optional[str] = None
    session_lp: Optional[float] = None
    exercises: Optional[List[ExerciseSchema]] = None
    cardio: Optional[CardioSessionSchema] = None
    free: Optional[FreeSessionSchema] = None

class SessionResponse(SessionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    exercises: List[ExerciseSchema] = []
    cardio: Optional[CardioSessionSchema] = None
    free: Optional[FreeSessionSchema] = None

    class Config:
        from_attributes = True

class SessionListResponse(BaseModel):
    id: int
    date: datetime
    type: str
    difficulty: Optional[str]
    goal: Optional[str]
    session_lp: float

    class Config:
        from_attributes = True
