from flask import Blueprint, render_template, request, jsonify
from app.services.ai_service import NatureAIService

guide_bp = Blueprint("guide", __name__)
ai_service = NatureAIService()

# Naturalist fallback answers for common exploration queries when Ollama is offline
GUIDE_FALLBACKS = {
    "park": (
        "In a local park, look for transitions between manicured turf and unmanaged tree borders. "
        "Search under old fallen logs for woodlice, centipedes, and ground beetles (always replace logs gently). "
        "Observe the bark on mature trees for lichens, which act as living air quality indicators. "
        "Listen for high-pitched contact calls of chickadees, tits, or sparrows in dense shrubbery."
    ),
    "birds": (
        "To distinguish common birds as a beginner, observe three key traits: "
        "1. Silhouette & Beak: Stout cones (seed-eaters like finches) vs. slender needles (insect-eaters like warblers). "
        "2. Movement style: Does it hop on two feet (sparrows) or walk one foot at a time (starlings and pigeons)? "
        "3. Flight pattern: Straight and direct vs. undulating roller-coaster swoops (woodpeckers and goldfinches)."
    ),
    "bees": (
        "Bees are keystone ecosystem engineers. Beyond making honey, native wild bees pollinate over 80% of "
        "flowering plants and one-third of our human food crops. Without pollinators, fruiting shrubs and trees "
        "cannot produce berries and seeds, which collapses food webs for wild birds and small mammals."
    ),
    "garden": (
        "To start a small wildlife-friendly garden: "
        "1. Plant single-petaled native flowers (double-ruffled hybrids often lack accessible nectar). "
        "2. Provide a shallow dish with pebbles and fresh water so bees and birds can drink without drowning. "
        "3. Leave a small patch of bare soil for solitary ground-nesting bees (which rarely sting). "
        "4. Avoid synthetic pesticides and herbicides."
    ),
    "walk": (
        "For a mindful 15-minute nature walk: "
        "1. Leave your phone in your pocket or silent mode. "
        "2. Spend the first 5 minutes tuning your senses to sound: how many different bird or insect sounds do you detect? "
        "3. For the next 5 minutes, look strictly downward: notice leaf venation, soil crust, or ants along a foraging trail. "
        "4. In the final 5 minutes, look up at the tree canopy against the sky."
    ),
}

@guide_bp.route("/guide")
def guide():
    """Nature Guide conversation interface."""
    starter_prompts = [
        "What can I observe in my local park right now?",
        "How can I distinguish common backyard birds by their flight?",
        "What do solitary bees contribute to local biodiversity?",
        "How can I create a small wildlife-friendly garden corner?",
        "What sensory exercises make a 15-minute nature walk richer?",
    ]
    return render_template("guide.html", starter_prompts=starter_prompts)


@guide_bp.route("/api/guide/ask", methods=["POST"])
def ask_guide():
    """Endpoint answering nature queries using the local open-weight model or naturalist library."""
    data = request.get_json()
    if not data or not data.get("question"):
        return jsonify({"success": False, "error": "Please provide a question."}), 400

    question = data["question"].strip()
    context = data.get("context", "").strip()

    if len(question) < 3:
        return jsonify({"success": False, "error": "Question is too short."}), 400

    ai_result = ai_service.generate_nature_explanation(question, context=context)

    if ai_result.get("success"):
        return jsonify({
            "success": True,
            "answer": ai_result["explanation"],
            "model_used": ai_result.get("model_used", "Local Ollama LLM"),
            "is_ai_generated": True,
            "provider": "ollama_local",
        })

    # Graceful fallback: match keywords or provide a comprehensive thoughtful naturalist answer
    q_lower = question.lower()
    selected_answer = None
    for kw, ans in GUIDE_FALLBACKS.items():
        if kw in q_lower:
            selected_answer = ans
            break

    if not selected_answer:
        selected_answer = (
            f"Regarding '{question}': When exploring nature, begin with quiet, patient observation. "
            "Examine the physical structure of leaves, the flight behavior of birds, or the micro-habitats "
            "beneath shaded canopies. Remember to touch grass, respect living creatures, and leave no trace."
        )

    return jsonify({
        "success": True,
        "answer": selected_answer,
        "model_used": "NatureLens Field Guide (Offline Mode)",
        "is_ai_generated": False,
        "provider": "offline_naturalist_library",
        "notice": "Local Ollama server is currently offline or unreachable. Answering via the offline NatureLens Naturalist Library.",
    })
