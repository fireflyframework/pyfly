/**
 * PyFly Admin — Toast Notification System.
 *
 * Slides in from top-right, auto-dismisses. Safe DOM only.
 */

/** SVG icon paths for each toast type. */
const TOAST_ICONS = {
    success: 'M22 11.08V12a10 10 0 11-5.93-9.14 M22 4L12 14.01l-3-3',
    error:   'M12 2a10 10 0 100 20 10 10 0 000-20z M15 9l-6 6 M9 9l6 6',
    warning: 'M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z M12 9v4 M12 17h.01',
    info:    'M12 2a10 10 0 100 20 10 10 0 000-20z M12 16v-4 M12 8h.01',
};

/** CSS class for each toast type. */
const TOAST_CLASSES = {
    success: 'toast-success',
    error:   'toast-error',
    warning: 'toast-warning',
    info:    'toast-info',
};

/**
 * Create an SVG icon element.
 */
function createIcon(pathData) {
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('class', 'toast-icon');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');

    const segments = pathData.split(/(?= M)/);
    for (const seg of segments) {
        const path = document.createElementNS(svgNS, 'path');
        path.setAttribute('d', seg.trim());
        svg.appendChild(path);
    }

    return svg;
}

/**
 * Show a toast notification.
 *
 * @param {string} message   Text to display.
 * @param {string} [type]    "success" | "error" | "warning" | "info"
 * @param {number} [duration] Auto-dismiss after ms (default 3000). 0 = no auto-dismiss.
 */
export function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${TOAST_CLASSES[type] || TOAST_CLASSES.info}`;

    // Icon
    const iconPath = TOAST_ICONS[type] || TOAST_ICONS.info;
    toast.appendChild(createIcon(iconPath));

    // Message
    const msg = document.createElement('span');
    msg.className = 'toast-message';
    msg.textContent = message;
    toast.appendChild(msg);

    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.className = 'toast-close';
    closeBtn.setAttribute('aria-label', 'Close');

    const svgNS = 'http://www.w3.org/2000/svg';
    const closeSvg = document.createElementNS(svgNS, 'svg');
    closeSvg.setAttribute('viewBox', '0 0 24 24');
    closeSvg.setAttribute('fill', 'none');
    closeSvg.setAttribute('stroke', 'currentColor');
    closeSvg.setAttribute('stroke-width', '2');
    closeSvg.setAttribute('stroke-linecap', 'round');
    closeSvg.setAttribute('stroke-linejoin', 'round');
    const p1 = document.createElementNS(svgNS, 'path');
    p1.setAttribute('d', 'M18 6L6 18');
    closeSvg.appendChild(p1);
    const p2 = document.createElementNS(svgNS, 'path');
    p2.setAttribute('d', 'M6 6l12 12');
    closeSvg.appendChild(p2);
    closeBtn.appendChild(closeSvg);

    closeBtn.addEventListener('click', () => dismiss(toast));
    toast.appendChild(closeBtn);

    container.appendChild(toast);

    // Auto-dismiss
    if (duration > 0) {
        setTimeout(() => dismiss(toast), duration);
    }
}

function dismiss(toast) {
    if (!toast.parentNode) return;
    toast.classList.add('removing');
    toast.addEventListener('animationend', () => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
    });
}
