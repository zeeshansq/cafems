/* Employee Dashboard JS */
'use strict';
(function () {
  // Animate stat values
  document.querySelectorAll('.stat-value').forEach(el => {
    const target = parseInt(el.textContent.replace(/[^\d]/g, ''), 10);
    if (isNaN(target) || target === 0) return;
    let current = 0;
    const step = Math.max(1, Math.floor(target / 20));
    const iv = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current.toLocaleString();
      if (current >= target) clearInterval(iv);
    }, 40);
  });
})();
