/**
 * NatureLens AI - Core Frontend Logic
 * Service Worker Registration, AI Status Polling, Toast Notifications, Offline Detection
 */

document.addEventListener('DOMContentLoaded', () => {
  initServiceWorker();
  initNetworkStatus();
  checkAIStatus();
});

// Register PWA Service Worker
function initServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/sw.js')
      .then((reg) => {
        console.log('[NatureLens] Service Worker registered with scope:', reg.scope);
      })
      .catch((err) => {
        console.warn('[NatureLens] Service Worker registration failed:', err);
      });
  }
}

// Online / Offline Status Detection
function initNetworkStatus() {
  const offlineBanner = document.getElementById('offline-banner');

  function updateStatus() {
    if (!navigator.onLine) {
      if (offlineBanner) offlineBanner.style.display = 'block';
    } else {
      if (offlineBanner) offlineBanner.style.display = 'none';
    }
  }

  window.addEventListener('online', updateStatus);
  window.addEventListener('offline', updateStatus);
  updateStatus();
}

// Poll AI status on app startup
function checkAIStatus() {
  const statusPill = document.getElementById('ai-status-indicator');
  const statusText = document.getElementById('ai-status-text');

  fetch('/api/ai-status')
    .then((res) => res.json())
    .then((data) => {
      if (!statusPill) return;

      if (data.connected) {
        statusPill.className = 'ai-status-pill online';
        const modelLabel = data.active_model || data.gemini_model || data.vision_model_configured || 'Online';
        statusText.textContent = `AI: ${modelLabel}`;
        statusPill.title = data.status_message || 'AI service connected and ready';
      } else {
        statusPill.className = 'ai-status-pill offline';
        statusText.textContent = 'Offline / Curated Library';
        statusPill.title = data.status_message || 'AI is offline. Educational fallback active.';
      }
    })
    .catch(() => {
      if (statusPill && statusText) {
        statusPill.className = 'ai-status-pill offline';
        statusText.textContent = 'Offline Mode';
      }
    });
}

// Toast notification helper
function showToast(message, type = 'success') {
  let toastContainer = document.getElementById('nature-toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'nature-toast-container';
    toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
    toastContainer.style.zIndex = '9999';
    document.body.appendChild(toastContainer);
  }

  const toastId = 'toast-' + Date.now();
  const bgClass = type === 'success' ? 'bg-success text-white' : type === 'warning' ? 'bg-warning text-dark' : 'bg-danger text-white';
  const icon = type === 'success' ? 'bi-check-circle' : type === 'warning' ? 'bi-exclamation-triangle' : 'bi-x-circle';

  const toastHtml = `
    <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 shadow-lg" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i class="bi ${icon} fs-5"></i>
          <div>${message}</div>
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    </div>
  `;

  toastContainer.insertAdjacentHTML('beforeend', toastHtml);
  const toastElem = document.getElementById(toastId);
  if (window.bootstrap && window.bootstrap.Toast) {
    const bsToast = new window.bootstrap.Toast(toastElem, { delay: 4500 });
    bsToast.show();
  }
}
