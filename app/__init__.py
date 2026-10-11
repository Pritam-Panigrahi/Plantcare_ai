import os
from flask import Flask, render_template
from config import config_by_name
from app.models import db

def create_app(config_name=None):
    """Application factory for NatureLens AI."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    
    # Load configuration
    cfg = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(cfg)

    # Ensure required directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["INSTANCE_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.explorer import explorer_bp
    from app.routes.guide import guide_bp
    from app.routes.missions import missions_bp
    from app.routes.journal import journal_bp
    from app.routes.progress import progress_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(explorer_bp)
    app.register_blueprint(guide_bp)
    app.register_blueprint(missions_bp)
    app.register_blueprint(journal_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(api_bp)

    # Create tables and initial badges inside app context
    with app.app_context():
        db.create_all()
        from app.services.nature_service import NatureService
        nature_service = NatureService()
        nature_service.init_badges_if_needed()

    # Security Headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

    return app
