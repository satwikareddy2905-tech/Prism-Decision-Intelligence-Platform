/**
 * Prism — app.js
 * Global application logic: dark mode, toasts, CSRF, sidebar, confirmations.
 */

// --------------------------------------------------------------------------
// CSRF Token (available to all AJAX calls)
// --------------------------------------------------------------------------
const CSRF_TOKEN = document.querySelector('meta[name="csrf-token"]')?.content || '';

function getCsrf() { return CSRF_TOKEN; }

// --------------------------------------------------------------------------
// Dark Mode
// --------------------------------------------------------------------------
const DarkMode = (() => {
  const htmlEl = document.documentElement;

  function apply(isDark) {
    if (isDark) {
      htmlEl.setAttribute('data-theme', 'dark');
    } else {
      htmlEl.removeAttribute('data-theme');
    }
  }

  function toggle() {
    const isDark = htmlEl.getAttribute('data-theme') === 'dark';
    apply(!isDark);
    persistPreference(!isDark);
    return !isDark;
  }

  function persistPreference(isDark) {
    // Save to server if logged in
    fetch('/profile/dark-mode', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrf(),
      },
      body: JSON.stringify({ dark_mode: isDark }),
    }).catch(() => {});

    localStorage.setItem('prism-dark', isDark ? '1' : '0');
  }

  function init(serverPreference) {
    apply(serverPreference);
  }

  return { init, toggle, apply };
})();


// --------------------------------------------------------------------------
// Toast Notification System
// --------------------------------------------------------------------------
const Toast = (() => {
  let container = null;

  function getContainer() {
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  const ICONS = {
    success: '<i class="bi bi-check-circle-fill"></i>',
    warning: '<i class="bi bi-exclamation-triangle-fill"></i>',
    danger:  '<i class="bi bi-x-circle-fill"></i>',
    error:   '<i class="bi bi-x-circle-fill"></i>',
    info:    '<i class="bi bi-info-circle-fill"></i>',
  };

  function show(type, title, message = '', duration = 4000) {
    const c = getContainer();
    const toast = document.createElement('div');
    const t = type === 'error' ? 'danger' : type;
    toast.className = `toast toast-${t}`;
    toast.innerHTML = `
      <div class="toast-icon">${ICONS[type] || ICONS.info}</div>
      <div class="toast-body">
        <div class="toast-title">${title}</div>
        ${message ? `<div class="toast-message">${message}</div>` : ''}
      </div>
      <button class="toast-close" aria-label="Dismiss"><i class="bi bi-x"></i></button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => dismiss(toast));
    c.appendChild(toast);

    if (duration > 0) {
      setTimeout(() => dismiss(toast), duration);
    }

    return toast;
  }

  function dismiss(toast) {
    toast.classList.add('removing');
    setTimeout(() => toast.remove(), 200);
  }

  function success(title, msg, d)  { return show('success', title, msg, d); }
  function warning(title, msg, d)  { return show('warning', title, msg, d); }
  function error(title, msg, d)    { return show('danger', title, msg, d); }
  function info(title, msg, d)     { return show('info', title, msg, d); }

  return { show, success, warning, error, info, dismiss };
})();


// --------------------------------------------------------------------------
// Flash Messages → Toasts (server-rendered alerts)
// --------------------------------------------------------------------------
function initFlashToasts() {
  document.querySelectorAll('[data-flash]').forEach(el => {
    const category = el.dataset.flash;
    const message = el.textContent.trim();
    el.remove();

    const map = { success: 'success', warning: 'warning', error: 'error',
                  danger: 'error', info: 'info' };
    const type = map[category] || 'info';
    Toast.show(type, message, '', 4500);
  });
}


// --------------------------------------------------------------------------
// Confirmation Dialog (replaces browser confirm())
// --------------------------------------------------------------------------
function confirmAction(message, onConfirm, options = {}) {
  const { title = 'Are you sure?', confirmText = 'Confirm',
          cancelText = 'Cancel', danger = false } = options;

  const existing = document.getElementById('prism-confirm-modal');
  if (existing) existing.remove();

  const modal = document.createElement('div');
  modal.id = 'prism-confirm-modal';
  modal.style.cssText = `
    position:fixed;inset:0;z-index:${getComputedStyle(document.documentElement)
      .getPropertyValue('--z-modal') || 500};
    display:flex;align-items:center;justify-content:center;
    background:rgba(0,0,0,0.4);backdrop-filter:blur(4px);
    animation:fade-in 150ms ease;
  `;
  modal.innerHTML = `
    <div style="background:var(--color-surface);border:1px solid var(--color-border);
      border-radius:var(--radius-lg);padding:var(--space-6);max-width:380px;width:90%;
      box-shadow:var(--shadow-xl);">
      <h3 style="font-size:var(--text-base);font-weight:var(--weight-semibold);
        margin-bottom:var(--space-2)">${title}</h3>
      <p style="font-size:var(--text-sm);color:var(--color-text-secondary);
        margin-bottom:var(--space-6)">${message}</p>
      <div style="display:flex;justify-content:flex-end;gap:var(--space-2)">
        <button id="confirm-cancel" class="btn btn-secondary btn-sm">${cancelText}</button>
        <button id="confirm-ok" class="btn ${danger ? 'btn-danger' : 'btn-primary'} btn-sm">
          ${confirmText}
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  modal.querySelector('#confirm-cancel').addEventListener('click', () => modal.remove());
  modal.querySelector('#confirm-ok').addEventListener('click', () => {
    modal.remove();
    onConfirm();
  });
  modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
}


// --------------------------------------------------------------------------
// AJAX helper
// --------------------------------------------------------------------------
async function apiFetch(url, options = {}) {
  const defaults = {
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrf(),
      'X-Requested-With': 'XMLHttpRequest',
    },
  };

  const merged = {
    ...defaults,
    ...options,
    headers: { ...defaults.headers, ...(options.headers || {}) },
  };

  const res = await fetch(url, merged);

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || data.message || `Request failed: ${res.status}`);
  }

  return res.json();
}


