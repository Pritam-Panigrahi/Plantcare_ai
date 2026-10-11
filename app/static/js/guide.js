/**
 * NatureLens AI - AI Nature Guide Chat Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('guide-messages');
  const chatForm = document.getElementById('guide-chat-form');
  const questionInput = document.getElementById('guide-question-input');
  const sendBtn = document.getElementById('guide-send-btn');
  const starterChips = document.querySelectorAll('.starter-chip-btn');

  // Starter chip click listener
  starterChips.forEach((chip) => {
    chip.addEventListener('click', () => {
      const question = chip.getAttribute('data-question') || chip.textContent.trim();
      questionInput.value = question;
      sendQuestion(question);
    });
  });

  // Chat form submit
  if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const question = questionInput.value.trim();
      if (!question) return;
      sendQuestion(question);
    });
  }

  async function sendQuestion(question) {
    appendMessage(question, 'user');
    questionInput.value = '';
    sendBtn.disabled = true;

    // Append typing bubble
    const typingId = 'typing-' + Date.now();
    const typingBubble = document.createElement('div');
    typingBubble.id = typingId;
    typingBubble.className = 'guide-bubble assistant d-flex align-items-center gap-2';
    typingBubble.innerHTML = `
      <span class="spinner-grow spinner-grow-sm text-success" role="status"></span>
      <span class="text-muted fst-italic">Consulting local field knowledge...</span>
    `;
    chatMessages.appendChild(typingBubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const resp = await fetch('/api/guide/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      const data = await resp.json();
      const typingElem = document.getElementById(typingId);
      if (typingElem) typingElem.remove();

      if (data.success) {
        appendMessage(data.answer, 'assistant', data.notice, data.model_used);
      } else {
        appendMessage(data.error || 'Unable to retrieve answer.', 'assistant');
      }
    } catch (err) {
      const typingElem = document.getElementById(typingId);
      if (typingElem) typingElem.remove();
      appendMessage('Connection issue while reaching AI service. Please verify Ollama is active.', 'assistant');
    } finally {
      sendBtn.disabled = false;
      questionInput.focus();
    }
  }

  function appendMessage(text, role, notice = null, model = null) {
    const bubble = document.createElement('div');
    bubble.className = `guide-bubble ${role}`;

    let html = `<div>${escapeHtml(text)}</div>`;
    if (notice) {
      html += `<div class="mt-2 pt-2 border-top border-warning-subtle small text-warning-emphasis"><i class="bi bi-info-circle me-1"></i>${escapeHtml(notice)}</div>`;
    }
    if (model && role === 'assistant') {
      html += `<div class="mt-1 small text-muted fst-italic" style="font-size:0.75rem;"><i class="bi bi-cpu me-1"></i>${escapeHtml(model)}</div>`;
    }

    bubble.innerHTML = html;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
