/**
 * NatureLens AI - Nature Explorer Client Logic
 * Handles camera capture, drag-and-drop upload, AI image inference, and journal persistence
 */

document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('upload-dropzone');
  const fileInput = document.getElementById('image-file-input');
  const cameraInput = document.getElementById('camera-file-input');
  const cameraBtn = document.getElementById('camera-btn');
  const previewBox = document.getElementById('preview-container');
  const previewImg = document.getElementById('preview-img');
  const removeBtn = document.getElementById('preview-remove-btn');
  const analyzeBtn = document.getElementById('analyze-submit-btn');
  const analyzingBox = document.getElementById('analyzing-box');
  const resultCard = document.getElementById('discovery-result-card');
  const saveJournalBtn = document.getElementById('save-journal-btn');

  let currentFile = null;
  let currentAnalysis = null;
  let currentImageFilename = null;

  // Trigger dropzone file select
  if (dropzone && fileInput) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        handleFileSelected(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelected(e.target.files[0]);
      }
    });
  }

  // Camera capture trigger
  if (cameraBtn && cameraInput) {
    cameraBtn.addEventListener('click', () => cameraInput.click());
    cameraInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        handleFileSelected(e.target.files[0]);
      }
    });
  }

  // Handle selected image
  function handleFileSelected(file) {
    if (!file.type.startsWith('image/')) {
      showToast('Please select a valid image file (PNG, JPG, WEBP).', 'warning');
      return;
    }

    if (file.size > 16 * 1024 * 1024) {
      showToast('Image file exceeds 16MB limit. Please choose a smaller photo.', 'warning');
      return;
    }

    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      previewBox.classList.remove('d-none');
      dropzone.classList.add('d-none');
      analyzeBtn.disabled = false;
      resultCard.classList.add('d-none');
    };
    reader.readAsDataURL(file);
  }

  // Remove preview
  if (removeBtn) {
    removeBtn.addEventListener('click', () => {
      currentFile = null;
      currentAnalysis = null;
      currentImageFilename = null;
      fileInput.value = '';
      if (cameraInput) cameraInput.value = '';
      previewImg.src = '';
      previewBox.classList.add('d-none');
      dropzone.classList.remove('d-none');
      analyzeBtn.disabled = true;
      resultCard.classList.add('d-none');
      analyzingBox.classList.add('d-none');
    });
  }

  // Submit image to AI endpoint
  if (analyzeBtn) {
    analyzeBtn.addEventListener('click', async () => {
      if (!currentFile) {
        showToast('Please select or capture a photo first.', 'warning');
        return;
      }

      const categoryHint = document.querySelector('input[name="category_hint"]:checked')?.value || 'unknown';
      const formData = new FormData();
      formData.append('image', currentFile);
      formData.append('category_hint', categoryHint);

      analyzeBtn.disabled = true;
      analyzingBox.classList.remove('d-none');
      resultCard.classList.add('d-none');

      try {
        const response = await fetch('/api/analyze-image', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        analyzingBox.classList.add('d-none');
        analyzeBtn.disabled = false;

        if (data.success && data.analysis) {
          currentAnalysis = data.analysis;
          currentImageFilename = data.image_filename;
          renderDiscoveryCard(data.analysis, data.image_url);
        } else {
          showToast(data.error || 'Failed to analyze nature image.', 'danger');
        }
      } catch (err) {
        analyzingBox.classList.add('d-none');
        analyzeBtn.disabled = false;
        showToast('Network error while analyzing photo. Check your connection or Ollama service.', 'danger');
      }
    });
  }

  // Render Discovery Card
  function renderDiscoveryCard(analysis, imageUrl) {
    resultCard.classList.remove('d-none');
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

    document.getElementById('res-common-name').textContent = analysis.common_name || 'Uncertain Organism';
    document.getElementById('res-scientific-name').textContent = analysis.scientific_name ? `(${analysis.scientific_name})` : '';
    
    // Category Badge
    const catBadge = document.getElementById('res-category-badge');
    const cat = analysis.category || 'unknown';
    catBadge.className = `badge-category badge-${cat}`;
    catBadge.textContent = cat;

    // Confidence Badge
    const confBadge = document.getElementById('res-confidence-badge');
    const conf = analysis.confidence_level || 'moderate';
    confBadge.className = `badge rounded-pill badge-conf-${conf}`;
    confBadge.textContent = `Confidence: ${conf.toUpperCase()}`;

    // Source Model Badge
    const modelBadge = document.getElementById('res-model-badge');
    if (analysis.is_ai_generated) {
      modelBadge.className = 'badge bg-success-subtle text-success border border-success-subtle';
      const providerLabel = analysis.provider === 'google_gemini' ? 'Google Gemini' : 'Local AI';
      modelBadge.textContent = `Identified by ${providerLabel}: ${analysis.model_used || 'AI'}`;
    } else {
      modelBadge.className = 'badge bg-warning-subtle text-warning-emphasis border border-warning-subtle';
      modelBadge.textContent = `Curated Naturalist Library (${analysis.model_used || 'Offline'})`;
    }

    // Detail text
    document.getElementById('res-characteristics').textContent = analysis.visible_characteristics || 'Observation details pending.';
    document.getElementById('res-habitat').textContent = analysis.habitat_ecology || 'Habitat context unavailable.';
    document.getElementById('res-facts').textContent = analysis.educational_facts || 'Educational facts unavailable.';
    document.getElementById('res-activity').textContent = analysis.observation_activity || 'Try observing this organism quietly in its natural habitat.';
    document.getElementById('res-limitations').textContent = analysis.limitations_notes || 'Always confirm species identification with local field guides and respect native wildlife.';

    // Reset save button state
    saveJournalBtn.disabled = false;
    saveJournalBtn.innerHTML = '<i class="bi bi-bookmark-plus me-1"></i> Save to Nature Journal';
  }

  // Save to Nature Journal
  if (saveJournalBtn) {
    saveJournalBtn.addEventListener('click', async () => {
      if (!currentAnalysis) return;

      const userNotes = document.getElementById('res-user-notes')?.value || '';
      const locationName = document.getElementById('res-location-name')?.value || '';

      saveJournalBtn.disabled = true;
      saveJournalBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';

      const payload = {
        common_name: currentAnalysis.common_name,
        scientific_name: currentAnalysis.scientific_name,
        category: currentAnalysis.category,
        confidence_level: currentAnalysis.confidence_level,
        visible_characteristics: currentAnalysis.visible_characteristics,
        habitat_ecology: currentAnalysis.habitat_ecology,
        educational_facts: currentAnalysis.educational_facts,
        observation_activity: currentAnalysis.observation_activity,
        limitations_notes: currentAnalysis.limitations_notes,
        image_filename: currentImageFilename,
        user_notes: userNotes,
        location_name: locationName,
        is_demo: !currentAnalysis.is_ai_generated,
        model_used: currentAnalysis.model_used,
      };

      try {
        const resp = await fetch('/api/journal/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        const data = await resp.json();
        if (data.success) {
          saveJournalBtn.innerHTML = '<i class="bi bi-check-circle me-1"></i> Saved to Journal!';
          saveJournalBtn.classList.replace('btn-nature-primary', 'btn-success');
          showToast('Discovery saved to your Nature Journal!', 'success');

          // Celebrate unlocked badges if any
          if (data.newly_unlocked_badges && data.newly_unlocked_badges.length > 0) {
            data.newly_unlocked_badges.forEach((b) => {
              showToast(`🏆 Badge Unlocked: "${b.name}"! ${b.description}`, 'success');
            });
          }
        } else {
          saveJournalBtn.disabled = false;
          saveJournalBtn.innerHTML = '<i class="bi bi-bookmark-plus me-1"></i> Save to Nature Journal';
          showToast(data.error || 'Failed to save discovery.', 'danger');
        }
      } catch (err) {
        saveJournalBtn.disabled = false;
        saveJournalBtn.innerHTML = '<i class="bi bi-bookmark-plus me-1"></i> Save to Nature Journal';
        showToast('Error saving discovery to journal.', 'danger');
      }
    });
  }
});
