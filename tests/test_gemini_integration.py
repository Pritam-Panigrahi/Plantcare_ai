import json
from unittest.mock import patch, MagicMock
from app.services.ai_service import NatureAIService

def test_gemini_key_detection():
    """Test that has_gemini is True only with a real non-placeholder key."""
    service_none = NatureAIService(gemini_api_key="")
    assert service_none.has_gemini is False

    service_placeholder = NatureAIService(gemini_api_key="your_new_api_key_here")
    assert service_placeholder.has_gemini is False

    service_valid = NatureAIService(gemini_api_key="AIzaSyTestValidFakeKey123")
    assert service_valid.has_gemini is True


def test_ai_status_never_leaks_gemini_key():
    """Verify check_ai_status never exposes the raw GEMINI_API_KEY string."""
    secret_key = "AIzaSySuperSecretKeyDoNotLeak"
    service = NatureAIService(gemini_api_key=secret_key, gemini_model="gemini-2.5-flash")
    status = service.check_ai_status()

    assert status["connected"] is True
    assert status["provider"] == "google_gemini"
    assert status["active_model"] == "gemini-2.5-flash"
    assert status["gemini_configured"] is True
    # Ensure raw secret key is NOT present in any value
    status_str = json.dumps(status)
    assert secret_key not in status_str


def test_gemini_image_analysis_mocked():
    """Test multimodal image analysis using mocked google-genai client."""
    mock_payload = {
        "common_name": "Broadleaf Plantain",
        "scientific_name": "Plantago major",
        "category": "plant",
        "confidence_level": "high",
        "visible_characteristics": "Rosette of broad oval leaves with parallel veins.",
        "habitat_ecology": "Common in footpaths and grasslands.",
        "educational_facts": "Leaves historically used to soothe minor bug bites.",
        "observation_activity": "Gently check leaf stems for string-like veins.",
        "limitations_notes": "Visually distinct, but confirm with local guide.",
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_payload)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    service = NatureAIService(gemini_api_key="AIzaSyTestKey", gemini_model="gemini-2.5-flash")
    with patch.object(service, "get_gemini_client", return_value=mock_client):
        result = service.analyze_nature_image(b"fake_image_bytes", category_hint="plant")
        assert result["success"] is True
        assert result["data"]["common_name"] == "Broadleaf Plantain"
        assert result["data"]["provider"] == "google_gemini"
        assert result["data"]["model_used"] == "gemini-2.5-flash"
        assert result["data"]["is_ai_generated"] is True


def test_gemini_nature_explanation_mocked():
    """Test AI Nature Guide explanation using mocked google-genai client."""
    mock_response = MagicMock()
    mock_response.text = "Solitary bees are vital pollinators visiting over 80% of wildflowers."

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    service = NatureAIService(gemini_api_key="AIzaSyTestKey", gemini_model="gemini-2.5-flash")
    with patch.object(service, "get_gemini_client", return_value=mock_client):
        result = service.generate_nature_explanation("What do solitary bees do?")
        assert result["success"] is True
        assert "pollinators" in result["explanation"]
        assert result["provider"] == "google_gemini"
        assert result["is_ai_generated"] is True


def test_gemini_mission_generation_mocked():
    """Test Touch Grass mission generation using mocked google-genai client."""
    mock_mission_payload = {
        "title": "The Meadow Leaf Census",
        "objective": "Identify three distinct leaf shapes.",
        "instructions": "Walk to park. Inspect leaves. Notice edges.",
        "checklist": ["Find entire margin", "Find serrated margin", "Compare textures"],
        "safety_guidance": "Do not tear leaves from branches.",
        "completion_criteria": "Observed 3 leaves.",
        "reflection_question": "Which leaf had the thickest cuticle?",
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_mission_payload)

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    service = NatureAIService(gemini_api_key="AIzaSyTestKey", gemini_model="gemini-2.5-flash")
    with patch.object(service, "get_gemini_client", return_value=mock_client):
        result = service.generate_outdoor_mission(
            activity_type="walking",
            duration_minutes=15,
            difficulty="easy",
            environment="park",
        )
        assert result["success"] is True
        assert result["data"]["title"] == "The Meadow Leaf Census"
        assert result["data"]["provider"] == "google_gemini"
        assert result["data"]["duration_minutes"] == 15


def test_gemini_invalid_api_key_error_handling():
    """Test error handling when Gemini API key is rejected."""
    service = NatureAIService(gemini_api_key="AIzaSyInvalidKey", gemini_model="gemini-2.5-flash")
    
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API_KEY_INVALID: Key not found (400)")

    with patch.object(service, "get_gemini_client", return_value=mock_client):
        # Image analysis should handle error gracefully and try fallback
        with patch.object(service, "_analyze_image_ollama", return_value={"success": False, "error": "Ollama offline"}):
            result = service.analyze_nature_image(b"fake_image_bytes")
            # Should have caught the error and attempted fallback
            assert result["success"] is False


def test_gemini_quota_exceeded_error_handling():
    """Test error handling when Gemini quota is exceeded."""
    service = NatureAIService(gemini_api_key="AIzaSyQuotaKey", gemini_model="gemini-2.5-flash")
    
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("RESOURCE_EXHAUSTED: 429 Quota exceeded")

    with patch.object(service, "get_gemini_client", return_value=mock_client):
        with patch.object(service, "_generate_explanation_ollama", return_value={"success": False, "error": "Ollama offline"}):
            result = service.generate_nature_explanation("How to watch birds?")
            assert result["success"] is False
