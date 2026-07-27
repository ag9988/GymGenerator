from datetime import datetime
from app.schemas import SessionCreate, ExerciseSchema, SetSchema

def test_create_gym_session(client):
    """Test creating a gym workout session."""
    session_data = {
        "type": "upper",
        "difficulty": "intermediate",
        "goal": "hypertrophy",
        "unit": "lb",
        "session_lp": 0,
        "exercises": [
            {
                "name": "Bench Press",
                "order": 0,
                "sets": [
                    {"weight": "185", "reps": "8-12", "order": 0},
                    {"weight": "185", "reps": "8-12", "order": 1},
                    {"weight": "185", "reps": "8-12", "order": 2},
                ]
            }
        ]
    }

    response = client.post("/api/sessions", json=session_data)
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "upper"
    assert data["difficulty"] == "intermediate"
    assert len(data["exercises"]) == 1
    assert data["exercises"][0]["name"] == "Bench Press"
    assert len(data["exercises"][0]["sets"]) == 3

def test_list_sessions(client):
    """Test listing sessions."""
    session_data = {
        "type": "upper",
        "difficulty": "beginner",
        "goal": "strength",
        "unit": "lb",
        "exercises": []
    }

    # Create 2 sessions
    client.post("/api/sessions", json=session_data)
    client.post("/api/sessions", json=session_data)

    response = client.get("/api/sessions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_get_session(client):
    """Test getting a specific session."""
    session_data = {
        "type": "lower",
        "difficulty": "advanced",
        "goal": "endurance",
        "unit": "kg",
        "exercises": []
    }

    create_response = client.post("/api/sessions", json=session_data)
    session_id = create_response.json()["id"]

    response = client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "lower"
    assert data["unit"] == "kg"

def test_delete_session(client):
    """Test deleting a session."""
    session_data = {
        "type": "upper",
        "difficulty": "beginner",
        "goal": "hypertrophy",
        "unit": "lb",
        "exercises": []
    }

    create_response = client.post("/api/sessions", json=session_data)
    session_id = create_response.json()["id"]

    response = client.delete(f"/api/sessions/{session_id}")
    assert response.status_code == 200

    # Verify it's deleted
    response = client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 404

def test_get_exercises(client):
    """Test getting available exercises."""
    response = client.get("/api/utils/exercises?workout_type=upper")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "name" in data[0]
    assert "muscles" in data[0]
    assert "type" in data[0]

def test_get_swaps(client):
    """Test getting exercise swaps."""
    response = client.get("/api/utils/swaps?exercise=Bench%20Press")
    assert response.status_code == 200
    data = response.json()
    assert "similar" in data
    assert "easier" in data
    assert len(data["similar"]) > 0
