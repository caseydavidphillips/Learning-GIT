(function () {
  const list = document.getElementById('fail-list');
  if (!list) return;

  const items = Array.from(list.querySelectorAll('.fail-item'));

  // Compute counts from rendered items.
  let failed = 0;
  let errors = 0;

  items.forEach(item => {
    const kind = (item.querySelector('.fail-kind')?.textContent || '').toUpperCase();
    if (kind === 'FAILURE') failed++;
    else if (kind === 'ERROR') errors++;
  });

  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = String(value);
  };

  // Update counts.
  setText('count-failed', failed);
  setText('count-errors', errors);

  // Empty state
  const empty = document.getElementById('fail-empty');
  if (empty) empty.hidden = items.length !== 0;

  // Filters + search
  const filters = { failure: true, error: true };

  const applyFilters = () => {
    const query = (document.getElementById('fail-search')?.value || '').toLowerCase();

    items.forEach(item => {
      const kind = (item.querySelector('.fail-kind')?.textContent || '').toUpperCase();

      const typeOk =
        (kind === 'FAILURE' && filters.failure) ||
        (kind === 'ERROR' && filters.error);

      const textOk = !query || item.textContent.toLowerCase().includes(query);

      item.style.display = (typeOk && textOk) ? '' : 'none';
    });
  };

  // Wire filter toggles (elements with data-filter="failure|error")
  document.querySelectorAll('[data-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
      const type = btn.dataset.filter;
      filters[type] = !filters[type];
      btn.classList.toggle('inactive', !filters[type]);
      applyFilters();
    });
  });

  const search = document.getElementById('fail-search');
  if (search) search.addEventListener('input', applyFilters);

  applyFilters();
})();