/* Employee Form JS */
'use strict';
(function() {
  const form = document.getElementById('employeeForm');
  if(form) {
    form.addEventListener('submit', function() {
      const btn = document.getElementById('btnSaveEmployee');
      if(btn) btn.disabled = true;
    });
  }
})();
