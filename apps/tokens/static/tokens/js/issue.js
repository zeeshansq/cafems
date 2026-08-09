/**
 * Tokens – Issue Page JavaScript
 * Detects Roti-Open selection, shows override checkbox.
 */
'use strict';

(function () {
  const empSelect = document.getElementById('id_token_employee');
  const overrideSection = document.getElementById('rotiOverrideSection');
  const overrideCheckbox = document.getElementById('id_roti_override');
  const submitBtn = document.getElementById('btnIssueSubmit');

  if (!empSelect) return;

  function checkRotiOpen() {
    const selected = empSelect.options[empSelect.selectedIndex];
    const type = selected ? selected.dataset.type : '';
    const isRotiOpen = type === 'roti_open';

    overrideSection.style.display = isRotiOpen ? 'block' : 'none';

    if (!isRotiOpen) {
      overrideCheckbox.checked = false;
    }
  }

  empSelect.addEventListener('change', checkRotiOpen);
  checkRotiOpen(); // Run on load

  // Keyboard shortcut: Enter focuses submit if employee selected
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && document.activeElement === empSelect) {
      e.preventDefault();
      submitBtn?.focus();
    }
  });

})();
