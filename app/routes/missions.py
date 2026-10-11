from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.models import db, NatureMission, MissionCompletion
from app.services.nature_service import NatureService

missions_bp = Blueprint("missions", __name__)
nature_service = NatureService()

@missions_bp.route("/missions")
def missions():
    """Touch Grass outdoor exploration mission generator & history."""
    all_missions = NatureMission.query.order_by(NatureMission.created_at.desc()).all()
    completions = MissionCompletion.query.order_by(MissionCompletion.completed_at.desc()).limit(5).all()
    return render_template("missions.html", missions=all_missions, recent_completions=completions)


@missions_bp.route("/api/missions/generate", methods=["POST"])
def generate_mission():
    """Generate a new personalized outdoor mission."""
    data = request.get_json() or request.form

    activity_type = data.get("activity_type", "walking")
    duration = int(data.get("duration_minutes", 15))
    difficulty = data.get("difficulty", "easy")
    environment = data.get("environment", "park")
    interests = data.get("interests", "")

    # Sanitize choices
    valid_activities = {"walking", "birdwatching", "gardening", "photography", "exploration"}
    valid_difficulties = {"easy", "moderate", "challenging"}
    valid_environments = {"garden", "park", "neighbourhood", "forest_trail"}

    if activity_type not in valid_activities:
        activity_type = "walking"
    if difficulty not in valid_difficulties:
        difficulty = "easy"
    if environment not in valid_environments:
        environment = "park"
    if duration not in {10, 15, 30, 60}:
        duration = 15

    mission = nature_service.generate_mission(
        activity_type=activity_type,
        duration_minutes=duration,
        difficulty=difficulty,
        environment=environment,
        interests=interests,
    )

    return jsonify({
        "success": True,
        "mission": mission.to_dict(),
        "message": f"Generated outdoor mission: '{mission.title}'",
    })


@missions_bp.route("/missions/<int:mission_id>")
def mission_detail(mission_id):
    """View mission details, checklist, and completion dialog."""
    mission = NatureMission.query.get_or_404(mission_id)
    return render_template("mission_detail.html", mission=mission)


@missions_bp.route("/api/missions/<int:mission_id>/complete", methods=["POST"])
def complete_mission(mission_id):
    """Mark a mission as completed by user, saving reflection and unlocking badges."""
    mission = NatureMission.query.get_or_404(mission_id)
    data = request.get_json() or request.form

    user_reflection = data.get("user_reflection", "").strip()
    outdoor_notes = data.get("outdoor_notes", "").strip()

    completion = MissionCompletion(
        mission_id=mission.id,
        user_reflection=user_reflection or None,
        outdoor_notes=outdoor_notes or None,
    )
    db.session.add(completion)
    db.session.commit()

    # Check for unlocked badges
    new_badges = nature_service.check_and_unlock_badges()
    unlocked_badge_data = [b.to_dict() for b in new_badges]

    if request.is_json:
        return jsonify({
            "success": True,
            "message": f"Great job! Mission '{mission.title}' marked complete.",
            "completion": completion.to_dict(),
            "newly_unlocked_badges": unlocked_badge_data,
        })

    flash(f"Awesome work! You completed '{mission.title}'.", "success")
    return redirect(url_for("missions.missions"))
