/**
 * AI Career Intelligence Platform — Main JavaScript
 * ===================================================
 * Utilities: sidebar, toast, progress rings, count-up, 
 * skeleton, AI loading steps, drag-drop, debounce, etc.
 */

'use strict';

/* ── SIDEBAR ──────────────────────────────────────────────── */
const SidebarManager = (() => {
    const STORAGE_KEY = 'aicareer_sidebar_collapsed';
    const sidebar     = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    const toggleBtn   = document.getElementById('sidebarToggle');
    const overlay     = document.getElementById('sidebarOverlay');

    function isDesktop() { return window.innerWidth >= 769; }

    function collapse() {
        if (isDesktop()) {
            sidebar?.classList.add('sidebar-collapsed');
            mainContent?.classList.add('sidebar-collapsed-content');
            localStorage.setItem(STORAGE_KEY, '1');
        } else {
            sidebar?.classList.remove('mobile-open');
            overlay?.classList.remove('active');
        }
    }

    function expand() {
        if (isDesktop()) {
            sidebar?.classList.remove('sidebar-collapsed');
            mainContent?.classList.remove('sidebar-collapsed-content');
            localStorage.setItem(STORAGE_KEY, '0');
        } else {
            sidebar?.classList.add('mobile-open');
            overlay?.classList.add('active');
        }
    }

    function toggle() {
        if (isDesktop()) {
            const collapsed = sidebar?.classList.contains('sidebar-collapsed');
            collapsed ? expand() : collapse();
        } else {
            const open = sidebar?.classList.contains('mobile-open');
            open ? collapse() : expand();
        }
    }

    function init() {
        if (!sidebar) return;

        // Restore desktop state
        if (isDesktop() && localStorage.getItem(STORAGE_KEY) === '1') {
            sidebar.classList.add('sidebar-collapsed');
            mainContent?.classList.add('sidebar-collapsed-content');
        }

        toggleBtn?.addEventListener('click', toggle);
        overlay?.addEventListener('click', collapse);

        // Responsive: close mobile sidebar on resize
        window.addEventListener('resize', () => {
            if (isDesktop()) {
                sidebar.classList.remove('mobile-open');
                overlay?.classList.remove('active');
            }
        });
    }

    return { init, toggle, collapse, expand };
})();


/* ── TOAST ────────────────────────────────────────────────── */
const Toast = (() => {
    const stack = document.getElementById('toastStack');

    const ICONS = {
        success: 'bi-check-circle-fill',
        danger:  'bi-exclamation-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info:    'bi-info-circle-fill',
    };

    function show(message, type = 'info', duration = 4000) {
        if (!stack) return;

        const item = document.createElement('div');
        item.className = `toast-item ${type}`;
        item.setAttribute('role', 'alert');
        item.innerHTML = `
            <i class="bi ${ICONS[type] || ICONS.info} toast-icon"></i>
            <span class="toast-message">${message}</span>
            <button class="toast-close" aria-label="Dismiss"><i class="bi bi-x-lg"></i></button>
        `;

        stack.appendChild(item);

        item.querySelector('.toast-close').addEventListener('click', () => dismiss(item));

        if (duration > 0) {
            setTimeout(() => dismiss(item), duration);
        }
    }

    function dismiss(item) {
        item.classList.add('removing');
        item.addEventListener('animationend', () => item.remove(), { once: true });
    }

    return { show, success: m => show(m,'success'), error: m => show(m,'danger'), warning: m => show(m,'warning'), info: m => show(m,'info') };
})();

// Make globally accessible
window.Toast = Toast;


/* ── PROGRESS RING ────────────────────────────────────────── */
/**
 * Render an SVG progress ring into a container element.
 * @param {HTMLElement} container
 * @param {number} value         0–100
 * @param {object} opts
 *   size    {number}  diameter in px    (default 90)
 *   stroke  {number}  stroke width      (default 8)
 *   color   {string}  stroke color      (default var(--primary))
 *   label   {string}  text below value
 *   showPct {boolean} append % after value
 */
