import json
import logging
import os
import uuid
from datetime import datetime
from PIL import Image
from werkzeug.utils import secure_filename
from app.models import db, NatureDiscovery, NatureMission, MissionCompletion, NatureBadge
from app.services.ai_service import NatureAIService

logger = logging.getLogger(__name__)

# Curated Fallback Data for Offline or Demo Mode
# Clearly labeled as educational fallback; never fabricated as live AI inference
FALLBACK_DISCOVERIES = {
    "plant": {
        "common_name": "Broadleaf Plantain",
        "scientific_name": "Plantago major",
        "category": "plant",
        "confidence_level": "moderate",
        "visible_characteristics": "Rosette of broad oval leaves with prominent parallel veins running from base to tip; dense green spike inflorescence emerging vertically.",
        "habitat_ecology": "Thrives in compacted soils along walking paths, lawns, and disturbed ground worldwide. Highly resilient to foot traffic.",
        "educational_facts": "Often called 'white man's footprint' by indigenous North Americans because it spread along trading and settlement routes. Leaves have historical traditional use for soothing bug bites.",
        "observation_activity": "Find a plantain leaf and gently break a stem: observe the tough string-like vascular bundles running through each vein.",
        "limitations_notes": "Identified using offline curated botanical knowledge base. For medicinal or foraging questions, always consult accredited botanical authorities.",
        "is_demo": True,
        "model_used": "Offline Educational Library (Demo)",
    },
    "leaf": {
        "common_name": "English Oak Leaf",
        "scientific_name": "Quercus robur",
        "category": "leaf",
        "confidence_level": "high",
        "visible_characteristics": "Alternate deciduous leaves with 4 to 5 deep rounded lobes on each side, distinct short stalk (petiole), and auricles ('ear lobes') at the leaf base.",
        "habitat_ecology": "Dominant canopy tree in temperate deciduous woodlands, supporting over 280 species of insects and myriad birds and mammals.",
        "educational_facts": "A single mature oak tree can host thousands of micro-organisms, gall wasps, lichens, and mosses, forming a self-contained ecological community.",
        "observation_activity": "Flip the leaf over with a magnifying glass or your camera lens. Look for tiny spangle galls or silk cocoons created by micro-wasps.",
        "limitations_notes": "Offline botanical profile. Note that Quercus robur hybridizes with Quercus petraea (Sessile Oak); stalk length is the key distinguishing diagnostic.",
        "is_demo": True,
        "model_used": "Offline Educational Library (Demo)",
    },
    "flower": {
        "common_name": "Common Dandelion",
        "scientific_name": "Taraxacum officinale",
        "category": "flower",
        "confidence_level": "high",
        "visible_characteristics": "Bright golden-yellow composite flower head made of numerous ray florets; hollow milky stem; deeply toothed basal leaves resembling lion's teeth.",
        "habitat_ecology": "Crucial early-spring food source for emerging bumblebees and solitary bees when few other nectar sources are in bloom.",
        "educational_facts": "The entire flower closes tightly at night and during rain to protect pollen from dampness. The clock seed head (pappus) allows seeds to drift miles on wind currents.",
        "observation_activity": "Observe the dandelion at mid-day versus sunset: observe how its bracts fold upward to shelter the florets as the sun dips.",
        "limitations_notes": "Offline floral profile. There are hundreds of dandelion micro-species with subtle differences in bract reflexing.",
        "is_demo": True,
        "model_used": "Offline Educational Library (Demo)",
    },
    "bird": {
        "common_name": "European Robin",
        "scientific_name": "Erithacus rubecula",
        "category": "bird",
        "confidence_level": "moderate",
        "visible_characteristics": "Distinctive orange-red breast and face bordered by grey, olive-brown upperparts, pale belly, and large dark inquisitive eyes.",
        "habitat_ecology": "Common across woodlands, hedgerows, and suburban gardens. Territorial ground-forager following gardeners and digging animals for worms.",
        "educational_facts": "Both male and female robins sing during the winter to maintain separate feeding territories. They possess a magnetic compass in their eyes based on cryptochrome proteins.",
        "observation_activity": "Stay still near a garden patch or park bench for 5 minutes. Notice if a robin perches nearby cocking its head to visually scan for soil movement.",
        "limitations_notes": "Offline ornithological profile. Never approach active bird nests or use audio playback calls that cause unnecessary territorial stress.",
        "is_demo": True,
        "model_used": "Offline Educational Library (Demo)",
    },
    "insect": {
        "common_name": "Western Honeybee",
        "scientific_name": "Apis mellifera",
        "category": "insect",
        "confidence_level": "high",
        "visible_characteristics": "Golden-brown and black banded abdomen, hairy thorax, pollen baskets (corbiculae) visible on hind legs, and two pairs of translucent wings.",
        "habitat_ecology": "Vital generalist pollinator visiting flowers in gardens, meadows, and orchards. Highly social species living in perennial colonies with division of labor.",
        "educational_facts": "Communicates distance and direction to rich nectar patches via the famous 'waggle dance'. A single worker bee makes about 1/12th of a teaspoon of honey in her lifetime.",
        "observation_activity": "Watch a honeybee landing on a blossom without moving too close. Can you see colored pollen pellets packed onto her hind legs?",
        "limitations_notes": "Offline entomological profile. Do not attempt to catch or touch bees. Observe quietly from at least two feet away.",
        "is_demo": True,
        "model_used": "Offline Educational Library (Demo)",
    },
    "unknown": {
        "common_name": "Field Lichen & Moss Patch",
        "scientific_name": "Symbiotic Lichen community",
        "category": "unknown",
        "confidence_level": "low",
        "visible_characteristics": "Crustose or foliose green-grey patches adhering tightly to bark, rock, or ground, interspersed with velvety moss cushions.",
        "habitat_ecology": "Pioneer organisms that can survive extreme drought and cold. Essential bio-indicators of atmospheric air quality and nitrogen levels.",
        "educational_facts": "Lichen is not a single plant, but a composite organism formed by a symbiotic partnership between fungi and photosynthesizing algae or cyanobacteria.",
        "observation_activity": "Mist a dry patch of moss with a tiny drop of water and watch how rapidly the cells re-hydrate and expand in color.",
        "limitations_notes": "Offline baseline profile. Visual identification of lichens and cryptogams often requires chemical spot tests or microscopy. Observe safely in situ.",
        "is_demo": True,
        "model_used": "Offline Educational Library (Demo)",
    },
}

