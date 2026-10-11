from app.models import NatureDiscovery, db

def test_journal_save_and_retrieve(client):
    """Test saving a discovery via API and retrieving in journal list."""
    payload = {
        "common_name": "English Oak Leaf",
        "scientific_name": "Quercus robur",
        "category": "leaf",
        "confidence_level": "high",
        "visible_characteristics": "Distinct rounded lobes with auricles at leaf base.",
        "habitat_ecology": "Temperate woodland canopy.",
        "educational_facts": "Hosts hundreds of insect species.",
        "observation_activity": "Inspect undersides for galls.",
        "limitations_notes": "Hybridizes with sessile oak.",
        "user_notes": "Found on the south trail.",
        "location_name": "Riverside Park",
        "is_demo": False,
        "model_used": "Test Vision Model",
    }
    
    resp = client.post("/api/journal/save", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    disc_id = data["discovery_id"]

    # Verify presence in journal HTML
    list_resp = client.get("/journal")
    assert list_resp.status_code == 200
    assert "English Oak Leaf" in list_resp.data.decode("utf-8")

    # Verify detail view
    detail_resp = client.get(f"/journal/{disc_id}")
    assert detail_resp.status_code == 200
    detail_html = detail_resp.data.decode("utf-8")
    assert "Quercus robur" in detail_html
    assert "Found on the south trail." in detail_html


def test_journal_search_and_category_filter(client):
    """Test filtering by category and searching by keyword."""
    # Seed 2 entries
    d1 = NatureDiscovery(common_name="Red Cardinal", category="bird", visible_characteristics="Bright red plumage")
    d2 = NatureDiscovery(common_name="Silver Birch", category="plant", visible_characteristics="White peeling bark")
    db.session.add_all([d1, d2])
    db.session.commit()

    # Search for "Cardinal"
    search_resp = client.get("/journal?q=Cardinal")
    assert search_resp.status_code == 200
    html = search_resp.data.decode("utf-8")
    assert "Red Cardinal" in html
    assert "Silver Birch" not in html

    # Filter for category "plant"
    cat_resp = client.get("/journal?category=plant")
    assert cat_resp.status_code == 200
    cat_html = cat_resp.data.decode("utf-8")
    assert "Silver Birch" in cat_html
    assert "Red Cardinal" not in cat_html


def test_journal_edit_and_delete(client):
    """Test updating and deleting a journal entry."""
    entry = NatureDiscovery(common_name="Baby Robin", category="bird", user_notes="Hopping on lawn")
    db.session.add(entry)
    db.session.commit()
    entry_id = entry.id

    # Edit via POST
    edit_resp = client.post(
        f"/journal/{entry_id}/edit",
        data={
            "common_name": "European Robin (Adult)",
            "scientific_name": "Erithacus rubecula",
            "category": "bird",
            "location_name": "Botanical Garden",
            "user_notes": "Singing from hedge perch",
        },
        follow_redirects=True,
    )
    assert edit_resp.status_code == 200
    assert "European Robin (Adult)" in edit_resp.data.decode("utf-8")

    # Delete via POST
    del_resp = client.post(f"/journal/{entry_id}/delete", follow_redirects=True)
    assert del_resp.status_code == 200
    assert "Observation deleted from your journal." in del_resp.data.decode("utf-8")

    # Ensure deleted from DB
    assert NatureDiscovery.query.get(entry_id) is None


def test_journal_export_json(client):
    """Test exporting all observations to JSON."""
    entry = NatureDiscovery(common_name="Dandelion", category="flower")
    db.session.add(entry)
    db.session.commit()

    resp = client.get("/journal/export")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "total_observations" in data
    assert data["total_observations"] >= 1
    assert any(e["common_name"] == "Dandelion" for e in data["entries"])
