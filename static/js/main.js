/**
 * Prescription Scanner - Main JavaScript
 */

// Toggle password visibility
function togglePassword(fieldId) {
    const field = document.getElementById(fieldId);
    const icon = document.getElementById('eye-' + fieldId);
    if (!field || !icon) return;
    if (field.type === 'password') {
        field.type = 'text';
        icon.classList.replace('bi-eye', 'bi-eye-slash');
    } else {
        field.type = 'password';
        icon.classList.replace('bi-eye-slash', 'bi-eye');
    }
}

// Auto-dismiss alerts after 6 seconds
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert.alert-custom');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 6000);
    });

    // Register form validation
    const registerForm = document.querySelector('form[action*="register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function (e) {
            const agree = document.getElementById('agree');
            if (agree && !agree.checked) {
                e.preventDefault();
                showToast('Please acknowledge the disclaimer to continue.', 'warning');
            }
        });
    }

    // Animate stat values on dashboard
    const statValues = document.querySelectorAll('.stat-value');
    statValues.forEach(function (el) {
        const text = el.textContent.trim();
        const num = parseFloat(text);
        if (!isNaN(num) && !text.includes('%')) {
            animateNumber(el, 0, num, 900);
        }
    });
});

function animateNumber(el, from, to, duration) {
    const start = performance.now();
    const suffix = el.textContent.includes('%') ? '%' : '';
    function update(time) {
        const elapsed = time - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(from + (to - from) * eased) + suffix;
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

function showToast(msg, type) {
    type = type || 'info';
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-custom alert-dismissible fade show`;
    toast.style.cssText = 'position:fixed;top:80px;right:24px;z-index:9999;min-width:280px;max-width:400px;box-shadow:0 4px 16px rgba(0,0,0,.15);';
    toast.innerHTML = `<i class="bi bi-info-circle me-2"></i>${msg}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    document.body.appendChild(toast);
    setTimeout(() => {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(toast);
        if (bsAlert) bsAlert.close();
    }, 5000);
}
