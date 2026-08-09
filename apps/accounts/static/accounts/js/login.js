/**
 * CafeMS – Ultra-Premium Gourmet Login Interactive JS
 * Features: Upward floating food icons, spatial light tracking, password toggle, quick test credentials
 */

'use strict';

(function () {

  // ── 1. Interactive 3D Spatial Light Spot Tracker ─────────────────────
  const loginCard = document.getElementById('loginCard');
  const lightSpot = document.getElementById('cardLightSpot');

  if (loginCard && lightSpot) {
    loginCard.addEventListener('mousemove', (e) => {
      const rect = loginCard.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      lightSpot.style.left = `${x}px`;
      lightSpot.style.top = `${y}px`;
    });
  }

  // ── 2. Password Show/Hide Toggle ──────────────────────────────────────
  const toggleBtn  = document.getElementById('passwordToggleBtn');
  const toggleIcon = document.getElementById('passwordToggleIcon');
  const pwdInput   = document.getElementById('id_password');

  if (toggleBtn && pwdInput) {
    toggleBtn.addEventListener('click', () => {
      const isText = pwdInput.type === 'text';
      pwdInput.type = isText ? 'password' : 'text';
      toggleIcon.className = isText ? 'bi bi-eye-slash' : 'bi bi-eye text-warning';
    });
  }

  // ── 3. Quick Test Credential Auto-Fill Buttons ─────────────────────────
  const emailInput = document.getElementById('id_email');
  const quickBtns  = document.querySelectorAll('.btn-quick-login');

  quickBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const email = btn.dataset.email;
      const pwd   = btn.dataset.pwd;

      if (emailInput && email) {
        emailInput.value = email;
        const emailGroup = document.getElementById('groupEmail');
        if (emailGroup) {
          emailGroup.style.borderColor = '#f59e0b';
          setTimeout(() => { emailGroup.style.borderColor = ''; }, 1200);
        }
      }

      if (pwdInput && pwd) {
        pwdInput.value = pwd;
        const pwdGroup = document.getElementById('passwordToggleGroup');
        if (pwdGroup) {
          pwdGroup.style.borderColor = '#f59e0b';
          setTimeout(() => { pwdGroup.style.borderColor = ''; }, 1200);
        }
      }

      const submitBtn = document.getElementById('loginSubmitBtn');
      submitBtn?.focus();
    });
  });

  // ── 4. Auto-Focus Email Input ─────────────────────────────────────────
  if (emailInput && !emailInput.value) {
    setTimeout(() => emailInput.focus(), 200);
  }

  // ── 5. Submit Button Loading State ─────────────────────────────────────
  const form      = document.getElementById('loginForm');
  const submitBtn = document.getElementById('loginSubmitBtn');
  const btnText   = document.getElementById('loginBtnText');

  if (form && submitBtn) {
    form.addEventListener('submit', () => {
      const emailVal = emailInput?.value.trim();
      const pwdVal   = pwdInput?.value;

      if (!emailVal || !pwdVal) return;

      submitBtn.disabled = true;
      if (btnText) {
        btnText.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Authenticating…';
      }

      setTimeout(() => {
        submitBtn.disabled = false;
        if (btnText) {
          btnText.innerHTML = '<span>Sign In to Cafeteria</span><i class="bi bi-arrow-right-short ms-1 fs-4 align-middle"></i>';
        }
      }, 8000);
    });
  }

  // ── 6. Keyboard Shortcut: Enter Submits ───────────────────────────────
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && e.target.tagName !== 'BUTTON') {
      const f = document.getElementById('loginForm');
      if (f) f.requestSubmit();
    }
  });

  // ── 7. Render Django Messages Toast ────────────────────────────────────
  document.querySelectorAll('[data-toast]').forEach(el => {
    const type = el.dataset.toast;
    const msg  = el.dataset.toastMessage;
    if (msg && window.ToastManager) {
      ToastManager.show(msg, type);
    }
    el.remove();
  });

  // ── 8. Optimized Upward Floating Food Icons Background Generator ───────
  const foodRainContainer = document.getElementById('foodIconRain');
  if (foodRainContainer) {
    const foodIcons = [
      'bi-cup-hot', 'bi-cup-hot-fill', 'bi-egg-fried', 'bi-cup-straw',
      'bi-basket', 'bi-bag-heart', 'bi-cake2', 'bi-apple', 'bi-fire',
      'bi-cookie', 'bi-ticket-perforated', 'bi-award'
    ];
    const colors = ['color-saffron', 'color-terracotta', 'color-mint', 'color-gold'];

    // Reduced to 12 elements for low-end PC optimization & 60fps performance
    const ICON_COUNT = 12;

    for (let i = 0; i < ICON_COUNT; i++) {
      const el = document.createElement('i');
      const randomIcon = foodIcons[Math.floor(Math.random() * foodIcons.length)];
      const randomColor = colors[Math.floor(Math.random() * colors.length)];

      el.className = `bi ${randomIcon} falling-food-icon ${randomColor}`;

      const leftPos = Math.random() * 90 + 5; // 5% to 95%
      const duration = Math.random() * 10 + 12; // 12s to 22s
      const delay = Math.random() * -20; // Negative delay so icons are floating on load
      const fontSize = (Math.random() * 1.2 + 1.2).toFixed(2); // 1.2rem to 2.4rem
      const opacity = (Math.random() * 0.14 + 0.1).toFixed(2); // 0.10 to 0.24

      el.style.left = `${leftPos}%`;
      el.style.animationDuration = `${duration}s`;
      el.style.animationDelay = `${delay}s`;
      el.style.fontSize = `${fontSize}rem`;
      el.style.setProperty('--target-opacity', opacity);

      foodRainContainer.appendChild(el);
    }
  }

})();
