import os
import logging
from flask import Blueprint, render_template, request, jsonify, current_app
from app.models import db, NatureDiscovery
from app.services.nature_service import NatureService

logger = logging.getLogger(__name__)

explorer_bp = Blueprint("explorer", __name__)
nature_service = NatureService()

@explorer_bp.route("/explorer")
def explorer():
    """Nature Explorer page for photo capture and AI species identification."""
    recent_discoveries = NatureDiscovery.query.order_by(NatureDiscovery.created_at.desc()).limit(4).all()
    return render_template("explorer.html", recent_discoveries=recent_discoveries)


@explorer_bp.route("/api/analyze-image", methods=["POST"])
def analyze_image():
    """Endpoint for uploading a photograph and running local vision model inference."""
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file provided in request."}), 400

    file_storage = request.files["image"]
    category_hint = request.form.get("category_hint", "unknown")
    if category_hint not in {"bird", "plant", "flower", "leaf", "insect", "unknown"}:
        category_hint = "unknown"

    try:
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        unique_filename, save_path = nature_service.process_and_save_upload(file_storage, upload_folder)
    except ValueError as val_err:
        return jsonify({"success": False, "error": str(val_err)}), 400
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return jsonify({"success": False, "error": "Failed to process image file."}), 500

    # Run AI analysis (or curated fallback if Ollama is offline)
    try:
        analysis_data = nature_service.analyze_image_with_fallback(save_path, category_hint=category_hint)
        return jsonify({
            "success": True,
            "analysis": analysis_data,
            "image_filename": unique_filename,
            "image_url": f"/uploads/{unique_filename}",
        })
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return jsonify({
            "success": False,
            "error": "Species analysis encountered an unexpected error.",
            "details": str(e),
        }), 500


@explorer_bp.route("/api/journal/save", methods=["POST"])
def save_discovery():
    """Persist an analyzed discovery into the SQLite Nature Journal."""
    data = request.get_json()
    if not data or not data.get("common_name"):
        return jsonify({"success": False, "error": "A valid common name is required."}), 400

    category = data.get("category", "unknown")
    if category not in {"bird", "plant", "flower", "leaf", "insect", "unknown"}:
        category = "unknown"

    discovery = NatureDiscovery(
        common_name=data["common_name"].strip(),
        scientific_name=data.get("scientific_name", "").strip() or None,
        category=category,
        confidence_level=data.get("confidence_level", "moderate"),
        visible_characteristics=data.get("visible_characteristics", ""),
        habitat_ecology=data.get("habitat_ecology", ""),
        educational_facts=data.get("educational_facts", ""),
        observation_activity=data.get("observation_activity", ""),
        limitations_notes=data.get("limitations_notes", ""),
        image_filename=data.get("image_filename"),
        user_notes=data.get("user_notes", "").strip() or None,
        location_name=data.get("location_name", "").strip() or None,
        is_demo=bool(data.get("is_demo", False)),
        model_used=data.get("model_used", "Local AI"),
    )

    db.session.add(discovery)
    db.session.commit()

    # Check for unlocked badges following this new discovery
    new_badges = nature_service.check_and_unlock_badges()
    unlocked_badge_data = [b.to_dict() for b in new_badges]

    return jsonify({
        "success": True,
        "discovery_id": discovery.id,
        "message": "Observation saved to your Nature Journal!",
        "newly_unlocked_badges": unlocked_badge_data,
    })
