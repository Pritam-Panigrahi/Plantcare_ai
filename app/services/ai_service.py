import base64
import json
import logging
import os
import re
import requests
from flask import current_app

try:
    from google import genai
    from google.genai import types
    from google.genai import errors as genai_errors
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None
    genai_errors = None

logger = logging.getLogger(__name__)

class NatureAIService:
    """Service layer interfacing with Google Gemini API (primary cloud AI)

    and local Ollama open-weight models (local / fallback AI).
    """

    def __init__(
        self,
        gemini_api_key=None,
        gemini_model=None,
        base_url=None,
        vision_model=None,
        text_model=None,
        timeout=None,
    ):
        self._gemini_api_key = gemini_api_key
        self._gemini_model = gemini_model
        self._base_url = base_url
        self._vision_model = vision_model
        self._text_model = text_model
        self._timeout = timeout
        self._cached_gemini_client = None

    # -------------------------------------------------------------------------
    # Configuration Properties
    # -------------------------------------------------------------------------

    @property
    def gemini_api_key(self):
        if self._gemini_api_key:
            return self._gemini_api_key
        if current_app:
            return current_app.config.get("GEMINI_API_KEY", "")
        return os.environ.get("GEMINI_API_KEY", "")

    @property
    def has_gemini(self):
        """Check if a valid non-placeholder Gemini API key is configured."""
        key = self.gemini_api_key
        if not key or not isinstance(key, str):
            return False
        key = key.strip()
        return bool(key and key != "your_new_api_key_here")

    @property
    def gemini_model(self):
        if self._gemini_model:
            return self._gemini_model
        if current_app:
            return current_app.config.get("GEMINI_MODEL", "gemini-2.5-flash")
        return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    @property
    def gemini_fallback_model(self):
        if current_app:
            return current_app.config.get("GEMINI_FALLBACK_MODEL", "gemini-2.0-flash")
        return os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-2.0-flash")

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

    def get_gemini_client(self):
        """Lazily initialize and return the official Google GenAI client."""
        if not GENAI_AVAILABLE:
            raise RuntimeError("google-genai package is not installed.")
        if not self.has_gemini:
            raise ValueError("GEMINI_API_KEY is not configured.")
        if self._cached_gemini_client is None:
            self._cached_gemini_client = genai.Client(api_key=self.gemini_api_key.strip())
        return self._cached_gemini_client

    # -------------------------------------------------------------------------
    # Diagnostic & Status Inspection
    # -------------------------------------------------------------------------

    def check_ai_status(self):
        """Returns safe connectivity state across Gemini and local Ollama.

        Security guarantee: Never prints or exposes the actual GEMINI_API_KEY.
        """
        gemini_ready = self.has_gemini and GENAI_AVAILABLE
        ollama_status = self.check_ollama_status()

        if gemini_ready:
            return {
                "connected": True,
                "provider": "google_gemini",
                "active_model": self.gemini_model,
                "mode": f"Google Gemini ({self.gemini_model})",
                "gemini_configured": True,
                "gemini_model": self.gemini_model,
                "ollama_connected": ollama_status.get("connected", False),
                "available_models": [self.gemini_model, self.gemini_fallback_model],
                "status_message": f"Connected to Google Gemini AI via {self.gemini_model}.",
            }

        if ollama_status.get("connected"):
            return {
                "connected": True,
                "provider": "ollama_local",
                "active_model": self.vision_model,
                "mode": f"Local Open-Weight AI ({self.vision_model})",
                "gemini_configured": False,
                "gemini_model": None,
                "ollama_connected": True,
                "available_models": ollama_status.get("available_models", []),
                "status_message": ollama_status.get("status_message"),
            }

        return {
            "connected": False,
            "provider": "offline_demo",
            "active_model": "Curated Naturalist Library",
            "mode": "Offline / Curated Library Mode",
            "gemini_configured": False,
            "gemini_model": None,
            "ollama_connected": False,
            "available_models": [],
            "status_message": "No active AI provider detected. Using offline naturalist library.",
        }

    def check_ollama_status(self):
        """Check if local Ollama daemon is reachable and inspect available models."""
        url = f"{self.base_url}/api/tags"
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("name") for m in data.get("models", [])]
                has_vision = any(
                    self.vision_model in m or self.vision_model_fallback in m for m in models
                )
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
        except Exception:
            pass

        return {
            "connected": False,
            "endpoint": self.base_url,
            "available_models": [],
            "mode": "offline_demo",
            "status_message": "Local Ollama service is not running or unreachable on port 11434.",
        }

    # -------------------------------------------------------------------------
    # Feature 1: Nature Image Identification
    # -------------------------------------------------------------------------

    def analyze_nature_image(self, image_bytes, category_hint=None, mime_type="image/jpeg"):
        """Analyze a photograph using Google Gemini API (or local Ollama fallback).

        Returns a dictionary containing structured identification details.
        """
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

        # 1. Try Google Gemini API if configured
        if self.has_gemini and GENAI_AVAILABLE:
            gemini_res = self._analyze_image_gemini(image_bytes, prompt, mime_type=mime_type)
            if gemini_res.get("success"):
                return gemini_res
            logger.warning(
                f"Gemini image analysis returned error: {gemini_res.get('error')}. Attempting Ollama fallback."
            )

        # 2. Fallback to local Ollama vision model
        return self._analyze_image_ollama(image_bytes, prompt)

    def _analyze_image_gemini(self, image_bytes, prompt, mime_type="image/jpeg"):
        """Execute multimodal image analysis with google-genai SDK."""
        try:
            client = self.get_gemini_client()
            part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

            # Try primary Gemini model, fallback to secondary if model error
            models_to_try = [self.gemini_model, self.gemini_fallback_model]
            last_err = None

            for model in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=[part, prompt],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.2,
                        ),
                    )

                    if response and response.text:
                        parsed = self._clean_and_parse_json(response.text)
                        if parsed and "common_name" in parsed:
                            parsed["model_used"] = model
                            parsed["provider"] = "google_gemini"
                            parsed["is_ai_generated"] = True
                            return {
                                "success": True,
                                "data": parsed,
                                "error": None,
                            }
                except Exception as model_err:
                    last_err = model_err
                    err_msg = str(model_err)
                    if "NOT_FOUND" in err_msg or "404" in err_msg:
                        logger.warning(f"Gemini model {model} not found, trying fallback...")
                        continue
                    # Handle specific client errors
                    return self._handle_gemini_exception(model_err)

            if last_err:
                return self._handle_gemini_exception(last_err)

        except Exception as e:
            return self._handle_gemini_exception(e)

        return {
            "success": False,
            "error": "Gemini returned empty response.",
            "code": "EMPTY_RESPONSE",
        }

    def _analyze_image_ollama(self, image_bytes, prompt):
        """Execute image analysis on local Ollama daemon."""
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
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
                        "options": {"temperature": 0.2, "top_p": 0.9},
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
                    "error": f"Image inference timed out after {self.timeout}s.",
                    "code": "TIMEOUT",
                }
            except Exception as e:
                logger.error(f"Ollama inference exception: {e}")
                last_error = str(e)

        return {
            "success": False,
            "error": last_error or "Vision inference could not complete.",
            "code": "MODEL_FAILED",
        }

    # -------------------------------------------------------------------------
    # Feature 2: Nature Educational Explanations (AI Guide)
    # -------------------------------------------------------------------------

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

        # 1. Try Google Gemini API if configured
        if self.has_gemini and GENAI_AVAILABLE:
            gemini_res = self._generate_explanation_gemini(full_prompt)
            if gemini_res.get("success"):
                return gemini_res
            logger.warning(
                f"Gemini guide explanation returned error: {gemini_res.get('error')}. Attempting Ollama fallback."
            )

        # 2. Fallback to local Ollama
        return self._generate_explanation_ollama(full_prompt)

    def _generate_explanation_gemini(self, full_prompt):
        """Generate text explanation using google-genai SDK."""
        try:
            client = self.get_gemini_client()
            models_to_try = [self.gemini_model, self.gemini_fallback_model]
            last_err = None

            for model in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=full_prompt,
                        config=types.GenerateContentConfig(temperature=0.4),
                    )
                    if response and response.text:
                        return {
                            "success": True,
                            "explanation": response.text.strip(),
                            "model_used": model,
                            "provider": "google_gemini",
                            "is_ai_generated": True,
                        }
                except Exception as model_err:
                    last_err = model_err
                    if "NOT_FOUND" in str(model_err) or "404" in str(model_err):
                        continue
                    return self._handle_gemini_exception(model_err)

            if last_err:
                return self._handle_gemini_exception(last_err)
        except Exception as e:
            return self._handle_gemini_exception(e)

        return {
            "success": False,
            "error": "Gemini returned empty text response.",
            "code": "EMPTY_RESPONSE",
        }

    def _generate_explanation_ollama(self, full_prompt):
        """Generate explanation using Ollama text model."""
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.text_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": 0.4, "top_p": 0.9},
                },
                timeout=self.timeout,
            )

            if resp.status_code == 200:
                ans = resp.json().get("response", "").strip()
                return {
                    "success": True,
                    "explanation": ans,
                    "model_used": self.text_model,
                    "provider": "ollama_local",
                    "is_ai_generated": True,
                }
            elif resp.status_code == 404:
                return {
                    "success": False,
                    "error": f"Text model '{self.text_model}' is not pulled in Ollama.",
                    "code": "MODEL_NOT_FOUND",
                }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Ollama service is not reachable on localhost:11434.",
                "code": "SERVER_UNREACHABLE",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code": "UNKNOWN_ERROR",
            }

        return {
            "success": False,
            "error": "Ollama generation failed.",
            "code": "FAILED",
        }

    # -------------------------------------------------------------------------
    # Feature 3: Touch Grass Mission Generator
    # -------------------------------------------------------------------------

    def generate_outdoor_mission(
        self, activity_type, duration_minutes, difficulty, environment, interests=None
    ):
        """Generate a realistic, safe, outdoor 'Touch Grass' mission using Gemini or Ollama."""
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

        # 1. Try Google Gemini API if configured
        if self.has_gemini and GENAI_AVAILABLE:
            gemini_res = self._generate_mission_gemini(
                prompt, activity_type, duration_minutes, difficulty, environment
            )
            if gemini_res.get("success"):
                return gemini_res
            logger.warning(
                f"Gemini mission generation error: {gemini_res.get('error')}. Attempting Ollama fallback."
            )

        # 2. Fallback to Ollama
        return self._generate_mission_ollama(
            prompt, activity_type, duration_minutes, difficulty, environment
        )

    def _generate_mission_gemini(
        self, prompt, activity_type, duration_minutes, difficulty, environment
    ):
        """Generate structured mission using google-genai SDK."""
        try:
            client = self.get_gemini_client()
            models_to_try = [self.gemini_model, self.gemini_fallback_model]
            last_err = None

            for model in models_to_try:
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.5,
                        ),
                    )
                    if response and response.text:
                        data = self._clean_and_parse_json(response.text)
                        if data and "title" in data:
                            data["activity_type"] = activity_type
                            data["duration_minutes"] = int(duration_minutes)
                            data["difficulty"] = difficulty
                            data["environment"] = environment
                            data["is_ai_generated"] = True
                            data["provider"] = "google_gemini"
                            data["model_used"] = model
                            return {
                                "success": True,
                                "data": data,
                                "model_used": model,
                                "provider": "google_gemini",
                            }
                except Exception as model_err:
                    last_err = model_err
                    if "NOT_FOUND" in str(model_err) or "404" in str(model_err):
                        continue
                    return self._handle_gemini_exception(model_err)

            if last_err:
                return self._handle_gemini_exception(last_err)
        except Exception as e:
            return self._handle_gemini_exception(e)

        return {
            "success": False,
            "error": "Gemini mission generation returned invalid response.",
            "code": "FAILED",
        }

    def _generate_mission_ollama(
        self, prompt, activity_type, duration_minutes, difficulty, environment
    ):
        """Generate mission using local Ollama model."""
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.text_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.5},
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
                        "provider": "ollama_local",
                    }
        except Exception as e:
            logger.warning(f"Ollama mission generation exception: {e}")

        return {
            "success": False,
            "error": "Local AI mission generation unavailable.",
            "code": "AI_UNAVAILABLE",
        }

    # -------------------------------------------------------------------------
    # Exception & JSON Parsing Helpers
    # -------------------------------------------------------------------------

    def _handle_gemini_exception(self, exc):
        """Inspect Gemini exceptions and format clean, user-friendly error messages."""
        logger.error(f"Google Gemini API error: {exc}")
        err_str = str(exc)

        # Invalid API key
        if any(w in err_str for w in ["API_KEY_INVALID", "INVALID_ARGUMENT", "400", "403", "api_key"]):
            if "key" in err_str.lower() or "403" in err_str:
                return {
                    "success": False,
                    "error": "Invalid or unauthorized Google Gemini API key. Please verify GEMINI_API_KEY in your .env file.",
                    "code": "INVALID_API_KEY",
                }

        # Quota limits
        if any(w in err_str for w in ["RESOURCE_EXHAUSTED", "429", "quota", "rate limit"]):
            return {
                "success": False,
                "error": "Google Gemini API rate limit or quota exceeded. Please try again shortly.",
                "code": "QUOTA_EXCEEDED",
            }

        # Model not found / unsupported
        if any(w in err_str for w in ["NOT_FOUND", "404", "model"]):
            return {
                "success": False,
                "error": f"Configured Gemini model '{self.gemini_model}' is not available.",
                "code": "MODEL_NOT_FOUND",
            }

        # Network / Connection failure
        if any(w in err_str for w in ["ConnectError", "NetworkError", "timeout", "timed out"]):
            return {
                "success": False,
                "error": "Could not connect to Google Gemini service. Check your internet connection.",
                "code": "NETWORK_ERROR",
            }

        return {
            "success": False,
            "error": f"Google Gemini API error: {err_str[:160]}",
            "code": "GEMINI_ERROR",
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