function renderProgressRing(container, value, opts = {}) {
    if (!container) return;

    const size    = opts.size    || 90;
    const stroke  = opts.stroke  || 8;
    const color   = opts.color   || 'var(--primary)';
    const label   = opts.label   || '';
    const showPct = opts.showPct !== false;
    const animate = opts.animate !== false;
    const radius  = (size - stroke) / 2;
    const sizeClass = opts.sizeClass || '';

    container.innerHTML = `
        <div class="progress-ring-wrap ${sizeClass}" style="width:${size}px;height:${size}px;">
            <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" aria-hidden="true">
                <circle class="progress-ring-track" cx="${size/2}" cy="${size/2}" r="${radius}" stroke-width="${stroke}"/>
                <circle class="progress-ring-fill"
                    cx="${size/2}" cy="${size/2}" r="${radius}"
                    stroke-width="${stroke}"
                    stroke="${color}"
                    pathLength="100"
                    stroke-dasharray="100"
                    stroke-dashoffset="${animate ? 100 : 100 - value}"
                    data-target-offset="${100 - value}"
                    style="--ring-circumference:100"
                />
            </svg>
            <div class="progress-ring-text">
                <span class="progress-ring-value ${size < 80 ? 'sm' : ''}" 
                      data-count-from="0" data-count-to="${value}">0</span>
                ${showPct ? `<span class="progress-ring-label">%</span>` : ''}
                ${label ? `<span class="progress-ring-label">${label}</span>` : ''}
            </div>
        </div>`;

    if (animate) {
        // Trigger animation after a brief delay
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                const fill = container.querySelector('.progress-ring-fill');
                if (fill) {
                    fill.style.transition = 'stroke-dashoffset 1s cubic-bezier(0.34, 1.56, 0.64, 1)';
                    fill.style.strokeDashoffset = 100 - value;
                }
                const val = container.querySelector('[data-count-to]');
                if (val) animateCount(val, 0, value, 1000);
            });
        });
    }
}


/* ── COUNT-UP ANIMATION ───────────────────────────────────── */
function animateCount(el, from, to, duration = 1000, suffix = '') {
    if (!el) return;
    const start = performance.now();
    const range = to - from;

    function step(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out quad
        const eased = 1 - (1 - progress) * (1 - progress);
        const value = Math.round(from + range * eased);
        el.textContent = value + suffix;
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

window.animateCount = animateCount;
window.renderProgressRing = renderProgressRing;


/* ── INTERSECTION OBSERVER (animate on scroll) ────────────── */
const AnimationObserver = (() => {
    const io = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el = entry.target;

            // Progress ring
            if (el.dataset.ring !== undefined) {
                const value = parseInt(el.dataset.ring, 10) || 0;
                const color = el.dataset.ringColor || undefined;
                const label = el.dataset.ringLabel || '';
                const size  = parseInt(el.dataset.ringSize, 10) || 90;
                renderProgressRing(el, value, { color, label, size });
                io.unobserve(el);
                return;
            }

            // Count-up
            if (el.dataset.countTo !== undefined) {
                const to = parseInt(el.dataset.countTo, 10) || 0;
                const from = parseInt(el.dataset.countFrom, 10) || 0;
                const suffix = el.dataset.countSuffix || '';
                animateCount(el, from, to, 1000, suffix);
                io.unobserve(el);
                return;
            }

            // Generic fade
            el.classList.add('fade-in-up');
            io.unobserve(el);
        });
    }, { threshold: 0.15 });

    function observe(selector = '[data-animate]') {
        document.querySelectorAll(selector).forEach(el => io.observe(el));
        document.querySelectorAll('[data-ring]').forEach(el => io.observe(el));
        document.querySelectorAll('[data-count-to]').forEach(el => io.observe(el));
    }

    return { observe };
})();


/* ── PROGRESS BARS (animate on scroll) ───────────────────── */
function initProgressBars() {
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const bar = entry.target;
            const target = bar.dataset.width || bar.style.width;
            bar.style.width = '0%';
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    bar.style.transition = 'width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1)';
                    bar.style.width = target;
                });
            });
            observer.unobserve(bar);
        });
    }, { threshold: 0.2 });

    document.querySelectorAll('.progress-bar[data-width]').forEach(bar => {
        bar.dataset.width = bar.style.width || bar.getAttribute('data-width') || '0%';
        bar.style.width = '0%';
        observer.observe(bar);
    });
}


/* ── SCORE BAR ROWS (auto color) ─────────────────────────── */
function colorScoreBars() {
    document.querySelectorAll('.score-bar-fill').forEach(bar => {
        if (bar.dataset.colored) return;
        bar.dataset.colored = '1';
        const val = parseInt(bar.style.width) || parseInt(bar.getAttribute('data-width')) || 0;
        if (val >= 80)      bar.style.background = 'var(--success)';
        else if (val >= 60) bar.style.background = 'linear-gradient(90deg, var(--primary), var(--info))';
        else if (val >= 40) bar.style.background = 'var(--warning)';
        else                bar.style.background = 'var(--danger)';
    });
}


