/* ============================================================
   KiteTrade — main.js
   Global utilities: format, toast, modal, clock, market status
   ============================================================ */

// ── INR Formatter ───────────────────────────────────────────
function fmt(num) {
    if (num === null || num === undefined || isNaN(num)) return '₹—';
    const n = parseFloat(num);
    return '₹' + Math.abs(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// ── Toast Notifications ──────────────────────────────────────
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;
    setTimeout(() => { toast.className = 'toast hidden'; }, 3500);
}

// ── Modal ─────────────────────────────────────────────────────
let _modalCallback = null;

function showModal(title, body, onConfirm) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').textContent = body;
    document.getElementById('modalOverlay').classList.remove('hidden');
    _modalCallback = onConfirm;
}

function closeModal() {
    document.getElementById('modalOverlay').classList.add('hidden');
    _modalCallback = null;
}

document.addEventListener('DOMContentLoaded', () => {
    const confirmBtn = document.getElementById('modalConfirmBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', () => {
            if (_modalCallback) _modalCallback();
            closeModal();
        });
    }

    // Close modal on overlay click
    const overlay = document.getElementById('modalOverlay');
    if (overlay) {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeModal();
        });
    }

    // Start clock
    updateClock();
    setInterval(updateClock, 1000);

    // Market status
    updateMarketStatus();
    setInterval(updateMarketStatus, 60000);
});

// ── IST Clock ─────────────────────────────────────────────────
function updateClock() {
    const el = document.getElementById('topbarTime');
    if (!el) return;
    const now = new Date();
    const ist = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
    const h = String(ist.getHours()).padStart(2, '0');
    const m = String(ist.getMinutes()).padStart(2, '0');
    const s = String(ist.getSeconds()).padStart(2, '0');
    el.textContent = `IST ${h}:${m}:${s}`;
}

// ── Market Status ─────────────────────────────────────────────
function updateMarketStatus() {
    const statusText = document.getElementById('marketStatusText');
    const statusDot = document.querySelector('.status-dot');
    if (!statusText) return;

    const now = new Date();
    const ist = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
    const day = ist.getDay(); // 0=Sun, 6=Sat
    const h = ist.getHours();
    const m = ist.getMinutes();
    const timeVal = h * 60 + m;
    const open = 9 * 60 + 15;
    const close = 15 * 60 + 30;

    const isWeekday = day >= 1 && day <= 5;
    const isOpen = isWeekday && timeVal >= open && timeVal < close;

    statusText.textContent = isOpen ? 'Market Open' : 'Market Closed';
    if (statusDot) {
        statusDot.classList.toggle('closed', !isOpen);
    }
}
