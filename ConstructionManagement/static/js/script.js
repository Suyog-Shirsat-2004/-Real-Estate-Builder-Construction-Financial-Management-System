/* Real Estate Builder - UI behaviour and animations */
document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.getElementById('appSidebar');
  const backdrop = document.getElementById('sidebarBackdrop');
  const toggle = document.getElementById('sidebarToggle');
  const close = document.getElementById('sidebarClose');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('sidebar-open');
    if (backdrop) backdrop.classList.add('show');
  }
  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('sidebar-open');
    if (backdrop) backdrop.classList.remove('show');
  }

  if (toggle) toggle.addEventListener('click', openSidebar);
  if (close) close.addEventListener('click', closeSidebar);
  if (backdrop) backdrop.addEventListener('click', closeSidebar);

  // Highlight the active sidebar link based on the current path.
  const current = window.location.pathname.replace(/\/$/, '');
  document.querySelectorAll('.sidebar-nav .nav-link').forEach(function (link) {
    const href = (link.getAttribute('href') || '').replace(/\/$/, '');
    if (href && current === href) link.classList.add('active');
  });

  // Reveal cards/sections as they scroll into view.
  const revealItems = document.querySelectorAll('.reveal');
  if (revealItems.length) {
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.08 });
      revealItems.forEach(function (item) { observer.observe(item); });
    } else {
      revealItems.forEach(function (item) { item.classList.add('is-visible'); });
    }
  }

  // ---- Clickable dashboard cards -> deep detail modal ----
  const modalEl = document.getElementById('dashboardDetailModal');
  const detailBody = document.getElementById('dashboardDetailBody');
  const detailTitle = document.getElementById('dashboardDetailTitle');
  const detailSubtitle = document.getElementById('dashboardDetailSubtitle');
  const detailIcon = document.getElementById('dashboardDetailIcon');
  const detailModal = (modalEl && window.bootstrap) ? bootstrap.Modal.getOrCreateInstance(modalEl) : null;

  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch];
    });
  }

  function safeBadge(value) {
    return /^[a-z0-9-]+$/.test(String(value)) ? value : 'secondary';
  }

  function renderDetail(data) {
    detailTitle.textContent = data.title || 'Details';
    detailSubtitle.textContent = data.subtitle || '';
    if (detailIcon) detailIcon.className = 'bi ' + (data.icon || 'bi-list-ul');

    const sections = Array.isArray(data.sections) ? data.sections : [];
    if (!sections.length) {
      detailBody.innerHTML = '<div class="p-4 text-muted">No records found.</div>';
      return;
    }

    let html = '<div class="reb-detail-wrap">';
    sections.forEach(function (section) {
      const rows = Array.isArray(section.rows) ? section.rows : [];
      html += '<section class="reb-detail-section">';
      html += '<h6 class="reb-detail-heading"><span>' + escapeHtml(section.heading) + '</span>' +
              '<span class="badge bg-light text-secondary border">' + rows.length + ' record' + (rows.length === 1 ? '' : 's') + '</span></h6>';
      if (!rows.length) {
        html += '<div class="reb-detail-empty">No records in this section.</div>';
      } else {
        html += '<div class="reb-detail-grid">';
        rows.forEach(function (row) {
          const tag = row.link ? 'a' : 'div';
          const attrs = row.link ? ' href="' + escapeHtml(row.link) + '"' : '';
          html += '<' + tag + ' class="reb-detail-row"' + attrs + '>';
          html += '<span class="reb-detail-label">' + escapeHtml(row.label) + '</span>';
          html += '<span class="reb-detail-value">';
          if (row.badge) {
            html += '<span class="badge bg-' + safeBadge(row.badge) + '">' + escapeHtml(row.badge_label || row.value) + '</span> ';
          }
          html += escapeHtml(row.value) + '</span>';
          if (row.note) html += '<span class="reb-detail-note">' + escapeHtml(row.note) + '</span>';
          if (row.link) html += '<i class="bi bi-arrow-up-right reb-detail-arrow"></i>';
          html += '</' + tag + '>';
        });
        html += '</div>';
      }
      html += '</section>';
    });
    html += '</div>';
    detailBody.innerHTML = html;
    detailBody.scrollTop = 0;
  }

  function showLoading(label) {
    detailTitle.textContent = label || 'Details';
    detailSubtitle.textContent = 'Loading live records...';
    if (detailIcon) detailIcon.className = 'bi bi-hourglass-split';
    detailBody.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div>' +
                           '<div class="small text-muted mt-2">Fetching details</div></div>';
    detailBody.scrollTop = 0;
  }

  document.addEventListener('click', function (event) {
    const card = event.target.closest('[data-detail-url]');
    if (!card) return;
    // Let real links/buttons inside a card behave normally.
    if (event.target.closest('a, button')) return;
    const url = card.getAttribute('data-detail-url');
    if (!url) return;
    event.preventDefault();

    const label = card.getAttribute('data-detail-title') || 'Details';
    showLoading(label);
    if (detailModal) detailModal.show();

    fetch(url, { headers: { 'X-Requested-With': 'fetch' } })
      .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
      })
      .then(renderDetail)
      .catch(function () {
        detailSubtitle.textContent = 'Unable to load details';
        detailBody.innerHTML = '<div class="alert alert-danger m-4 mb-0">Details could not be loaded. Please try again.</div>';
      });
  });

  document.addEventListener('keydown', function (event) {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    const card = event.target.closest('.detail-card[tabindex]');
    if (!card) return;
    event.preventDefault();
    card.click();
  });
});
