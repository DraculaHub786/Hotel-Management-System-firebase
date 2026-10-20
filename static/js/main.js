/**
 * Nur-e-Haya Platform Core Client Library
 * Implements master_plan.md Phase 1: api(), toasts, modals, polling
 */

(function() {
  'use strict';

  // 1. Toast Notification Container Setup
  let toastContainer = document.getElementById('nh-toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'nh-toast-container';
    document.body.appendChild(toastContainer);
  }

  window.showToast = function(message, type = 'info', duration = 3500) {
    const toast = document.createElement('div');
    toast.className = `nh-toast toast-${type}`;
    
    let iconClass = 'fa-info-circle';
    if (type === 'success') iconClass = 'fa-check-circle';
    else if (type === 'error') iconClass = 'fa-exclamation-circle';
    else if (type === 'warning') iconClass = 'fa-exclamation-triangle';

    toast.innerHTML = `
      <i class="fas ${iconClass}"></i>
      <span style="flex: 1;">${message}</span>
      <button style="background: none; border: none; color: var(--text-tertiary); cursor: pointer; padding: 4px;" onclick="this.parentElement.remove()">
        <i class="fas fa-times"></i>
      </button>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        toast.style.transition = 'all 0.25s ease';
        setTimeout(() => toast.remove(), 250);
      }
    }, duration);
  };

  // 2. Apple Style Confirmation Modal
  window.showModal = function({ title, message, htmlContent, confirmText = 'Confirm', cancelText = 'Cancel', isDanger = false, onConfirm = null }) {
    let modalOverlay = document.getElementById('nh-active-modal');
    if (modalOverlay) modalOverlay.remove();

    modalOverlay = document.createElement('div');
    modalOverlay.id = 'nh-active-modal';
    modalOverlay.className = 'nh-modal-overlay';

    modalOverlay.innerHTML = `
      <div class="nh-modal-box">
        <h3 class="nh-modal-title">${title}</h3>
        <div class="nh-modal-body">${htmlContent || `<p>${message}</p>`}</div>
        <div class="nh-modal-actions">
          <button type="button" class="btn-nh btn-nh-secondary" id="nh-modal-cancel">${cancelText}</button>
          <button type="button" class="btn-nh ${isDanger ? 'btn-nh-danger' : 'btn-nh-primary'}" id="nh-modal-confirm">${confirmText}</button>
        </div>
      </div>
    `;

    document.body.appendChild(modalOverlay);
    requestAnimationFrame(() => modalOverlay.classList.add('active'));

    function closeModal() {
      modalOverlay.classList.remove('active');
      setTimeout(() => modalOverlay.remove(), 250);
    }

    modalOverlay.querySelector('#nh-modal-cancel').onclick = closeModal;
    modalOverlay.querySelector('#nh-modal-confirm').onclick = async () => {
      if (onConfirm) {
        const res = await onConfirm();
        if (res !== false) closeModal();
      } else {
        closeModal();
      }
    };
  };

  // 2.5 Global CSRF Interceptor for same-origin state-changing fetches
  const originalFetch = window.fetch;
  window.fetch = function(resource, init = {}) {
    try {
      const method = ((init && init.method) || 'GET').toUpperCase();
      if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const token = csrfMeta ? csrfMeta.getAttribute('content') : '';
        if (token) {
          init = init || {};
          if (init.headers instanceof Headers) {
            if (!init.headers.has('X-CSRF-Token')) init.headers.set('X-CSRF-Token', token);
          } else if (Array.isArray(init.headers)) {
            if (!init.headers.some(([k]) => k.toLowerCase() === 'x-csrf-token')) init.headers.push(['X-CSRF-Token', token]);
          } else {
            init.headers = init.headers || {};
            if (!init.headers['X-CSRF-Token'] && !init.headers['x-csrf-token']) {
              init.headers['X-CSRF-Token'] = token;
            }
          }
        }
      }
    } catch (e) {
      console.warn('CSRF interceptor note:', e);
    }
    return originalFetch.call(this, resource, init);
  };

  // 3. Unified API Fetch Wrapper
  window.api = async function(url, options = {}) {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
    const headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };
    const method = (options.method || 'GET').toUpperCase();
    if (csrfToken && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
      headers['X-CSRF-Token'] = csrfToken;
    }

    const fetchOptions = {
      headers,
      method,
      ...options
    };

    if (fetchOptions.body && typeof fetchOptions.body === 'object' && !(fetchOptions.body instanceof FormData)) {
      fetchOptions.body = JSON.stringify(fetchOptions.body);
    }

    try {
      const response = await fetch(url, fetchOptions);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMsg = data.message || (data.errors ? Object.values(data.errors).join(', ') : 'Request failed');
        return { ok: false, status: response.status, message: errorMsg, errors: data.errors || {}, data: data.data || {} };
      }

      return { ok: true, status: response.status, data: data.data !== undefined ? data.data : data, message: data.message };
    } catch (err) {
      console.error('API call error:', err);
      return { ok: false, status: 0, message: err.message || 'Network error' };
    }
  };

  // 4. Live Polling Engine (e.g. 3-5s for task boards)
  window.startPolling = function(url, onData, intervalMs = 3000) {
    let isRunning = true;
    let timerId = null;

    async function poll() {
      if (!isRunning) return;
      try {
        const res = await window.api(url);
        if (res.ok && onData) {
          onData(res.data);
        }
      } catch (e) {
        console.warn('Polling error:', e);
      } finally {
        if (isRunning) {
          timerId = setTimeout(poll, intervalMs);
        }
      }
    }

    poll();

    return {
      stop: () => {
        isRunning = false;
        if (timerId) clearTimeout(timerId);
      }
    };
  };

  // 5. Global Mobile Sidebar Toggle
  document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('nh-sidebar-toggle');
    const sidebar = document.querySelector('.app-sidebar');
    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
      });
    }
  });

})();
