/**
 * CafeMS – Global Application JavaScript
 * Handles: dark mode, sidebar, toasts, htmx enhancements
 */

'use strict';

(function () {
  // Idempotent execution guard
  if (window.__cafems_app_loaded__) return;
  window.__cafems_app_loaded__ = true;

  // ─── Theme Manager ──────────────────────────────────────────────────────────
  const ThemeManager = {
    STORAGE_KEY: 'cafems_theme',

    init() {
      const savedTheme = document.body.dataset.userTheme || localStorage.getItem(this.STORAGE_KEY) || 'light';
      this.apply(savedTheme, false);
    },

    apply(theme, persist = true) {
      document.documentElement.setAttribute('data-theme', theme);
      document.documentElement.setAttribute('data-bs-theme', theme);
      document.body.setAttribute('data-user-theme', theme);
      document.body.classList.toggle('dark-mode', theme === 'dark');
      if (persist) {
        localStorage.setItem(this.STORAGE_KEY, theme);
      }
    },

    toggle() {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      this.apply(next);

      fetch('/accounts/profile/dark-mode/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': CafeMS.getCsrfToken(),
          'Content-Type': 'application/json',
        },
      }).catch(console.error);

      return next;
    },
  };

  // ─── Sidebar Manager ────────────────────────────────────────────────────────
  const SidebarManager = {
    init() {
      const toggleBtn = document.getElementById('sidebarToggleBtn');
      const sidebar   = document.getElementById('appSidebar');

      if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => this.toggle());
      }

      const currentPath = window.location.pathname;
      document.querySelectorAll('.sidebar-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
          link.classList.add('active');
        }
      });
    },

    toggle() {
      const sidebar = document.getElementById('appSidebar');
      sidebar?.classList.toggle('show');
    },

    close() {
      document.getElementById('appSidebar')?.classList.remove('show');
    },
  };

  // ─── Toast Notifications ────────────────────────────────────────────────────
  const ToastManager = {
    DURATION: 4500,

    show(message, type = 'info', duration = this.DURATION) {
      const container = document.getElementById('toastContainer');
      if (!container) return;

      const icons = {
        success: 'bi-check-circle-fill',
        error:   'bi-x-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info:    'bi-info-circle-fill',
      };

      const toast = document.createElement('div');
      toast.className = `toast-item ${type}`;
      toast.innerHTML = `
        <i class="bi ${icons[type] || icons.info} flex-shrink-0" style="color:var(--clr-${type === 'error' ? 'danger' : type})"></i>
        <span class="flex-grow-1" style="font-size:0.875rem">${message}</span>
        <button type="button" class="btn-close btn-close-sm ms-2" aria-label="Close"></button>
      `;

      container.appendChild(toast);
      toast.querySelector('.btn-close')?.addEventListener('click', () => this.dismiss(toast));
      setTimeout(() => this.dismiss(toast), duration);
    },

    dismiss(toast) {
      toast.style.animation = 'fadeOut 0.3s forwards';
      setTimeout(() => toast.remove(), 300);
    },

    success(msg) { this.show(msg, 'success'); },
    error(msg)   { this.show(msg, 'error'); },
    warning(msg) { this.show(msg, 'warning'); },
    info(msg)    { this.show(msg, 'info'); },
  };

  // ─── CSRF & HTMX Setup ──────────────────────────────────────────────────────
  const CafeMS = {
    getCsrfToken() {
      return document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1] || '';
    },

    setupHtmx() {
      document.addEventListener('htmx:configRequest', (e) => {
        e.detail.headers['X-CSRFToken'] = this.getCsrfToken();
      });

      document.addEventListener('htmx:afterRequest', (e) => {
        const xhr = e.detail.xhr;
        if (xhr.status === 403) {
          window.location.href = '/accounts/login/?next=' + window.location.pathname;
        }
      });

      document.addEventListener('htmx:afterOnLoad', (e) => {
        const toastHeader = e.detail.xhr.getResponseHeader('X-Toast');
        if (toastHeader) {
          try {
            const { message, type } = JSON.parse(toastHeader);
            ToastManager.show(message, type);
          } catch {}
        }
      });
    },
  };

  // ─── Notification Polling (htmx-based) ──────────────────────────────────────
  const NotifManager = {
    POLL_INTERVAL: 30000,

    init() {
      const dot = document.getElementById('navNotifDot');
      if (!dot) return;

      setInterval(() => this.poll(), this.POLL_INTERVAL);
    },

    poll() {
      fetch('/api/v1/notifications/unread-count/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      })
      .then(r => r.json())
      .then(data => {
        const dot = document.getElementById('navNotifDot');
        if (!dot) return;
        if (data.count > 0) {
          dot.classList.remove('d-none');
        } else {
          dot.classList.add('d-none');
        }
      })
      .catch(() => {});
    },
  };

  // ─── Form Helpers ────────────────────────────────────────────────────────────
  const FormHelpers = {
    disableOnSubmit(form) {
      form.addEventListener('submit', () => {
        const btn = form.querySelector('[type=submit]');
        if (btn) {
          btn.disabled = true;
          const original = btn.innerHTML;
          btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Processing…`;
          setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = original;
          }, 8000);
        }
      });
    },

    initAll() {
      document.querySelectorAll('form[data-submit-once]').forEach(form => {
        this.disableOnSubmit(form);
      });
    },
  };

  // ─── Pakistani Date Picker Manager ──────────────────────────────────────────
  const DatePickerManager = {
    init() {
      if (typeof flatpickr !== 'undefined') {
        flatpickr("input[type='date'], .datepicker", {
          dateFormat: "Y-m-d",
          altInput: true,
          altFormat: "d-M-Y",
          allowInput: true,
        });
      }
    }
  };

  // ─── Init ────────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
    SidebarManager.init();
    CafeMS.setupHtmx();
    NotifManager.init();
    FormHelpers.initAll();
    DatePickerManager.init();

    // Dark Mode Toggle Button Listener
    document.getElementById('darkModeToggle')?.addEventListener('click', () => {
      ThemeManager.toggle();
    });

    // Auto-show Django messages
    document.querySelectorAll('[data-toast]').forEach(el => {
      const type = el.dataset.toast;
      const msg  = el.dataset.toastMessage;
      if (msg) ToastManager.show(msg, type);
      el.remove();
    });

    // Live PKT Clock Ticker
    function updateClock() {
      const timeEl = document.getElementById('liveTimeStr');
      if (timeEl) {
        const now = new Date();
        timeEl.textContent = now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true }) + ' PKT';
      }
    }
    updateClock();
    setInterval(updateClock, 1000);
  });

  // Expose globals
  window.CafeMS       = CafeMS;
  window.ToastManager = ToastManager;
  window.ThemeManager = ThemeManager;

})();
