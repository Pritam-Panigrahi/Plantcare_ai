import io
import os
import pytest
from PIL import Image
from app import create_app
from app.models import db, NatureBadge
from app.services.nature_service import NatureService

@pytest.fixture
def app():
    """Create Flask test application configured for in-memory SQLite and isolated uploads."""
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        nature_service = NatureService()
        nature_service.init_badges_if_needed()
        yield app
        db.session.remove()
        db.drop_all()

    # Clean up test upload directory if created
    test_upload_folder = app.config["UPLOAD_FOLDER"]
    if os.path.exists(test_upload_folder):
        for f in os.listdir(test_upload_folder):
            try:
                os.remove(os.path.join(test_upload_folder, f))
            except Exception:
                pass


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def sample_image_bytes():
    """Generate a small valid RGB JPEG in memory for test uploads."""
    img = Image.new("RGB", (100, 100), color=(46, 125, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def sample_png_bytes():
    """Generate a small valid RGBA PNG in memory for test uploads."""
    img = Image.new("RGBA", (120, 120), color=(184, 217, 134, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()