// --------------------------------------------------------------------------
// Sidebar mobile toggle
// --------------------------------------------------------------------------
function initSidebar() {
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');

  if (!toggleBtn || !sidebar) return;

  toggleBtn.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('active');
  });

  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('active');
    });
  }
}


// --------------------------------------------------------------------------
// Auto-resize textareas
// --------------------------------------------------------------------------
function initAutoResize() {
  document.querySelectorAll('textarea[data-autoresize]').forEach(ta => {
    function resize() {
      ta.style.height = 'auto';
      ta.style.height = ta.scrollHeight + 'px';
    }
    ta.addEventListener('input', resize);
    resize();
  });
}


// --------------------------------------------------------------------------
// Inline edit (click-to-edit pattern)
// --------------------------------------------------------------------------
function initInlineEdits() {
  document.querySelectorAll('[data-inline-edit]').forEach(wrapper => {
    const display = wrapper.querySelector('[data-inline-display]');
    const input   = wrapper.querySelector('[data-inline-input]');
    const saveBtn = wrapper.querySelector('[data-inline-save]');

    if (!display || !input) return;

    display.addEventListener('click', () => {
      display.style.display = 'none';
      input.style.display = 'block';
      input.focus();
      input.select();
    });

    function cancel() {
      input.style.display = 'none';
      display.style.display = 'block';
    }

    input.addEventListener('keydown', e => {
      if (e.key === 'Escape') cancel();
    });

    if (saveBtn) {
      saveBtn.addEventListener('click', cancel);
    }
  });
}


// --------------------------------------------------------------------------
// Delete confirm buttons
// --------------------------------------------------------------------------
function initDeleteButtons() {
  document.querySelectorAll('[data-confirm-delete]').forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      const msg = btn.dataset.confirmDelete || 'This action cannot be undone.';
      const target = btn.dataset.target;

      confirmAction(msg, () => {
        if (target) {
          const form = document.getElementById(target) || document.querySelector(target);
          if (form) form.submit();
        } else if (btn.form) {
          btn.form.submit();
        } else if (btn.href || btn.dataset.href) {
          window.location.href = btn.href || btn.dataset.href;
        }
      }, {
        title: 'Delete',
        confirmText: 'Delete',
        cancelText: 'Cancel',
        danger: true,
      });
    });
  });
}


// --------------------------------------------------------------------------
// Keyboard shortcuts
// --------------------------------------------------------------------------
function initKeyboardShortcuts() {
  document.addEventListener('keydown', e => {
    // Ctrl/Cmd + K → focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const searchInput = document.getElementById('global-search-input');
      if (searchInput) searchInput.focus();
    }

    // Escape → close modals
    if (e.key === 'Escape') {
      const modal = document.getElementById('prism-confirm-modal');
      if (modal) modal.remove();
    }
  });
}


// --------------------------------------------------------------------------
// Dark mode toggle button (in topbar)
// --------------------------------------------------------------------------
function initDarkModeToggle() {
  const btn = document.getElementById('dark-mode-toggle');
  if (!btn) return;

  btn.addEventListener('click', () => {
    const isDark = DarkMode.toggle();
    const icon = btn.querySelector('i');
    if (icon) {
      icon.className = isDark ? 'bi bi-sun' : 'bi bi-moon';
    }
  });
}


// --------------------------------------------------------------------------
// Notifications
// --------------------------------------------------------------------------
async function markNotificationRead(notifId, redirectLink) {
  try {
    await apiFetch(`/api/notifications/read/${notifId}`, { method: 'POST' });
    if (redirectLink) {
      window.location.href = redirectLink;
    } else {
      window.location.reload();
    }
  } catch (err) {
    console.error('Failed to mark notification as read:', err);
    if (redirectLink) {
      window.location.href = redirectLink;
    }
  }
}

async function markAllNotificationsRead(event) {
  if (event) event.stopPropagation();
  try {
    await apiFetch('/api/notifications/read-all', { method: 'POST' });
    Toast.success('All notifications marked as read');
    window.location.reload();
  } catch (err) {
    Toast.error('Failed to mark notifications as read', err.message);
  }
}


// --------------------------------------------------------------------------
// Init
// --------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initFlashToasts();
  initSidebar();
  initAutoResize();
  initInlineEdits();
  initDeleteButtons();
  initKeyboardShortcuts();
  initDarkModeToggle();
});
