import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class NatureDiscovery(db.Model):
    """Stores nature discoveries identified by AI or logged by the user."""
    __tablename__ = "nature_discoveries"

    id = db.Column(db.Integer, primary_key=True)
    common_name = db.Column(db.String(150), nullable=False, index=True)
    scientific_name = db.Column(db.String(150), nullable=True)
    category = db.Column(db.String(50), nullable=False, default="unknown", index=True)
    # bird, plant, flower, leaf, insect, unknown
    
    # AI Analysis & Confidence
    confidence_level = db.Column(db.String(50), default="moderate")  # "low", "moderate", "high"
    visible_characteristics = db.Column(db.Text, nullable=True)
    habitat_ecology = db.Column(db.Text, nullable=True)
    educational_facts = db.Column(db.Text, nullable=True)
    observation_activity = db.Column(db.Text, nullable=True)
    limitations_notes = db.Column(db.Text, nullable=True)
    
    # Metadata & User input
    image_filename = db.Column(db.String(255), nullable=True)
    user_notes = db.Column(db.Text, nullable=True)
    location_name = db.Column(db.String(150), nullable=True)
    is_demo = db.Column(db.Boolean, default=False)
    model_used = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        """Serialize discovery to dictionary for API responses."""
        return {
            "id": self.id,
            "common_name": self.common_name,
            "scientific_name": self.scientific_name or "",
            "category": self.category,
            "confidence_level": self.confidence_level,
            "visible_characteristics": self.visible_characteristics or "",
            "habitat_ecology": self.habitat_ecology or "",
            "educational_facts": self.educational_facts or "",
            "observation_activity": self.observation_activity or "",
            "limitations_notes": self.limitations_notes or "",
            "image_filename": self.image_filename,
            "image_url": f"/uploads/{self.image_filename}" if self.image_filename else None,
            "user_notes": self.user_notes or "",
            "location_name": self.location_name or "",
            "is_demo": bool(self.is_demo),
            "model_used": self.model_used or "Unknown",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
        }

    def __repr__(self):
        return f"<NatureDiscovery {self.id}: {self.common_name} ({self.category})>"


class NatureMission(db.Model):
    """Stores outdoor nature exploration missions."""
    __tablename__ = "nature_missions"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False, default="walking")
    # walking, birdwatching, gardening, photography, exploration
    duration_minutes = db.Column(db.Integer, nullable=False, default=15)
    difficulty = db.Column(db.String(50), nullable=False, default="easy")
    # easy, moderate, challenging
    environment = db.Column(db.String(50), nullable=False, default="park")
    # garden, park, neighbourhood, forest_trail
    
    objective = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    checklist_raw = db.Column(db.Text, nullable=False)  # JSON-encoded array of task strings
    safety_guidance = db.Column(db.Text, nullable=False)
    completion_criteria = db.Column(db.Text, nullable=False)
    reflection_question = db.Column(db.Text, nullable=False)
    is_ai_generated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    completions = db.relationship("MissionCompletion", backref="mission", cascade="all, delete-orphan", lazy=True)

    @property
    def checklist(self):
        """Return parsed list of checklist items."""
        try:
            return json.loads(self.checklist_raw)
        except (ValueError, TypeError):
            return [line.strip("- *") for line in self.checklist_raw.splitlines() if line.strip()]

    @checklist.setter
    def checklist(self, items):
        self.checklist_raw = json.dumps(items if isinstance(items, list) else [items])

    @property
    def is_completed(self):
        return len(self.completions) > 0

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "activity_type": self.activity_type,
            "duration_minutes": self.duration_minutes,
            "difficulty": self.difficulty,
            "environment": self.environment,
            "objective": self.objective,
            "instructions": self.instructions,
            "checklist": self.checklist,
            "safety_guidance": self.safety_guidance,
            "completion_criteria": self.completion_criteria,
            "reflection_question": self.reflection_question,
            "is_ai_generated": self.is_ai_generated,
            "is_completed": self.is_completed,
            "completions_count": len(self.completions),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
        }

    def __repr__(self):
        return f"<NatureMission {self.id}: {self.title}>"


class MissionCompletion(db.Model):
    """Records real user completion of an outdoor mission."""
    __tablename__ = "mission_completions"

    id = db.Column(db.Integer, primary_key=True)
    mission_id = db.Column(db.Integer, db.ForeignKey("nature_missions.id"), nullable=False, index=True)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_reflection = db.Column(db.Text, nullable=True)
    outdoor_notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "mission_id": self.mission_id,
            "completed_at": self.completed_at.strftime("%Y-%m-%d %H:%M"),
            "user_reflection": self.user_reflection or "",
            "outdoor_notes": self.outdoor_notes or "",
        }


class NatureBadge(db.Model):
    """Represents outdoor exploration badges unlocked by verified user activities."""
    __tablename__ = "nature_badges"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), nullable=False, default="award")
    category = db.Column(db.String(50), default="milestone")
    unlocked_at = db.Column(db.DateTime, nullable=True)
    criteria_type = db.Column(db.String(50), nullable=False)
    # criteria types:
    # "discoveries_count", "missions_count", "categories_count", "specific_category"
    criteria_threshold = db.Column(db.Integer, default=1)
    criteria_value = db.Column(db.String(50), nullable=True)  # e.g., category name for "specific_category"

    @property
    def is_unlocked(self):
        return self.unlocked_at is not None

    def to_dict(self):
        return {
            "id": self.id,
            "slug": self.slug,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "is_unlocked": self.is_unlocked,
            "unlocked_at": self.unlocked_at.strftime("%Y-%m-%d %H:%M") if self.unlocked_at else None,
            "criteria_type": self.criteria_type,
            "criteria_threshold": self.criteria_threshold,
        }

    def __repr__(self):
        return f"<NatureBadge {self.slug} - {'Unlocked' if self.is_unlocked else 'Locked'}>"
