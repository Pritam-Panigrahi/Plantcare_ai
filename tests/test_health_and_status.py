def test_health_check_endpoint(client):
    """Test health check endpoint returns 200 OK and database connectivity."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert data["service"] == "NatureLens AI"
    assert data["database_connected"] is True


def test_ai_status_endpoint(client):
    """Test AI status endpoint returns safe diagnostic fields."""
    resp = client.get("/api/ai-status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "connected" in data
    assert "mode" in data
    assert "vision_model_configured" in data
    assert "text_model_configured" in data
    assert "status_message" in data


def test_uploads_path_traversal_protection(client):
    """Test preventing directory traversal attacks on the uploads endpoint."""
    resp = client.get("/uploads/../../etc/passwd")
    assert resp.status_code in (404, 400)


def test_uploads_non_existent_file(client):
    """Test returning 404 for non-existent upload files."""
    resp = client.get("/uploads/ghost_nature_photo_123.jpg")
    assert resp.status_code == 404
