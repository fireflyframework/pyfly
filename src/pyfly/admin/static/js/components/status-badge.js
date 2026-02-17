/**
 * PyFly Admin — Status & Method Badge Components.
 *
 * Safe DOM construction — no innerHTML with untrusted data.
 */

/** Map health status to CSS class. */
const STATUS_MAP = {
    UP:             'badge-up',
    DOWN:           'badge-down',
    OUT_OF_SERVICE: 'badge-warning',
    UNKNOWN:        'badge-unknown',
};

/** Map HTTP method to CSS class. */
const METHOD_MAP = {
    GET:    'badge-get',
    POST:   'badge-post',
    PUT:    'badge-put',
    DELETE: 'badge-delete',
    PATCH:  'badge-patch',
    HEAD:   'badge-neutral',
    OPTIONS: 'badge-neutral',
};

/**
 * Create a health-status badge element.
 *
 * @param {string} status  e.g. "UP", "DOWN", "OUT_OF_SERVICE", "UNKNOWN"
 * @returns {HTMLElement}
 */
export function createStatusBadge(status) {
    const badge = document.createElement('span');
    const normalised = (status || 'UNKNOWN').toUpperCase();
    const cls = STATUS_MAP[normalised] || 'badge-unknown';
    badge.className = `badge ${cls}`;

    // Pulsing dot
    const dot = document.createElement('span');
    dot.className = 'badge-dot';
    badge.appendChild(dot);

    // Label text
    const label = document.createElement('span');
    label.textContent = normalised.replace(/_/g, ' ');
    badge.appendChild(label);

    return badge;
}

/**
 * Create an HTTP-method badge element.
 *
 * @param {string} method  e.g. "GET", "POST", "DELETE"
 * @returns {HTMLElement}
 */
export function createMethodBadge(method) {
    const badge = document.createElement('span');
    const normalised = (method || 'GET').toUpperCase();
    const cls = METHOD_MAP[normalised] || 'badge-neutral';
    badge.className = `badge badge-method ${cls}`;
    badge.textContent = normalised;
    return badge;
}
