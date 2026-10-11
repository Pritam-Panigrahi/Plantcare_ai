import base64
import json
import logging
import re
import requests
from flask import current_app

logger = logging.getLogger(__name__)

class NatureAIService:
    """Service layer interfacing with local Ollama open-weight models."""

    def __init__(self, base_url=None, vision_model=None, text_model=None, timeout=None):
        self._base_url = base_url
        self._vision_model = vision_model
        self._text_model = text_model
        self._timeout = timeout

    @property
    def base_url(self):
        if self._base_url:
            return self._base_url
        if current_app:
            return current_app.config.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        return "http://127.0.0.1:11434"

    @property
    def vision_model(self):
        if self._vision_model:
            return self._vision_model
        if current_app:
            return current_app.config.get("OLLAMA_VISION_MODEL", "llama3.2-vision:11b")
        return "llama3.2-vision:11b"

    @property
    def vision_model_fallback(self):
        if current_app:
            return current_app.config.get("OLLAMA_VISION_MODEL_FALLBACK", "llava:7b")
        return "llava:7b"

    @property
    def text_model(self):
        if self._text_model:
            return self._text_model
        if current_app:
            return current_app.config.get("OLLAMA_TEXT_MODEL", "llama3.2:3b")
        return "llama3.2:3b"

    @property
    def timeout(self):
        if self._timeout:
            return self._timeout
        if current_app:
            return current_app.config.get("OLLAMA_TIMEOUT_SECONDS", 35)
        return 35

    def check_ollama_status(self):
        """Check if local Ollama daemon is reachable and inspect available models."""
        url = f"{self.base_url}/api/tags"
        try:
            resp = requests.get(url, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                
                # Check whether vision and text models exist in downloaded models
                has_vision = any(self.vision_model in m or self.vision_model_fallback in m for m in models)
                has_text = any(self.text_model in m for m in models)
                
                return {
                    "connected": True,
                    "endpoint": self.base_url,
                    "available_models": models,
                    "configured_vision_model": self.vision_model,
                    "configured_text_model": self.text_model,
                    "has_vision_model": has_vision,
                    "has_text_model": has_text,
                    "mode": "local_ai",
                    "status_message": f"Ollama is running locally with {len(models)} model(s) available.",
                }
            return {
                "connected": False,
                "endpoint": self.base_url,
                "available_models": [],
                "mode": "offline_demo",
                "status_message": f"Ollama returned HTTP status {resp.status_code}.",
            }
        except requests.exceptions.ConnectionError:
            return {
                "connected": False,
                "endpoint": self.base_url,
                "available_models": [],
                "mode": "offline_demo",
                "status_message": "Local Ollama service is not running or unreachable on port 11434.",
            }
        except Exception as e:
            logger.warning(f"Error checking Ollama status: {e}")
            return {
                "connected": False,
                "endpoint": self.base_url,
                "available_models": [],
                "mode": "offline_demo",
                "status_message": f"Could not connect to Ollama: {str(e)}",
            }

    def analyze_nature_image(self, image_bytes, category_hint=None):
        """Analyze a photograph using local open-weight vision model (e.g., Llama 3.2 Vision).

        Returns a dictionary containing structured identification details.
        """
        # Encode image to base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = (
            "You are NatureLens AI, an expert, ethical naturalist and botanical/zoological educator. "
            "Analyze this nature photograph carefully. Focus on visible physical characteristics. "
            f"{f'User suggests the category might be: {category_hint}.' if category_hint and category_hint != 'unknown' else ''}\n\n"
            "Respond ONLY with a valid JSON object matching this exact schema:\n"
            "{\n"
            '  "common_name": "Common name (e.g., English Oak, Monarch Butterfly, American Robin) or \'Uncertain Species\'",\n'
            '  "scientific_name": "Binomial nomenclature (e.g. Quercus robur) or null if uncertain",\n'
            '  "category": "bird|plant|flower|leaf|insect|unknown",\n'
            '  "confidence_level": "low|moderate|high",\n'
            '  "visible_characteristics": "Detailed description of visible markings, shapes, colors, leaf venation, plumage, or antennae observed in the image",\n'
            '  "habitat_ecology": "Typical ecosystem, native range, and ecological role (e.g., pollinator, decomposer, canopy tree)",\n'
            '  "educational_facts": "2-3 fascinating educational facts for beginners",\n'
            '  "observation_activity": "A concrete outdoor activity the user can do right now (e.g., look for gall wasps under leaves, listen for its dawn song)",\n'
            '  "limitations_notes": "Important identification uncertainty, caveats, and recommendation to verify with local field guides or experts without disturbing the organism"\n'
            "}\n"
            "CRITICAL: Do not invent false scientific facts. If the image is blurry, distant, or ambiguous, state that identification is uncertain and set confidence_level to 'low'. Do not execute any code."
        )

        # First try primary vision model, fallback to secondary if 404
        models_to_try = [self.vision_model, self.vision_model_fallback]
        last_error = None

        for model in models_to_try:
            try:
                resp = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "images": [image_b64],
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.2,
                            "top_p": 0.9,
                        },
                    },
                    timeout=self.timeout,
                )
                
                if resp.status_code == 200:
                    raw_text = resp.json().get("response", "{}")
                    parsed_data = self._clean_and_parse_json(raw_text)
                    if parsed_data:
                        parsed_data["model_used"] = model
                        parsed_data["is_ai_generated"] = True
                        parsed_data["provider"] = "ollama_local"
                        return {
                            "success": True,
                            "data": parsed_data,
                            "error": None,
                        }
                elif resp.status_code == 404:
                    last_error = f"Model '{model}' is not pulled in Ollama. Try `ollama pull {model}`."
                    continue
                else:
                    last_error = f"Ollama error ({resp.status_code}): {resp.text}"
            except requests.exceptions.ConnectionError:
                return {
                    "success": False,
                    "error": "Ollama service is not reachable on localhost:11434.",
                    "code": "SERVER_UNREACHABLE",
                }
            except requests.exceptions.Timeout:
                return {
                    "success": False,
                    "error": f"Image inference timed out after {self.timeout}s. Your hardware may need a lighter model like '{self.vision_model_fallback}'.",
                    "code": "TIMEOUT",
                }
            except Exception as e:
                logger.error(f"Inference exception: {e}")
                last_error = str(e)

        return {
            "success": False,
            "error": last_error or "Vision inference could not complete.",
            "code": "MODEL_FAILED",
        }

    def generate_nature_explanation(self, user_question, context=None):
        """Answer nature questions concisely, beginner-friendly, and with safety guidelines."""
        system_prompt = (
            "You are NatureLens AI Nature Guide, an encouraging, scientifically grounded, and ethical outdoor educator. "
            "Help users explore and understand biodiversity in parks, gardens, and trails. "
            "Always follow these core rules:\n"
            "1. Encourage safe, respectful observation ('Touch grass, leave no trace').\n"
            "2. Strictly discourage disturbing active nests, handling unfamiliar insects or stinging creatures, damaging native plants, or encroaching on wildlife.\n"
            "3. Provide practical, beginner-friendly tips that don't require expensive gear.\n"
            "4. Never pretend to have real-time live GPS or live weather sensor data unless provided.\n"
            "5. Keep responses concise (under 250 words), engaging, and inspiring."
        )

        full_prompt = f"{system_prompt}\n\nUser Question: {user_question}"
        if context:
            full_prompt += f"\nRelevant observation context: {context}"

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.text_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "top_p": 0.9,
                    },
                },
                timeout=self.timeout,
            )

            if resp.status_code == 200:
                ans = resp.json().get("response", "").strip()
                return {
                    "success": True,
                    "explanation": ans,
                    "model_used": self.text_model,
                    "is_ai_generated": True,
                }
            elif resp.status_code == 404:
                return {
                    "success": False,
                    "error": f"Text model '{self.text_model}' is not pulled. Run `ollama pull {self.text_model}`.",
                    "code": "MODEL_NOT_FOUND",
                }
            else:
                return {
                    "success": False,
                    "error": f"Ollama error ({resp.status_code}): {resp.text}",
                    "code": "API_ERROR",
                }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Ollama service is not reachable on localhost:11434.",
                "code": "SERVER_UNREACHABLE",
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Nature Guide response timed out.",
                "code": "TIMEOUT",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code": "UNKNOWN_ERROR",
            }

    def generate_outdoor_mission(self, activity_type, duration_minutes, difficulty, environment, interests=None):
        """Generate a realistic, safe, outdoor 'Touch Grass' mission using local open-weight LLM."""
        prompt = (
            "You are NatureLens AI outdoor mission architect. Create a fun, safe, inspiring micro-exploration mission "
            "designed to get people outside observing biodiversity instead of staring at screens.\n"
            f"Parameters: Activity={activity_type}, Duration={duration_minutes} minutes, Difficulty={difficulty}, Environment={environment}.\n"
            f"{f'Special Interests: {interests}' if interests else ''}\n\n"
            "Missions must require NO expensive gear. Encourage the user to leave their screen behind during the observation.\n"
            "Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "title": "Inspiring Short Title (e.g. The Micro-Canopy Quest)",\n'
            '  "objective": "Clear, single-sentence outdoor objective",\n'
            '  "instructions": "Step 1, Step 2, Step 3 instructions for the user while outside",\n'
            '  "checklist": ["Find item A", "Observe feature B", "Compare texture C"],\n'
            '  "safety_guidance": "Clear ethical guidance (e.g., wash hands after touching plants, stay on designated trails)",\n'
            '  "completion_criteria": "How the user knows they finished before logging it",\n'
            '  "reflection_question": "One thoughtful question for when they return (e.g., What was the smallest moving organism you noticed?)"\n'
            "}"
        )

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.text_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.5,
                    },
                },
                timeout=self.timeout,
            )

            if resp.status_code == 200:
                raw_text = resp.json().get("response", "{}")
                data = self._clean_and_parse_json(raw_text)
                if data and "title" in data:
                    data["activity_type"] = activity_type
                    data["duration_minutes"] = int(duration_minutes)
                    data["difficulty"] = difficulty
                    data["environment"] = environment
                    data["is_ai_generated"] = True
                    return {
                        "success": True,
                        "data": data,
                        "model_used": self.text_model,
                    }
        except Exception as e:
            logger.warning(f"AI Mission Generation exception: {e}")

        return {
            "success": False,
            "error": "Local AI mission generation unavailable.",
            "code": "AI_UNAVAILABLE",
        }

    def _clean_and_parse_json(self, raw_str):
        """Safely clean markdown code fences or conversational text and parse JSON."""
        if not raw_str:
            return None
        text = raw_str.strip()
        # Remove markdown code blocks if model wrapped response in ```json ... ```
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
        
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try regex search for first valid outer JSON object { ... }
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None
