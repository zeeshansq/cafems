/**
 * Cafeteria Setup & Catalog Management JS
 * Handles tab persistence, modal triggers, and status toggle confirmations.
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('Cafeteria Setup JS initialized.');

  // Tab persistence via URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  const activeTabParam = urlParams.get('tab');
  if (activeTabParam) {
    const tabEl = document.querySelector('#setupTabs button[data-bs-target="#tab-' + activeTabParam + '"]');
    if (tabEl && typeof bootstrap !== 'undefined' && bootstrap.Tab) {
      const tab = new bootstrap.Tab(tabEl);
      tab.show();
    }
  }
});