FALLBACK_MISSIONS = [
    {
        "title": "The Micro-Leaf Architecture Quest",
        "activity_type": "walking",
        "duration_minutes": 15,
        "difficulty": "easy",
        "environment": "park",
        "objective": "Observe three distinctly shaped leaves and compare their vein structures without detaching them.",
        "instructions": "1. Put your smartphone in your pocket and take a mindful 5-minute stroll.\n2. Locate three different plants or trees within 20 paces of each other.\n3. Gently turn a leaf over on each plant to inspect the underside veins.\n4. Note whether the veins are parallel, pinnate (feather-like), or palmate (hand-like).",
        "checklist": [
            "Find a leaf with smooth edges (entire margin)",
            "Find a leaf with jagged or serrated edges",
            "Observe the main vein connection at the petiole",
            "Feel the difference in texture between top and bottom surfaces"
        ],
        "safety_guidance": "Do not tear leaves from branches. Avoid touching poison ivy, stinging nettles, or unidentified spiny foliage. Wash your hands when you return indoors.",
        "completion_criteria": "You examined three different leaf structures with your eyes and recorded their differences.",
        "reflection_question": "Which leaf had the thickest protective waxy cuticle, and why might that tree need it in its environment?"
    },
    {
        "title": "The 10-Minute Pollinator Census",
        "activity_type": "gardening",
        "duration_minutes": 10,
        "difficulty": "easy",
        "environment": "garden",
        "objective": "Sit motionless beside flowering plants and tally visiting pollinators.",
        "instructions": "1. Find a sunny patch of blooming flowers or clover in a garden or green verge.\n2. Sit or stand quietly at least 3 feet away so your shadow does not fall on the blooms.\n3. Count how many individual insects (bees, flies, butterflies, beetles) land on flowers within 10 minutes.\n4. Notice whether different species favor different flower colors.",
        "checklist": [
            "Find a flowering plant in direct sunlight",
            "Spot at least one bee or hoverfly foraging",
            "Observe whether the insect stays on one flower or moves rapidly",
            "Take a deep breath and listen to the ambient insect hum"
        ],
        "safety_guidance": "Keep calm and do not swat at insects. Bees and pollinators are busy foraging and will not bother you if unprovoked.",
        "completion_criteria": "You observed pollinator activity for a full 10 minutes without checking your phone screen.",
        "reflection_question": "Did you see any hoverflies disguised as bees (Batesian mimicry)? How could you tell them apart?"
    },
    {
        "title": "Bark Texture & Lichen Map",
        "activity_type": "exploration",
        "duration_minutes": 20,
        "difficulty": "moderate",
        "environment": "forest_trail",
        "objective": "Explore micro-ecosystems living on the trunks of older trees.",
        "instructions": "1. Walk along a trail or wooded path until you spot three distinct mature trees.\n2. Inspect the bark texture: is it furrowed, peeling, smooth, or plated?\n3. Look for lichens, moss cushions, and spider retreat webs nestled into crevices.\n4. Check if moss grows predominantly on one directional side of the trunk.",
        "checklist": [
            "Identify an old tree with deeply furrowed bark",
            "Find a patch of green or grey lichen on the bark",
            "Look for evidence of insect borers or woodpecker pecks",
            "Feel the temperature difference between shaded and sunlit bark"
        ],
        "safety_guidance": "Stay on marked trails to protect sensitive understory vegetation and avoid disturbing ground-nesting creatures.",
        "completion_criteria": "You investigated three tree trunks up close and discovered at least one symbiotic organism.",
        "reflection_question": "Why does bark texture matter so much to the insects and birds that inhabit a forest?"
    },
    {
        "title": "Avian Songscape Listening Circle",
        "activity_type": "birdwatching",
        "duration_minutes": 15,
        "difficulty": "easy",
        "environment": "neighbourhood",
        "objective": "Tune your ears to local bird vocalizations and map where sounds originate.",
        "instructions": "1. Step outdoors into your backyard, balcony, or quiet street corner.\n2. Close your eyes for 3 minutes to reset your sensory focus.\n3. Count how many distinctly different bird calls or songs you can hear around you.\n4. Point your arm toward each sound source to mentally map their positions.",
        "checklist": [
            "Close eyes and listen quietly for 3 minutes",
            "Identify at least 2 distinct bird pitches or patterns",
            "Locate one perched songbird with your eyes after hearing it",
            "Distinguish between a melodic song and an alarm chip"
        ],
        "safety_guidance": "Be mindful of your footing and traffic if you are walking near streets. Do not use digital playback lures.",
        "completion_criteria": "You spent 15 minutes listening attentively to local bird songs.",
        "reflection_question": "Did the birds pause singing when people or cars passed by, and how quickly did they resume?"
    }
]

