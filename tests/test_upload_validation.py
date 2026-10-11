import io

def test_upload_missing_image(client):
    """Test analyze-image fails gracefully when no image is provided."""
    resp = client.post("/api/analyze-image", data={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "No image file provided" in data["error"]


def test_upload_invalid_file_extension(client):
    """Test rejecting files with disallowed extensions (e.g. .txt)."""
    data = {
        "image": (io.BytesIO(b"fake text data"), "observation.txt"),
        "category_hint": "leaf",
    }
    resp = client.post("/api/analyze-image", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    res_json = resp.get_json()
    assert res_json["success"] is False
    assert "Unsupported file format" in res_json["error"]


def test_upload_corrupted_image_bytes(client):
    """Test rejecting non-image files disguised with .jpg extension."""
    data = {
        "image": (io.BytesIO(b"Not a real jpeg file header"), "fake.jpg"),
        "category_hint": "flower",
    }
    resp = client.post("/api/analyze-image", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    res_json = resp.get_json()
    assert res_json["success"] is False
    assert "Corrupted or invalid image" in res_json["error"]


def test_valid_image_upload_and_fallback_analysis(client, sample_image_bytes):
    """Test uploading a valid JPEG; when Ollama is offline, returns curated educational data."""
    data = {
        "image": (io.BytesIO(sample_image_bytes), "test_leaf.jpg"),
        "category_hint": "leaf",
    }
    resp = client.post("/api/analyze-image", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    res_json = resp.get_json()
    assert res_json["success"] is True
    assert "analysis" in res_json
    assert res_json["analysis"]["category"] == "leaf"
    assert "image_filename" in res_json
    assert res_json["image_url"].startswith("/uploads/")
