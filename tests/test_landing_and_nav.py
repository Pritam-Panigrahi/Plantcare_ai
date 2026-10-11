def test_landing_page_renders(client):
    """Test landing page renders with branding, CTAs, and Touch Grass ethos."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "NatureLens" in html
    assert "Discover the Wild Around You" in html
    assert "Look closer. Discover nature. Touch grass." in html
    assert "Explore Nature" in html
    assert "Start a Nature Mission" in html


def test_about_page_renders(client):
    """Test about page renders open-source AI architecture details."""
    resp = client.get("/about")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "Why Does Open Innovation Matter?" in html
    assert "Ollama" in html
    assert "llama3.2-vision" in html
    assert "Leave No Trace" in html


def test_offline_page_renders(client):
    """Test offline fallback page renders for Service Worker caching."""
    resp = client.get("/offline")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "You Are Currently Offline" in html


def test_404_error_page(client):
    """Test 404 handler returns friendly page for invalid URLs."""
    resp = client.get("/non-existent-trail-url-xyz")
    assert resp.status_code == 404
    html = resp.data.decode("utf-8")
    assert "Trail Not Found" in html