INITIAL_BADGES = [
    {
        "slug": "first-step",
        "name": "First Step Outdoors",
        "description": "Logged your first real-world nature discovery in your personal journal.",
        "icon": "compass",
        "category": "milestone",
        "criteria_type": "discoveries_count",
        "criteria_threshold": 1,
    },
    {
        "slug": "curious-observer",
        "name": "Curious Observer",
        "description": "Logged 5 observations of wildlife, flora, or insects.",
        "icon": "eye",
        "category": "milestone",
        "criteria_type": "discoveries_count",
        "criteria_threshold": 5,
    },
    {
        "slug": "master-naturalist",
        "name": "Master Naturalist",
        "description": "Logged 15 nature observations in your personal exploration journal.",
        "icon": "award",
        "category": "milestone",
        "criteria_type": "discoveries_count",
        "criteria_threshold": 15,
    },
    {
        "slug": "leaf-detective",
        "name": "Leaf Detective",
        "description": "Identified and cataloged at least 2 distinct leaves or plant specimens.",
        "icon": "tree",
        "category": "flora",
        "criteria_type": "specific_category",
        "criteria_threshold": 2,
        "criteria_value": "leaf",
    },
    {
        "slug": "feather-finder",
        "name": "Feather Finder",
        "description": "Observed and logged at least 2 bird species in their natural habitat.",
        "icon": "feather",
        "category": "fauna",
        "criteria_type": "specific_category",
        "criteria_threshold": 2,
        "criteria_value": "bird",
    },
    {
        "slug": "pollinator-pal",
        "name": "Pollinator Pal",
        "description": "Spotted and recorded at least 2 insect or pollinator species.",
        "icon": "bug",
        "category": "fauna",
        "criteria_type": "specific_category",
        "criteria_threshold": 2,
        "criteria_value": "insect",
    },
    {
        "slug": "touch-grass-initiate",
        "name": "Touch Grass Initiate",
        "description": "Completed your first outdoor mission away from digital screens.",
        "icon": "footprints",
        "category": "missions",
        "criteria_type": "missions_count",
        "criteria_threshold": 1,
    },
    {
        "slug": "outdoor-explorer",
        "name": "Dedicated Explorer",
        "description": "Completed 3 distinct outdoor exploration missions.",
        "icon": "map",
        "category": "missions",
        "criteria_type": "missions_count",
        "criteria_threshold": 3,
    },
    {
        "slug": "biodiversity-champion",
        "name": "Biodiversity Champion",
        "description": "Explored and logged discoveries across at least 4 nature categories.",
        "icon": "sun",
        "category": "milestone",
        "criteria_type": "categories_count",
        "criteria_threshold": 4,
    },
]