/* ── AI LOADING STEPS ────────────────────────────────────── */
function showAILoading(steps = [], containerId = 'aiLoadingOverlay') {
    let overlay = document.getElementById(containerId);
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = containerId;
        overlay.className = 'ai-loading-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-label', 'AI processing');
        overlay.innerHTML = `
            <div class="ai-loading-card scale-in">
                <div class="mb-4" style="font-size:2.5rem; animation: float 2s ease infinite;">🤖</div>
                <div class="ai-loading-title">AI is working…</div>
                <div class="ai-loading-sub">Please wait while we analyze your data</div>
                <div class="ai-loading-steps" id="${containerId}Steps"></div>
            </div>`;
        document.body.appendChild(overlay);
    }

    const stepsEl = document.getElementById(`${containerId}Steps`);
    if (!stepsEl) return overlay;

    steps.forEach((text, i) => {
        const step = document.createElement('div');
        step.className = 'ai-step';
        step.dataset.index = i;
        step.innerHTML = `
            <div class="ai-step-icon">${i + 1}</div>
            <span>${text}</span>`;
        stepsEl.appendChild(step);
    });

    // Animate steps
    let current = 0;
    function nextStep() {
        const stepEls = stepsEl.querySelectorAll('.ai-step');
        if (current > 0 && stepEls[current - 1]) {
            stepEls[current - 1].classList.remove('active');
            stepEls[current - 1].classList.add('done');
            stepEls[current - 1].querySelector('.ai-step-icon').innerHTML = '<i class="bi bi-check"></i>';
        }
        if (current < stepEls.length) {
            stepEls[current].classList.add('active');
            current++;
            const delay = 800 + Math.random() * 600;
            setTimeout(nextStep, delay);
        }
    }

    setTimeout(nextStep, 300);
    return overlay;
}

function hideAILoading(containerId = 'aiLoadingOverlay') {
    const overlay = document.getElementById(containerId);
    if (overlay) {
        overlay.style.opacity = '0';
        overlay.style.transition = 'opacity 0.3s';
        setTimeout(() => overlay.remove(), 300);
    }
}

window.showAILoading = showAILoading;
window.hideAILoading = hideAILoading;


/* ── ACCORDION ───────────────────────────────────────────── */
function initAccordions() {
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', function() {
            const body = this.nextElementSibling;
            const isOpen = this.classList.contains('open');
            this.classList.toggle('open', !isOpen);
            if (body && body.classList.contains('accordion-body')) {
                body.classList.toggle('open', !isOpen);
            }
        });
    });
}


/* ── TABS ─────────────────────────────────────────────────── */
function initTabs() {
    document.querySelectorAll('[data-tab-group]').forEach(group => {
        const groupName = group.dataset.tabGroup;
        group.addEventListener('click', e => {
            const btn = e.target.closest('.tab-btn[data-tab]');
            if (!btn) return;
            const target = btn.dataset.tab;

            // Toggle buttons
            document.querySelectorAll(`[data-tab-group="${groupName}"] .tab-btn`).forEach(b => {
                b.classList.toggle('active', b.dataset.tab === target);
            });
            // Toggle panels
            document.querySelectorAll(`[data-tab-panel="${groupName}"]`).forEach(panel => {
                panel.style.display = panel.dataset.tab === target ? '' : 'none';
            });
        });

        // Activate first tab by default
        const firstBtn = group.querySelector('.tab-btn[data-tab]');
        if (firstBtn && !group.querySelector('.tab-btn.active')) {
            firstBtn.click();
        }
    });
}


/* ── DRAG & DROP UPLOAD ─────────────────────────────────── */
function initUploadZones() {
    document.querySelectorAll('.upload-zone[data-upload-input]').forEach(zone => {
        const inputId = zone.dataset.uploadInput;
        const input = document.getElementById(inputId);
        if (!input) return;

        zone.addEventListener('click', () => input.click());
        zone.addEventListener('dragover', e => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });
        zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
        zone.addEventListener('drop', e => {
            e.preventDefault();
            zone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                input.files = e.dataTransfer.files;
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        input.addEventListener('change', () => {
            const file = input.files[0];
            if (file) {
                const nameEl = zone.querySelector('[data-upload-name]');
                if (nameEl) nameEl.textContent = file.name;
                zone.classList.add('has-file');
            }
        });
    });
}


/* ── DEBOUNCE ─────────────────────────────────────────────── */
function debounce(fn, wait = 300) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), wait);
    };
}

window.debounce = debounce;


/* ── SCORE COLOR HELPER ──────────────────────────────────── */
function getScoreColor(score) {
    if (score >= 80) return 'var(--success)';
    if (score >= 60) return 'var(--primary)';
    if (score >= 40) return 'var(--warning)';
    return 'var(--danger)';
}

function getScoreBadgeClass(score) {
    if (score >= 80) return 'score-excellent';
    if (score >= 60) return 'score-good';
    if (score >= 40) return 'score-average';
    return 'score-poor';
}

window.getScoreColor = getScoreColor;
window.getScoreBadgeClass = getScoreBadgeClass;


