/**
 * CafeMS – Admin Dashboard JavaScript
 */

'use strict';

(function () {

  // ── Animate stat cards on load ─────────────────────────────────────────
  function animateStats() {
    const stats = document.querySelectorAll('.stat-value');
    stats.forEach(el => {
      const target = parseInt(el.textContent, 10);
      if (isNaN(target)) return;

      let current = 0;
      const step = Math.max(1, Math.floor(target / 30));
      const interval = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current.toLocaleString();
        if (current >= target) clearInterval(interval);
      }, 30);
    });
  }

  // ── Pending requests counter live update ──────────────────────────────
  function loadPendingRequests() {
    const el = document.getElementById('pendingRequestsCount');
    if (!el) return;

    fetch('/api/v1/notifications/unread-count/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(r => r.json())
    .then(data => {
      if (el) el.textContent = data.pending_requests ?? '—';
    })
    .catch(() => { if (el) el.textContent = '—'; });
  }

  document.addEventListener('DOMContentLoaded', () => {
    animateStats();
    loadPendingRequests();

    // Refresh every 60 seconds
    setInterval(loadPendingRequests, 60000);
  });

})();
