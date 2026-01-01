(() => {
  const searchInput = document.querySelector('#search');
  const typeFilter = document.querySelector('#type-filter');
  const grid = document.querySelector('#store-grid');

  if (!grid) return;

  function normalize(text) {
    return (text || '').toLowerCase();
  }

  function applyFilters() {
    const term = normalize(searchInput?.value);
    const type = typeFilter?.value;

    grid.querySelectorAll('.store-card').forEach((card) => {
      const name = normalize(card.dataset.name);
      const address = normalize(card.dataset.address);
      const storeType = card.dataset.type;

      const matchesTerm = !term || name.includes(term) || address.includes(term);
      const matchesType = !type || storeType === type;

      card.style.display = matchesTerm && matchesType ? 'block' : 'none';
    });
  }

  searchInput?.addEventListener('input', applyFilters);
  typeFilter?.addEventListener('change', applyFilters);
})();
