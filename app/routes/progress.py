from flask import Blueprint, render_template
from app.services.nature_service import NatureService

progress_bp = Blueprint("progress", __name__)
nature_service = NatureService()

@progress_bp.route("/progress")
def progress():
    """Nature exploration progress dashboard and badges."""
    summary = nature_service.get_user_progress_summary()
    return render_template("progress.html", summary=summary)
