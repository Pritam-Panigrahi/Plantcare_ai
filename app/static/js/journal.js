/**
 * NatureLens AI - Nature Journal Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('journal-search-input');
  const journalGrid = document.getElementById('journal-cards-grid');
  const journalCards = document.querySelectorAll('.journal-entry-card');

  // Client-side quick filter on input
  if (searchInput && journalCards.length > 0) {
    searchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      let matchCount = 0;

      journalCards.forEach((card) => {
        const text = card.textContent.toLowerCase();
        if (text.includes(query)) {
          card.style.display = '';
          matchCount++;
        } else {
          card.style.display = 'none';
        }
      });

      const noMatchElem = document.getElementById('journal-no-matches');
      if (noMatchElem) {
        if (matchCount === 0 && query.length > 0) {
          noMatchElem.classList.remove('d-none');
        } else {
          noMatchElem.classList.add('d-none');
        }
      }
    });
  }
});