class NatureService:
    """Business logic for NatureLens AI explorer, journal, missions, and badges."""

    def __init__(self, ai_service=None):
        self.ai_service = ai_service or NatureAIService()

    def process_and_save_upload(self, file_storage, upload_folder, max_dimension=1600):
        """Safely validate, sanitize, and persist an uploaded image.
        
        Validates content using Pillow, resizes large mobile photos, and stores with UUID.
        """
        if not file_storage or file_storage.filename == "":
            raise ValueError("No file provided.")

        filename = secure_filename(file_storage.filename)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in {"png", "jpg", "jpeg", "webp"}:
            raise ValueError(f"Unsupported file format: .{ext}. Allowed: png, jpg, jpeg, webp.")

        # Read into Pillow to verify it is genuinely a valid image (prevents disguised files)
        try:
            image = Image.open(file_storage.stream)
            image.verify()  # Verify integrity
            file_storage.stream.seek(0)
            image = Image.open(file_storage.stream)  # Re-open for conversion
        except Exception as e:
            raise ValueError(f"Corrupted or invalid image file: {e}")

        # Convert RGBA to RGB for JPEG compatibility if needed
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            ext = "jpg"

        # Downscale oversized mobile camera uploads to protect memory and bandwidth
        if max(image.size) > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        unique_filename = f"nature_{uuid.uuid4().hex[:12]}.{ext if ext != 'jpeg' else 'jpg'}"
        os.makedirs(upload_folder, exist_ok=True)
        save_path = os.path.join(upload_folder, unique_filename)

        image.save(save_path, quality=85, optimize=True)
        return unique_filename, save_path

    def analyze_image_with_fallback(self, image_path, category_hint=None):
        """Analyzes image using Ollama. If Ollama is unavailable, uses curated fallback."""
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        ai_res = self.ai_service.analyze_nature_image(image_bytes, category_hint=category_hint)
        
        if ai_res.get("success"):
            return ai_res["data"]

        # If AI unavailable, return curated fallback corresponding to category hint
        cat = category_hint if category_hint in FALLBACK_DISCOVERIES else "unknown"
        fallback = FALLBACK_DISCOVERIES[cat].copy()
        fallback["ai_error_note"] = ai_res.get("error", "Local AI server unavailable")
        fallback["is_ai_generated"] = False
        fallback["provider"] = "Curated Naturalist Library (Offline Mode)"
        return fallback

    def generate_mission(self, activity_type, duration_minutes, difficulty, environment, interests=None):
        """Generate a mission using local Ollama LLM, or pick curated mission on fallback."""
        ai_res = self.ai_service.generate_outdoor_mission(
            activity_type=activity_type,
            duration_minutes=duration_minutes,
            difficulty=difficulty,
            environment=environment,
            interests=interests,
        )

        if ai_res.get("success"):
            data = ai_res["data"]
            mission = NatureMission(
                title=data.get("title", "Outdoor Observation Mission"),
                activity_type=activity_type,
                duration_minutes=int(duration_minutes),
                difficulty=difficulty,
                environment=environment,
                objective=data.get("objective", "Observe biodiversity closely."),
                instructions=data.get("instructions", "Step outside and observe quietly."),
                checklist_raw=json.dumps(data.get("checklist", ["Observe your surroundings"])),
                safety_guidance=data.get("safety_guidance", "Respect nature and leave no trace."),
                completion_criteria=data.get("completion_criteria", "Complete observation checklist."),
                reflection_question=data.get("reflection_question", "What surprised you most?"),
                is_ai_generated=True,
            )
            db.session.add(mission)
            db.session.commit()
            return mission

        # Fallback to curated mission
        selected_template = None
        for m in FALLBACK_MISSIONS:
            if m["activity_type"] == activity_type or m["environment"] == environment:
                selected_template = m
                break
        if not selected_template:
            selected_template = FALLBACK_MISSIONS[0]

        mission = NatureMission(
            title=selected_template["title"],
            activity_type=activity_type,
            duration_minutes=int(duration_minutes),
            difficulty=difficulty,
            environment=environment,
            objective=selected_template["objective"],
            instructions=selected_template["instructions"],
            checklist_raw=json.dumps(selected_template["checklist"]),
            safety_guidance=selected_template["safety_guidance"],
            completion_criteria=selected_template["completion_criteria"],
            reflection_question=selected_template["reflection_question"],
            is_ai_generated=False,
        )
        db.session.add(mission)
        db.session.commit()
        return mission

    def init_badges_if_needed(self):
        """Seed initial nature badges into database if table is empty."""
        existing_count = NatureBadge.query.count()
        if existing_count == 0:
            for b in INITIAL_BADGES:
                badge = NatureBadge(
                    slug=b["slug"],
                    name=b["name"],
                    description=b["description"],
                    icon=b["icon"],
                    category=b["category"],
                    criteria_type=b["criteria_type"],
                    criteria_threshold=b["criteria_threshold"],
                    criteria_value=b.get("criteria_value"),
                )
                db.session.add(badge)
            db.session.commit()

    def check_and_unlock_badges(self):
        """Inspect user's logged discoveries and mission completions, unlocking badges."""
        self.init_badges_if_needed()

        discoveries_count = NatureDiscovery.query.count()
        missions_count = MissionCompletion.query.count()
        distinct_categories = [
            row[0]
            for row in db.session.query(NatureDiscovery.category)
            .distinct()
            .filter(NatureDiscovery.category != "unknown")
            .all()
        ]
        categories_count = len(distinct_categories)

        newly_unlocked = []
        all_badges = NatureBadge.query.all()

        for badge in all_badges:
            if badge.is_unlocked:
                continue

            should_unlock = False
            if badge.criteria_type == "discoveries_count":
                if discoveries_count >= badge.criteria_threshold:
                    should_unlock = True
            elif badge.criteria_type == "missions_count":
                if missions_count >= badge.criteria_threshold:
                    should_unlock = True
            elif badge.criteria_type == "categories_count":
                if categories_count >= badge.criteria_threshold:
                    should_unlock = True
            elif badge.criteria_type == "specific_category":
                cat_count = NatureDiscovery.query.filter_by(category=badge.criteria_value).count()
                # If specific category matches either "leaf" or "plant"
                if badge.criteria_value == "leaf":
                    cat_count += NatureDiscovery.query.filter_by(category="plant").count()
                if cat_count >= badge.criteria_threshold:
                    should_unlock = True

            if should_unlock:
                badge.unlocked_at = datetime.utcnow()
                newly_unlocked.append(badge)

        if newly_unlocked:
            db.session.commit()

        return newly_unlocked

    def get_user_progress_summary(self):
        """Calculate verified statistics about user's outdoor exploration."""
        self.init_badges_if_needed()
        self.check_and_unlock_badges()

        discoveries_count = NatureDiscovery.query.count()
        missions_count = MissionCompletion.query.count()
        
        categories_query = (
            db.session.query(NatureDiscovery.category, db.func.count(NatureDiscovery.id))
            .group_by(NatureDiscovery.category)
            .all()
        )
        category_breakdown = {cat: count for cat, count in categories_query}

        badges = NatureBadge.query.order_by(NatureBadge.id.asc()).all()
        unlocked_badges = [b for b in badges if b.is_unlocked]

        # Calculate active days from discoveries and mission completions
        discovery_dates = [
            d[0].strftime("%Y-%m-%d")
            for d in db.session.query(NatureDiscovery.created_at).all()
            if d[0]
        ]
        mission_dates = [
            m[0].strftime("%Y-%m-%d")
            for m in db.session.query(MissionCompletion.completed_at).all()
            if m[0]
        ]
        active_unique_days = len(set(discovery_dates + mission_dates))

        return {
            "discoveries_count": discoveries_count,
            "missions_completed": missions_count,
            "categories_explored": len([c for c in category_breakdown.keys() if c != "unknown"]),
            "category_breakdown": category_breakdown,
            "active_days_count": active_unique_days,
            "total_badges": len(badges),
            "unlocked_badges_count": len(unlocked_badges),
            "badges": [b.to_dict() for b in badges],
        }
