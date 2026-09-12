/**
 * conventions.js - Shared UI States, Form Handling, Toast Notifications, and API Envelope Client
 * Implements todo.md Section A (A.1, A.2, A.3, A.4, A.5)
 */

(function () {
    'use strict';

    // =========================================================================
    // A.1.4 Transient Toast System (Top-right, 3-4s auto-dismiss)
    // =========================================================================
    const Toast = {
        container: null,

        ensureContainer() {
            if (!this.container) {
                this.container = document.querySelector('.toast-container');
                if (!this.container) {
                    this.container = document.createElement('div');
                    this.container.className = 'toast-container';
                    document.body.appendChild(this.container);
                }
            }
            return this.container;
        },

        show(message, type = 'success', durationMs = 3500) {
            const container = this.ensureContainer();

            const toast = document.createElement('div');
            toast.className = `app-toast toast-${type}`;

            let iconClass = 'fa-check-circle';
            if (type === 'error') iconClass = 'fa-exclamation-circle';
            else if (type === 'info') iconClass = 'fa-info-circle';
            else if (type === 'warning') iconClass = 'fa-exclamation-triangle';

            toast.innerHTML = `
                <i class="fas ${iconClass} toast-icon"></i>
                <div class="toast-content">${message}</div>
                <button type="button" class="toast-close" aria-label="Close">&times;</button>
                <div class="toast-progress" style="animation-duration: ${durationMs}ms;"></div>
            `;

            container.appendChild(toast);

            const removeToast = () => {
                toast.style.animation = 'toastSlideOut 0.3s forwards';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            };

            const timer = setTimeout(removeToast, durationMs);

            toast.querySelector('.toast-close').addEventListener('click', () => {
                clearTimeout(timer);
                removeToast();
            });
        },

        success(message, duration = 3500) {
            this.show(message, 'success', duration);
        },

        error(message, duration = 4000) {
            this.show(message, 'error', duration);
        },

        info(message, duration = 3500) {
            this.show(message, 'info', duration);
        }
    };

    // =========================================================================
    // A.4 Standard API Client (Enforces { ok: true, data } / { ok: false, errors, message })
    // =========================================================================
    const AppAPI = {
        async request(url, options = {}) {
            const defaultHeaders = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            };

            options.headers = {
                ...defaultHeaders,
                ...(options.headers || {})
            };

            if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
                options.body = JSON.stringify(options.body);
            }

            try {
                const response = await fetch(url, options);

                // Handle HTTP 403 Permission Denied
                if (response.status === 403) {
                    let errData = {};
                    try {
                        errData = await response.json();
                    } catch (e) {}

                    const deniedMsg = errData.message || 'You do not have permission to perform this action.';
                    Toast.error(deniedMsg);

                    // Client-side audit log notify
                    try {
                        fetch('/api/audit/permission-denied', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ target: url, message: deniedMsg })
                        }).catch(() => {});
                    } catch (e) {}

                    const error = new Error(deniedMsg);
                    error.status = 403;
                    error.isPermissionDenied = true;
                    throw error;
                }

                const resData = await response.json();

                if (resData.ok || resData.success) {
                    return resData.data !== undefined ? resData.data : resData;
                } else {
                    const error = new Error(resData.message || 'Request failed');
                    error.status = response.status;
                    error.errors = resData.errors || {};
                    error.message = resData.message || 'Request failed';
                    throw error;
                }
            } catch (err) {
                throw err;
            }
        },

        get(url, options = {}) {
            return this.request(url, { ...options, method: 'GET' });
        },

        post(url, body = {}, options = {}) {
            return this.request(url, { ...options, method: 'POST', body });
        },

        patch(url, body = {}, options = {}) {
            return this.request(url, { ...options, method: 'PATCH', body });
        },

        delete(url, options = {}) {
            return this.request(url, { ...options, method: 'DELETE' });
        }
    };

    // =========================================================================
    // A.1 Standard UI States (Loading, Empty, Error, Permission-denied)
    // =========================================================================
    const AppStates = {
        renderLoading(container, options = {}) {
            const count = options.count || 4;
            const type = options.type || 'table'; // 'table' or 'card'

            if (type === 'table') {
                let rowsHtml = '';
                for (let i = 0; i < count; i++) {
                    rowsHtml += `
                        <div class="skeleton-row">
                            <div class="skeleton skeleton-avatar"></div>
                            <div style="flex: 1;">
                                <div class="skeleton skeleton-text" style="width: 30%;"></div>
                                <div class="skeleton skeleton-text short"></div>
                            </div>
                            <div class="skeleton skeleton-text" style="width: 15%;"></div>
                            <div class="skeleton skeleton-text" style="width: 10%;"></div>
                        </div>
                    `;
                }
                container.innerHTML = `<div class="screen-content">${rowsHtml}</div>`;
            } else {
                let cardsHtml = '';
                for (let i = 0; i < count; i++) {
                    cardsHtml += `
                        <div class="skeleton-card">
                            <div class="skeleton skeleton-title"></div>
                            <div class="skeleton skeleton-text"></div>
                            <div class="skeleton skeleton-text medium"></div>
                        </div>
                    `;
                }
                container.innerHTML = cardsHtml;
            }
        },

        renderEmpty(container, {
            icon = 'fa-folder-open',
            title = 'No items found',
            message = 'There is no data to display at this time.',
            actionText = null,
            onAction = null
        } = {}) {
            const emptyEl = document.createElement('div');
            emptyEl.className = 'ui-empty-state';

            let actionButtonHtml = '';
            if (actionText) {
                actionButtonHtml = `<button type="button" class="btn btn-primary ui-empty-action-btn"><i class="fas fa-plus" style="margin-right: 6px;"></i> ${actionText}</button>`;
            }

            emptyEl.innerHTML = `
                <div class="ui-empty-icon"><i class="fas ${icon}"></i></div>
                <div class="ui-empty-title">${title}</div>
                <div class="ui-empty-message">${message}</div>
                ${actionButtonHtml}
            `;

            if (actionText && onAction) {
                const btn = emptyEl.querySelector('.ui-empty-action-btn');
                if (btn) btn.addEventListener('click', onAction);
            }

            container.innerHTML = '';
            container.appendChild(emptyEl);
        },

        renderError(container, {
            message = 'Something went wrong while loading data.',
            onRetry = null
        } = {}) {
            const errorEl = document.createElement('div');
            errorEl.className = 'ui-error-state';

            errorEl.innerHTML = `
                <div class="ui-error-icon"><i class="fas fa-exclamation-triangle"></i></div>
                <div class="ui-error-message">${message}</div>
                ${onRetry ? `<button type="button" class="btn btn-danger ui-retry-btn"><i class="fas fa-redo"></i> Retry</button>` : ''}
            `;

            if (onRetry) {
                const retryBtn = errorEl.querySelector('.ui-retry-btn');
                if (retryBtn) retryBtn.addEventListener('click', onRetry);
            }

            container.innerHTML = '';
            container.appendChild(errorEl);
        },

        renderPermissionDenied(container, {
            message = 'You do not have permission to view this content.',
            returnUrl = '/dashboard'
        } = {}) {
            // Log denied access to audit_logs
            fetch('/api/audit/permission-denied', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target: window.location.pathname, message })
            }).catch(() => {});

            container.innerHTML = `
                <div class="ui-denied-state card" style="max-width: 500px; margin: 40px auto; text-align: center;">
                    <div style="font-size: 48px; color: var(--danger-color); margin-bottom: 16px;">
                        <i class="fas fa-lock"></i>
                    </div>
                    <h3 style="margin-bottom: 10px; color: var(--text-bright);">Access Denied</h3>
                    <p style="margin-bottom: 24px; color: var(--text-primary); font-size: 14px;">${message}</p>
                    <a href="${returnUrl}" class="btn btn-primary">
                        <i class="fas fa-arrow-left" style="margin-right: 6px;"></i> Return to Dashboard
                    </a>
                </div>
            `;
        }
    };

    // =========================================================================
    // A.3 Standard Form Conventions (Validation on blur, disabled submit, spinner, dirty confirmation)
    // =========================================================================
    const AppForm = {
        bind(formEl, options = {}) {
            if (!formEl) return null;

            const submitBtn = formEl.querySelector('button[type="submit"], input[type="submit"]');
            const cancelBtn = formEl.querySelector('.btn-cancel, [data-action="cancel"], a.cancel-link');
            let isDirty = false;
            const originalFormData = new FormData(formEl);
            const originalValues = {};
            originalFormData.forEach((val, key) => { originalValues[key] = val; });

            // 1. Mark required labels with *
            const inputs = formEl.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.hasAttribute('required')) {
                    const id = input.id;
                    if (id) {
                        const label = formEl.querySelector(`label[for="${id}"]`);
                        if (label && !label.classList.contains('required')) {
                            label.classList.add('required');
                        }
                    }
                }
            });

            // Ensure field error helper elements exist
            inputs.forEach(input => {
                let errorEl = input.parentNode.querySelector(`.form-field-error[data-for="${input.name || input.id}"]`);
                if (!errorEl && input.name) {
                    errorEl = document.createElement('div');
                    errorEl.className = 'form-field-error';
                    errorEl.setAttribute('data-for', input.name || input.id);
                    input.parentNode.appendChild(errorEl);
                }
            });

            const validateField = (field) => {
                const name = field.name || field.id;
                const errorEl = field.parentNode.querySelector(`.form-field-error[data-for="${name}"]`);
                let errorMsg = '';

                if (field.hasAttribute('required')) {
                    if (field.type === 'checkbox' && !field.checked) {
                        errorMsg = 'This field is required.';
                    } else if (!field.value || !field.value.trim()) {
                        errorMsg = 'This field is required.';
                    }
                }

                if (!errorMsg && field.value) {
                    if (field.type === 'email') {
                        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                        if (!emailRegex.test(field.value.trim())) {
                            errorMsg = 'Please enter a valid email address.';
                        }
                    } else if (field.getAttribute('minlength')) {
                        const min = parseInt(field.getAttribute('minlength'), 10);
                        if (field.value.length < min) {
                            errorMsg = `Must be at least ${min} characters.`;
                        }
                    }
                }

                if (errorMsg) {
                    field.classList.add('is-invalid');
                    if (errorEl) {
                        errorEl.textContent = errorMsg;
                        errorEl.classList.add('visible');
                    }
                    return false;
                } else {
                    field.classList.remove('is-invalid');
                    if (errorEl) {
                        errorEl.textContent = '';
                        errorEl.classList.remove('visible');
                    }
                    return true;
                }
            };

            const checkFormValidity = () => {
                let isValid = true;
                inputs.forEach(input => {
                    if (input.hasAttribute('required')) {
                        if (input.type === 'checkbox') {
                            if (!input.checked) isValid = false;
                        } else if (!input.value || !input.value.trim()) {
                            isValid = false;
                        }
                    }
                    if (input.classList.contains('is-invalid')) {
                        isValid = false;
                    }
                });

                if (submitBtn) {
                    submitBtn.disabled = !isValid;
                }
                return isValid;
            };

            // Event: Blur validation
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    validateField(input);
                    checkFormValidity();
                });

                input.addEventListener('input', () => {
                    isDirty = true;
                    // If previously had error, revalidate on input for snappy UX
                    if (input.classList.contains('is-invalid')) {
                        validateField(input);
                    }
                    checkFormValidity();
                });
            });

            // Initial check
            checkFormValidity();

            // 2. Discard changes with confirmation if dirty
            if (cancelBtn) {
                cancelBtn.addEventListener('click', (e) => {
                    if (isDirty) {
                        const confirmed = window.confirm('You have unsaved changes. Are you sure you want to discard them?');
                        if (!confirmed) {
                            e.preventDefault();
                            return false;
                        }
                    }
                    if (options.onCancel) {
                        options.onCancel();
                    }
                });
            }

            // 3. Form Submit handling with inline spinner and server error mapping
            formEl.addEventListener('submit', async (e) => {
                e.preventDefault();

                // Validate all fields
                let allValid = true;
                inputs.forEach(input => {
                    const valid = validateField(input);
                    if (!valid) allValid = false;
                });

                if (!allValid) {
                    Toast.error('Please fix the errors in the form.');
                    return;
                }

                // Show spinner
                let originalBtnHtml = '';
                if (submitBtn) {
                    originalBtnHtml = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = `<span class="btn-spinner"></span> Submitting...`;
                }

                try {
                    const formData = new FormData(formEl);
                    const dataObj = {};
                    formData.forEach((val, key) => {
                        dataObj[key] = val;
                    });

                    if (options.onSubmit) {
                        await options.onSubmit(dataObj, formEl);
                        isDirty = false;
                    }
                } catch (err) {
                    // Map server-side errors { errors: { field_name: "message" } }
                    if (err.errors && typeof err.errors === 'object') {
                        Object.keys(err.errors).forEach(fieldName => {
                            const field = formEl.querySelector(`[name="${fieldName}"]`);
                            const errorEl = formEl.querySelector(`.form-field-error[data-for="${fieldName}"]`);
                            if (field) {
                                field.classList.add('is-invalid');
                            }
                            if (errorEl) {
                                errorEl.textContent = err.errors[fieldName];
                                errorEl.classList.add('visible');
                            }
                        });
                        Toast.error(err.message || 'Please correct the highlighted fields.');
                    } else {
                        Toast.error(err.message || 'Submission failed. Please try again.');
                    }
                } finally {
                    if (submitBtn) {
                        submitBtn.innerHTML = originalBtnHtml;
                        checkFormValidity();
                    }
                }
            });

            return {
                validate: checkFormValidity,
                resetDirty: () => { isDirty = false; }
            };
        }
    };

    // Expose globally
    window.AppConventions = {
        Toast,
        AppAPI,
        AppStates,
        AppForm
    };

    window.Toast = Toast;
    window.AppAPI = AppAPI;
    window.AppStates = AppStates;
    window.AppForm = AppForm;

})();
