/**
 * NatureLens AI - Mission Generator & Outdoor Tracker Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  const missionForm = document.getElementById('mission-generator-form');
  const generateBtn = document.getElementById('generate-mission-btn');
  const generatorCard = document.getElementById('active-mission-card');
  const completeModalElem = document.getElementById('completeMissionModal');
  const completeForm = document.getElementById('complete-mission-form');

  // Handle mission generation
  if (missionForm) {
    missionForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      generateBtn.disabled = true;
      generateBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Crafting Mission...';

      const formData = {
        activity_type: document.getElementById('activity_type')?.value || 'walking',
        duration_minutes: parseInt(document.getElementById('duration_minutes')?.value || 15),
        difficulty: document.getElementById('difficulty')?.value || 'easy',
        environment: document.getElementById('environment')?.value || 'park',
        interests: document.getElementById('interests')?.value || '',
      };

      try {
        const resp = await fetch('/api/missions/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        });

        const data = await resp.json();
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="bi bi-compass me-2"></i>Generate Outdoor Mission';

        if (data.success && data.mission) {
          showToast(data.message || 'Mission generated!', 'success');
          // Redirect to the newly generated mission detail page
          window.location.href = `/missions/${data.mission.id}`;
        } else {
          showToast(data.error || 'Failed to generate mission.', 'danger');
        }
      } catch (err) {
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="bi bi-compass me-2"></i>Generate Outdoor Mission';
        showToast('Error generating outdoor mission.', 'danger');
      }
    });
  }

  // Handle interactive checklist toggles on mission detail page
  const checklistCheckboxes = document.querySelectorAll('.mission-check-input');
  checklistCheckboxes.forEach((cb) => {
    cb.addEventListener('change', () => {
      const parent = cb.closest('.checklist-item');
      if (parent) {
        if (cb.checked) {
          parent.classList.add('checked');
        } else {
          parent.classList.remove('checked');
        }
      }
    });
  });

  // Handle complete mission AJAX form if present
  if (completeForm) {
    completeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const missionId = completeForm.getAttribute('data-mission-id');
      const reflection = document.getElementById('user_reflection')?.value || '';
      const notes = document.getElementById('outdoor_notes')?.value || '';
      const submitBtn = completeForm.querySelector('button[type="submit"]');

      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Saving...';

      try {
        const resp = await fetch(`/api/missions/${missionId}/complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_reflection: reflection, outdoor_notes: notes }),
        });

        const data = await resp.json();
        if (data.success) {
          // Close modal
          if (window.bootstrap && completeModalElem) {
            const modal = window.bootstrap.Modal.getInstance(completeModalElem);
            if (modal) modal.hide();
          }

          showToast(data.message, 'success');

          // Celebrate badges if unlocked
          if (data.newly_unlocked_badges && data.newly_unlocked_badges.length > 0) {
            data.newly_unlocked_badges.forEach((b) => {
              showToast(`🏆 Badge Unlocked: "${b.name}"!`, 'success');
            });
          }

          setTimeout(() => {
            window.location.href = '/missions';
          }, 1200);
        } else {
          submitBtn.disabled = false;
          submitBtn.innerHTML = 'Confirm Completion';
          showToast(data.error || 'Failed to complete mission.', 'danger');
        }
      } catch (err) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Confirm Completion';
        showToast('Error recording mission completion.', 'danger');
      }
    });
  }
});
