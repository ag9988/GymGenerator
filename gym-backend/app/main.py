from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routes import sessions, stats
from app.utils import EXERCISES, SWAPS

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gym Workout Backend", version="0.1.0")

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(sessions.router)
app.include_router(stats.router)

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/utils/exercises")
def get_exercises(workout_type: str = "upper"):
    """Get available exercises for a workout type."""
    if workout_type not in EXERCISES:
        return {"error": f"Unknown workout type: {workout_type}"}
    return EXERCISES[workout_type]

@app.get("/api/utils/swaps")
def get_swaps(exercise: str):
    """Get swap alternatives for an exercise."""
    if exercise not in SWAPS:
        return {"error": f"No swaps found for exercise: {exercise}"}
    return SWAPS[exercise]

@app.post("/api/utils/convert-weight")
def convert_weight_endpoint(value: float, from_unit: str, to_unit: str):
    """Convert weight between units."""
    from app.utils import convert_weight
    result = convert_weight(value, from_unit, to_unit)
    return {"value": result, "from_unit": from_unit, "to_unit": to_unit}
