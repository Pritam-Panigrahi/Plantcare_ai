import json
from unittest.mock import patch, MagicMock
import requests
from app.services.ai_service import NatureAIService

def test_ai_status_when_ollama_reachable():
    """Test checking Ollama status when local service is responsive."""
    service = NatureAIService(base_url="http://127.0.0.1:11434")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "llama3.2-vision:11b"}, {"name": "llama3.2:3b"}]
    }

    with patch("requests.get", return_value=mock_resp):
        status = service.check_ollama_status()
        assert status["connected"] is True
        assert "llama3.2-vision:11b" in status["available_models"]
        assert status["has_vision_model"] is True
        assert status["has_text_model"] is True


def test_ai_status_when_ollama_unreachable():
    """Test checking Ollama status when connection refused."""
    service = NatureAIService(base_url="http://127.0.0.1:11434")

    with patch("requests.get", side_effect=requests.exceptions.ConnectionError):
        status = service.check_ollama_status()
        assert status["connected"] is False
        assert status["mode"] == "offline_demo"
        assert "not running" in status["status_message"]


def test_analyze_image_successful_inference():
    """Test analyzing image when Ollama returns valid JSON."""
    service = NatureAIService(base_url="http://127.0.0.1:11434", vision_model="llama3.2-vision:11b")

    mock_model_payload = {
        "common_name": "Monarch Butterfly",
        "scientific_name": "Danaus plexippus",
        "category": "insect",
        "confidence_level": "high",
        "visible_characteristics": "Bright orange wings with black borders and white dots.",
        "habitat_ecology": "Meadows and milkweed habitats.",
        "educational_facts": "Migrates thousands of miles.",
        "observation_activity": "Look for caterpillars on milkweed.",
        "limitations_notes": "Visually distinct, but can resemble Viceroy butterfly.",
    }

    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    # Wrap in markdown fences to test regex cleanup
    mock_post_resp.json.return_value = {
        "response": f"```json\n{json.dumps(mock_model_payload)}\n```"
    }

    with patch("requests.post", return_value=mock_post_resp):
        res = service.analyze_nature_image(b"fake_image_bytes")
        assert res["success"] is True
        data = res["data"]
        assert data["common_name"] == "Monarch Butterfly"
        assert data["is_ai_generated"] is True
        assert data["model_used"] == "llama3.2-vision:11b"


def test_analyze_image_timeout_handling():
    """Test timeout error handling when hardware is overloaded."""
    service = NatureAIService(base_url="http://127.0.0.1:11434", timeout=5)

    with patch("requests.post", side_effect=requests.exceptions.Timeout):
        res = service.analyze_nature_image(b"fake_image_bytes")
        assert res["success"] is False
        assert res["code"] == "TIMEOUT"
        assert "timed out" in res["error"]


def test_generate_explanation_successful():
    """Test AI Nature Guide explanation generation with text model."""
    service = NatureAIService(base_url="http://127.0.0.1:11434", text_model="llama3.2:3b")

    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {
        "response": "To observe backyard birds, stay still near a bird bath for 10 minutes."
    }

    with patch("requests.post", return_value=mock_post_resp):
        res = service.generate_nature_explanation("How do I watch birds?")
        assert res["success"] is True
        assert "stay still" in res["explanation"]
        assert res["is_ai_generated"] is True
