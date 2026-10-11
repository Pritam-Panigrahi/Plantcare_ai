# NatureLens AI — Touch Grass with Local Open-Source AI 🌿

*Submission for Hacktoberfest 2026: Open-Source AI Challenge (Week 1: "Touch Grass")*

---

## 💡 What I Built

**NatureLens AI** is an open-source, local-AI nature exploration companion engineered to solve a pervasive problem of modern digital life: **screen addiction and disconnection from the natural world**.

While contemporary AI applications are frequently engineered to maximize screen time through conversational chatbots and infinite feeds, NatureLens AI inverts this dynamic. Its core philosophy is:

> **"Look closer. Discover nature. Touch grass."**

NatureLens AI encourages beginners, hikers, gardeners, students, and birdwatchers to step outdoors into parks, yards, and forest trails. Users can:
1. **Photograph biodiversity**: Snap or upload pictures of birds, plants, flowers, leaves, and insects.
2. **Local AI Species Analysis**: Run open-weight vision models (such as `llama3.2-vision:11b` or `llava:7b` via Ollama) completely on-device without cloud fees or privacy invasions.
3. **Take on "Touch Grass" Missions**: Generate 10-to-60 minute outdoor micro-adventures (e.g. canopy texture mapping, pollinator censuses, avian song listening circles) with interactive checklists.
4. **Log a Personal Nature Journal**: Store observations, photos, and field notes locally in SQLite, with one-click JSON backup export.
5. **Earn Exploration Badges**: Unlock badges based strictly on verified real-world actions, with zero dark patterns or addictive game mechanics.
6. **Learn with AI Field Guide**: Ask questions about local wildlife habitats with strict ethical "Leave No Trace" boundaries.

---

## 🔗 Demo

- **Live Demo URL**: `[INSERT_YOUR_DEMO_URL_HERE]` *(e.g. https://naturelens-ai.example.com or local demo recording)*
- **Demo Video / Walkthrough**: `[INSERT_YOUR_VIDEO_DEMO_LINK_HERE]`

*(For local testing, the application runs out-of-the-box via `python run.py`, providing a complete offline naturalist library even when no GPU or Ollama instance is present!)*

---

## 💻 Code

- **GitHub Repository**: `[INSERT_YOUR_GITHUB_REPOSITORY_URL_HERE]`
- **License**: MIT License (100% open-source)

---

## 🛠️ How I Built It

### 1. Architecture & Technology Stack
- **Frontend**: Responsive, mobile-first HTML5, CSS3, Vanilla JS, Bootstrap 5, Bootstrap Icons, with a custom botanical design system (`#2E7D32` primary green, `#163A2A` forest green, `#F5F7F0` soft earth, `#B8D986` lime accent).
- **Backend**: Python 3.11+ and Flask 3.1 modular blueprints (`explorer`, `missions`, `journal`, `guide`, `progress`, `api`).
- **Database**: Flask-SQLAlchemy with SQLite for serverless local persistence.
- **Image Pipeline**: Pillow (PIL) for image integrity validation, format sanitization, resizing oversized mobile camera uploads, and preventing file spoofing or path traversal.
- **Local AI Engine**: [Ollama](https://ollama.com/) local REST API (`http://127.0.0.1:11434`):
  - **Vision-Language Model**: `llama3.2-vision:11b` (with lightweight `llava:7b` fallback for lower-VRAM machines).
  - **Text Model**: `llama3.2:3b` or `qwen2.5:3b` for the Nature Guide and mission generator.
- **Offline Resilience**: Progressive Web App (PWA) with Service Worker asset caching and an offline naturalist knowledge base for deep woodland trails without cellular connectivity.
- **Testing**: Comprehensive pytest suite (24 passing automated tests) verifying input validation, SQLite persistence, mock AI inference, error recovery, and security protections.

---

## 🌍 Why Does Open Innovation Matter?

Most consumer AI solutions depend on proprietary, closed APIs (OpenAI, Anthropic, Google). For a nature exploration companion, proprietary cloud models introduce serious friction:

1. **Absolute Privacy for Personal Media**: When users photograph their private backyards, balconies, or children examining a leaf, those photos should never be harvested to train corporate models. NatureLens AI processes images entirely on local hardware.
2. **Model Sovereignty & Customization**: Open weights empower developers to swap models (`llama3.2-vision`, `qwen2.5-vl`, `llava`, `moondream`) based on hardware capability using simple environment flags without vendor lock-in.
3. **Zero Financial Barriers**: Open-source AI eliminates token subscriptions and paywalls. Nature education should be freely accessible to students and community groups worldwide.
4. **Offline Trail Independence**: True outdoor exploration happens beyond cell tower range. Open weights running locally on a portable device or laptop ensure complete autonomy in the wild.

---

## 🤖 My Agent Session

- **AI Pair Programming Assistant**: Antigravity (Google DeepMind Advanced Agentic Coding)
- **Agent Trajectory & Logs**: `[INSERT_YOUR_AGENT_SESSION_SHARE_LINK_HERE]`

During this session, Antigravity helped architect the full-stack Flask application, write the clean botanical CSS design system, engineer the robust Ollama client with fallback parsing, implement Pillow image sanitization, and author 24 automated unit and integration tests.

---

## 🏆 Prize Categories

- **Primary Submission**: Hacktoberfest Open-Source AI Challenge — Week 1: "Touch Grass"
- *Category Consideration: `[CHECK_OFFICIAL_CHALLENGE_RULES_AND_SPECIFY_TRACK]`*