/* ── CONFIRMATION DIALOG ─────────────────────────────────── */
function confirmAction(message, onConfirm, opts = {}) {
    const title = opts.title || 'Are you sure?';
    const confirmText = opts.confirmText || 'Confirm';
    const cancelText  = opts.cancelText  || 'Cancel';
    const dangerous   = opts.dangerous !== false;

    let modal = document.getElementById('confirmModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'confirmModal';
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('role', 'dialog');
        modal.innerHTML = `
            <div class="modal-dialog modal-sm modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="confirmTitle"></h5>
                    </div>
                    <div class="modal-body">
                        <p id="confirmMessage" class="text-secondary-color" style="margin:0;"></p>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary btn-sm" data-bs-dismiss="modal" id="confirmCancel"></button>
                        <button class="btn btn-sm" id="confirmOk"></button>
                    </div>
                </div>
            </div>`;
        document.body.appendChild(modal);
    }

    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    document.getElementById('confirmCancel').textContent = cancelText;
    const okBtn = document.getElementById('confirmOk');
    okBtn.textContent = confirmText;
    okBtn.className = `btn btn-sm ${dangerous ? 'btn-danger' : 'btn-primary'}`;

    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();

    const handler = () => {
        bsModal.hide();
        onConfirm();
    };
    okBtn.removeEventListener('click', okBtn._handler);
    okBtn._handler = handler;
    okBtn.addEventListener('click', handler, { once: true });
}

window.confirmAction = confirmAction;


/* ── COPY TO CLIPBOARD ───────────────────────────────────── */
function copyToClipboard(text, feedbackEl) {
    navigator.clipboard?.writeText(text).then(() => {
        if (feedbackEl) {
            const orig = feedbackEl.innerHTML;
            feedbackEl.innerHTML = '<i class="bi bi-check2"></i>';
            setTimeout(() => { feedbackEl.innerHTML = orig; }, 2000);
        }
        Toast.success('Copied to clipboard!');
    }).catch(() => Toast.error('Copy failed.'));
}

window.copyToClipboard = copyToClipboard;


/* ── SKILL CHIPS ──────────────────────────────────────────── */
function initSkillChips() {
    document.querySelectorAll('[data-remove-chip]').forEach(btn => {
        btn.addEventListener('click', function() {
            const chip = this.closest('.skill-chip');
            const hiddenInput = document.getElementById(this.dataset.removeChip);
            if (chip) {
                chip.style.transform = 'scale(0)';
                chip.style.opacity = '0';
                chip.style.transition = 'all 0.15s';
                setTimeout(() => chip.remove(), 150);
                if (hiddenInput) hiddenInput.remove();
            }
        });
    });
}


/* ── FORM AI LOADING (intercept submit) ─────────────────── */
function attachAIFormLoading(formId, steps) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', function(e) {
        const btn = form.querySelector('[type=submit]');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="spin me-2" style="display:inline-block">⟳</span> Processing…';
        }
        if (steps && steps.length) {
            showAILoading(steps);
        }
    });
}

window.attachAIFormLoading = attachAIFormLoading;


/* ── GLOBAL SEARCH PLACEHOLDER ───────────────────────────── */
function initGlobalSearch() {
    const searchInput = document.getElementById('globalSearch');
    if (!searchInput) return;

    searchInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            const q = searchInput.value.trim();
            if (q) {
                // Route to company search if it looks like a company
                window.location.href = `/company?q=${encodeURIComponent(q)}`;
            }
        }
    });
}


/* ── CHART DEFAULTS ──────────────────────────────────────── */
function setChartDefaults() {
    if (!window.Chart) return;
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = '#64748B';
    Chart.defaults.borderColor = '#E2E8F0';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 16;
    Chart.defaults.plugins.tooltip.backgroundColor = '#0F172A';
    Chart.defaults.plugins.tooltip.titleColor = '#F8FAFC';
    Chart.defaults.plugins.tooltip.bodyColor = '#CBD5E1';
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.displayColors = false;
}


/* ── AUTO-DISMISS ALERTS ─────────────────────────────────── */
function initAlertAutoDismiss(ms = 5000) {
    document.querySelectorAll('.alert.alert-success, .alert.alert-info').forEach(alert => {
        setTimeout(() => {
            if (alert.isConnected) {
                const bsAlert = bootstrap.Alert.getInstance(alert);
                bsAlert ? bsAlert.close() : alert.remove();
            }
        }, ms);
    });
}


/* ── PROGRESS BARS ────────────────────────────────────────── */
function initProgressBars() {
    setTimeout(() => {
        document.querySelectorAll('.progress-bar').forEach(bar => {
            const width = bar.getAttribute('data-width');
            if (width) {
                bar.style.width = width;
                bar.style.transition = 'width 1s ease-in-out';
            }
        });
    }, 100);
}


/* ── INIT ─────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
    SidebarManager.init();
    initAccordions();
    initTabs();
    initUploadZones();
    initProgressBars();
    initSkillChips();
    initGlobalSearch();
    colorScoreBars();
    setChartDefaults();
    initAlertAutoDismiss();
    AnimationObserver.observe();
});
