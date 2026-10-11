from flask import Blueprint, render_template
from app.models import NatureDiscovery, NatureMission, NatureBadge, MissionCompletion
from app.services.nature_service import NatureService

main_bp = Blueprint("main", __name__)
nature_service = NatureService()

@main_bp.route("/")
def index():
    """NatureLens AI landing page."""
    nature_service.init_badges_if_needed()
    
    # Fetch recent discoveries for the showcase
    recent_discoveries = NatureDiscovery.query.order_by(NatureDiscovery.created_at.desc()).limit(3).all()
    
    # Counts for community / user impact
    total_discoveries = NatureDiscovery.query.count()
    completed_missions = MissionCompletion.query.count()
    unlocked_badges = NatureBadge.query.filter(NatureBadge.unlocked_at.isnot(None)).count()

    sample_card = {
        "common_name": "Monarch Butterfly",
        "scientific_name": "Danaus plexippus",
        "category": "insect",
        "confidence_level": "high",
        "visible_characteristics": "Brilliant orange wings laced with distinct black veins and a double row of white spots along margins.",
        "habitat_ecology": "Milkweed fields and gardens. Keystone pollinator undertaking phenomenal multi-generational migrations up to 3,000 miles.",
        "educational_facts": "Caterpillars ingest cardenolide toxins from milkweed plants, making both the caterpillars and adult butterflies unpalatable to predatory birds.",
        "observation_activity": "Inspect milkweed leaves for tiny pale green ribbed eggs on the undersides, or observe basking angle in early morning sun.",
    }

    return render_template(
        "index.html",
        recent_discoveries=recent_discoveries,
        total_discoveries=total_discoveries,
        completed_missions=completed_missions,
        unlocked_badges=unlocked_badges,
        sample_card=sample_card,
    )


@main_bp.route("/about")
def about():
    """Information page explaining the Touch Grass philosophy and Open-Source AI."""
    return render_template("about.html")


@main_bp.route("/offline")
def offline():
    """Offline fallback page loaded by the Service Worker when disconnected."""
    return render_template("offline.html")
