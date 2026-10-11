import os
from flask import Blueprint, jsonify, current_app, send_from_directory, abort
from werkzeug.utils import secure_filename
from app.models import db, NatureDiscovery, NatureMission
from app.services.ai_service import NatureAIService

api_bp = Blueprint("api", __name__)
ai_service = NatureAIService()

@api_bp.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint for container orchestrators and status monitoring."""
    db_ok = True
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception:
        db_ok = False

    return jsonify({
        "status": "healthy" if db_ok else "degraded",
        "service": "NatureLens AI",
        "database_connected": db_ok,
        "environment": current_app.config.get("ENV", "production" if not current_app.debug else "development"),
    }), (200 if db_ok else 500)


@api_bp.route("/api/ai-status", methods=["GET"])
def ai_status():
    """Returns safe diagnostic information regarding AI connectivity (Gemini & Ollama)."""
    status_info = ai_service.check_ai_status()
    # Mask any internal sensitive parameters (API key is strictly omitted)
    safe_data = {
        "connected": status_info.get("connected", False),
        "provider": status_info.get("provider", "offline"),
        "active_model": status_info.get("active_model", ""),
        "mode": status_info.get("mode", "Offline Mode"),
        "gemini_configured": status_info.get("gemini_configured", False),
        "gemini_model": status_info.get("gemini_model"),
        "vision_model_configured": current_app.config.get("OLLAMA_VISION_MODEL"),
        "text_model_configured": current_app.config.get("OLLAMA_TEXT_MODEL"),
        "available_models": status_info.get("available_models", []),
        "status_message": status_info.get("status_message"),
    }
    return jsonify(safe_data)


@api_bp.route("/uploads/<path:filename>")
def serve_upload(filename):
    """Safely serve uploaded user photographs with path traversal protection."""
    # Ensure filename is safe and has no path separators
    clean_name = secure_filename(os.path.basename(filename))
    upload_folder = current_app.config.get("UPLOAD_FOLDER")
    if not clean_name or not os.path.exists(os.path.join(upload_folder, clean_name)):
        abort(404)
    return send_from_directory(upload_folder, clean_name)
