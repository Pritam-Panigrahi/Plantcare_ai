from unittest.mock import patch
from app.models import NatureMission, MissionCompletion, NatureBadge, db

def test_mission_generation_curated_fallback(client):
    """Test generating a mission when Ollama is offline returns a curated mission."""
    resp = client.post(
        "/api/missions/generate",
        json={
            "activity_type": "walking",
            "duration_minutes": 15,
            "difficulty": "easy",
            "environment": "park",
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "mission" in data
    m = data["mission"]
    assert m["duration_minutes"] == 15
    assert len(m["checklist"]) >= 2
    assert "Micro-Leaf" in m["title"] or "Quest" in m["title"] or "Mission" in m["title"]


def test_mission_generation_mocked_ai(client):
    """Test mission generation when local AI returns structured JSON."""
    mock_ai_data = {
        "title": "The Lichen Detective Trail",
        "objective": "Find and map two different colors of tree bark lichen.",
        "instructions": "1. Walk to tree.\n2. Observe lichen with lens.\n3. Note color.",
        "checklist": ["Spot crustose lichen", "Spot foliose lichen", "Check north vs south side"],
        "safety_guidance": "Do not scrape bark.",
        "completion_criteria": "Two lichens noted.",
        "reflection_question": "Which side of the tree had the densest growth?",
    }

    with patch("app.services.ai_service.NatureAIService.generate_outdoor_mission") as mock_ai:
        mock_ai.return_value = {"success": True, "data": mock_ai_data}

        resp = client.post(
            "/api/missions/generate",
            json={
                "activity_type": "exploration",
                "duration_minutes": 20,
                "difficulty": "moderate",
                "environment": "forest_trail",
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["mission"]["title"] == "The Lichen Detective Trail"
        assert data["mission"]["is_ai_generated"] is True


def test_mission_completion_and_badge_unlock(client):
    """Test marking a mission complete records reflection and unlocks Touch Grass badge."""
    # Seed a mission
    mission = NatureMission(
        title="10-Minute Sun Basking",
        activity_type="walking",
        duration_minutes=10,
        objective="Feel the warmth of sunlight on bare soil.",
        instructions="Step outside.",
        checklist_raw='["Feel sunlight", "Observe shadows"]',
        safety_guidance="Wear sun protection.",
        completion_criteria="Spent 10 min outside.",
        reflection_question="How did the air feel?",
    )
    db.session.add(mission)
    db.session.commit()

    # Complete the mission
    resp = client.post(
        f"/api/missions/{mission.id}/complete",
        json={
            "user_reflection": "Felt cool autumn breeze and smelled crushed pine needles.",
            "outdoor_notes": "Sunny 19 degrees.",
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "Marked complete" in data["message"] or "complete" in data["message"].lower()

    # Verify badge "touch-grass-initiate" is unlocked!
    badge = NatureBadge.query.filter_by(slug="touch-grass-initiate").first()
    assert badge is not None
    assert badge.is_unlocked is True
