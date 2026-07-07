# Gym Workout Backend

A FastAPI + SQLite backend for the gym workout tracking app. This is a companion project to the existing `gym planning/workout-generator.html` but with a full backend instead of localStorage.

## Setup

### Install dependencies

```bash
cd gym-backend
pip install -e .
```

### Run the server

```bash
python -m uvicorn app.main:app --reload
```

The server will start at `http://localhost:8000`.

### View API documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI.

## Project Structure

- `app/main.py` — FastAPI app and utility endpoints
- `app/database.py` — SQLAlchemy configuration
- `app/models.py` — ORM models (Session, Exercise, Set, etc.)
- `app/schemas.py` — Pydantic request/response models
- `app/utils.py` — Helper functions (load points, unit conversion, exercise/swap data)
- `app/routes/sessions.py` — Session CRUD endpoints
- `app/routes/stats.py` — Stats and trends endpoints
- `tests/` — pytest test suite

## API Endpoints

### Sessions

- `GET /api/sessions` — List all sessions
- `POST /api/sessions` — Create a new session
- `GET /api/sessions/{id}` — Get a session by ID
- `PUT /api/sessions/{id}` — Update a session
- `DELETE /api/sessions/{id}` — Delete a session

Query parameters for listing:
- `skip` — Offset (default: 0)
- `limit` — Number of results (default: 100)
- `session_type` — Filter by type (e.g., "upper", "lower", "run")
- `days` — Only return sessions from the last N days

### Stats

- `GET /api/stats/volume` — Total volume (weight × reps) per exercise
- `GET /api/stats/load` — Training load points trend
- `GET /api/stats/calendar` — Workout days for a month

### Utilities

- `GET /api/utils/exercises?workout_type={type}` — Get available exercises
- `GET /api/utils/swaps?exercise={name}` — Get swap alternatives
- `POST /api/utils/convert-weight` — Convert weight between lb/kg

## Database

SQLite database stored at `./gym.db` (created automatically on first run).

Tables:
- `sessions` — Workout sessions
- `exercises` — Exercises within gym sessions
- `sets` — Sets within exercises
- `cardio_sessions` — Cardio-specific data
- `free_sessions` — Free/breathwork session data

## Running Tests

```bash
pip install -e ".[dev]"
pytest tests/
```

## Session Types

- **Gym**: `upper`, `lower`, `full`, `group_a`, `group_b`, `group_c`
- **Cardio**: `run`, `cycle`, `hike`, `swim`
- **Special**: `free`, `breathwork`

## Development

The app uses:
- **FastAPI** for the HTTP API
- **SQLAlchemy** for ORM
- **Pydantic** for validation
- **SQLite** for persistence

To add new endpoints:
1. Create a route function in `app/routes/*.py`
2. Add Pydantic schemas to `app/schemas.py` if needed
3. Import and include the router in `app/main.py`

CORS is enabled for development (all origins allowed).
