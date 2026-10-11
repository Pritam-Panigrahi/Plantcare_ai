# NatureLens AI — Outdoor Testing & Demo Recording Checklist 🌿

Use this practical checklist when taking NatureLens AI outside to test or record a demonstration video for Hacktoberfest Week 1 ("Touch Grass").

---

## 🎒 Pre-Trip Preparation (Indoors)

- [ ] **Start Local Server**: Ensure Flask is running (`python run.py`) and accessible via `http://localhost:5000` or local network IP on mobile.
- [ ] **Verify Ollama or Offline Mode**:
  - If running local AI: Ensure `ollama serve` is active and models are pulled (`ollama list`).
  - If running without Ollama: Verify that the app displays the **Offline / Curated Library Mode** badge properly.
- [ ] **Run Automated Tests**: Verify `pytest -v` shows all 24 tests passing.
- [ ] **Mobile Device Setup**: Connect your smartphone to the same local Wi-Fi or ensure the PWA is installed on your mobile home screen.

---

## 🌳 Outdoor Step 1: Mindful Observation & Mission Generation

- [ ] Open the **Touch Grass Missions** tab (`/missions`).
- [ ] Generate a 15-minute mission (e.g. *Activity: Mindful Walking, Environment: Park or Garden*).
- [ ] Review the step-by-step instructions and the observation checklist.
- [ ] **Crucial Ethos Moment**: Turn off or pocket your phone screen! Walk outdoors for 10–15 minutes with your physical senses focused on leaf shapes, bird songs, or bark patterns.

---

## 📷 Outdoor Step 2: Photography & AI Species Analysis

- [ ] Find an interesting botanical or entomological subject (e.g., an oak or maple leaf, dandelion, honeybee, or garden bird).
- [ ] Open **Nature Explorer** (`/explorer`).
- [ ] Click **"Use Camera"** to take a fresh photo or upload the image from your camera roll.
- [ ] Select the approximate category (e.g., `leaf`, `plant`, `bird`, `insect`).
- [ ] Tap **"Analyze with Local AI"**.
- [ ] Review the structured discovery card:
  - Verify common name and scientific binomial.
  - Read visible physical characteristics.
  - Review ecological role and educational facts.
  - Note the uncertainty disclaimer and ethical observation activity.

---

## 📝 Outdoor Step 3: Journaling & Badge Unlock

- [ ] Add your personal field notes (e.g., *"Observed on the shaded north side of an ancient oak"*).
- [ ] Enter the general location (e.g., *"Central Park Arboretum"*).
- [ ] Click **"Save to Nature Journal"**.
- [ ] Observe the celebratory toast when your first badge unlocks (e.g., *"First Step Outdoors"* or *"Leaf Detective"*).
- [ ] Open **Nature Journal** (`/journal`) to verify the entry is persisted with the photo, notes, and category filters.

---

## 🏆 Outdoor Step 4: Mission Reflection & Completion

- [ ] Return to the **Touch Grass Mission** page.
- [ ] Check off the items on the interactive observation checklist.
- [ ] Click **"Mark Mission Complete"**.
- [ ] Answer the reflection prompt with an authentic observation from your walk.
- [ ] Check the **Badges** page (`/progress`) to see your real active day recorded and milestone badges unlocked.

---

## 🎬 Tips for Video Walkthrough Recording

1. **Natural Sunlight**: Film a brief clip showing you walking outside near actual greenery/trees.
2. **Camera Snap**: Show the mobile screen capturing the photo in real-time.
3. **Local AI Inspection**: Point out the "Local AI" badge in the navigation bar to highlight the privacy of open-source models.
4. **End with Action**: Remind viewers of the central message: *"Look closer. Discover nature. Touch grass."*
