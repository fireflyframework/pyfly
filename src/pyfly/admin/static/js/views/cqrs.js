/**
 * PyFly Admin — CQRS View.
 *
 * Displays CQRS command and query handler registrations with
 * stat cards, searchable table, and kind badges.
 *
 * Data source:
 *   GET /admin/api/cqrs -> { handlers: [...], total: N }
 */

import { createTable } from '../components/table.js';

/* ── Helpers ──────────────────────────────────────────────────── */

/** Badge CSS class per handler kind. */
const KIND_CLASSES = {
    command: 'badge-info',
    query:   'badge-success',
};

/**
 * Create a kind badge element (command=blue, query=green).
 * @param {string} kind
 * @returns {HTMLSpanElement}
 */
function createKindBadge(kind) {
    const badge = document.createElement('span');
    const norm = (kind || '').toLowerCase();
    const cls = KIND_CLASSES[norm] || 'badge-neutral';
    badge.className = `badge ${cls}`;
    badge.textContent = (kind || '--').toUpperCase();
    return badge;
}

/**
 * Truncate a module path, keeping the last two segments.
 * e.g. "myapp.handlers.create_user.CreateUserHandler" -> "...create_user.CreateUserHandler"
 * @param {string} typePath
 * @returns {string}
 */
function truncateType(typePath) {
    if (!typePath) return '--';
    const parts = typePath.split('.');
    if (parts.length <= 2) return typePath;
    return '...' + parts.slice(-2).join('.');
}

/* ── Render ───────────────────────────────────────────────────── */

/**
 * Render the CQRS handler listing view.
 * @param {HTMLElement} container
 * @param {import('../api.js').AdminAPI} api
 */
export async function render(container, api) {
    container.replaceChildren();

    const wrapper = document.createElement('div');
    wrapper.className = 'view-enter';

    // Page header
    const header = document.createElement('div');
    header.className = 'page-header';
    const headerLeft = document.createElement('div');
    const h1 = document.createElement('h1');
    h1.textContent = 'CQRS';
    headerLeft.appendChild(h1);
    const sub = document.createElement('div');
    sub.className = 'page-subtitle';
    sub.textContent = 'application.cqrs';
    headerLeft.appendChild(sub);
    header.appendChild(headerLeft);
    wrapper.appendChild(header);

    // Loading
    const loader = document.createElement('div');
    loader.className = 'loading-spinner';
    wrapper.appendChild(loader);
    container.appendChild(wrapper);

    // Fetch CQRS data
    let data;
    try {
        data = await api.get('/cqrs');
    } catch (err) {
        wrapper.removeChild(loader);
        const errCard = document.createElement('div');
        errCard.className = 'admin-card';
        const errBody = document.createElement('div');
        errBody.className = 'admin-card-body empty-state';
        const errText = document.createElement('div');
        errText.className = 'empty-state-text';
        errText.textContent = 'Failed to load CQRS data: ' + err.message;
        errBody.appendChild(errText);
        errCard.appendChild(errBody);
        wrapper.appendChild(errCard);
        return;
    }

    wrapper.removeChild(loader);

    const handlers = data.handlers || [];
    const total = data.total != null ? data.total : handlers.length;
    const commandCount = handlers.filter(h => h.kind === 'command').length;
    const queryCount = handlers.filter(h => h.kind === 'query').length;

    // ── Stat cards row ───────────────────────────────────────
    const statsRow = document.createElement('div');
    statsRow.className = 'grid-3 mb-lg';

    // Total handlers
    const totalCard = document.createElement('div');
    totalCard.className = 'stat-card';
    const totalContent = document.createElement('div');
    totalContent.className = 'stat-card-content';
    const totalVal = document.createElement('div');
    totalVal.className = 'stat-card-value';
    totalVal.textContent = String(total);
    totalContent.appendChild(totalVal);
    const totalLabel = document.createElement('div');
    totalLabel.className = 'stat-card-label';
    totalLabel.textContent = 'Total Handlers';
    totalContent.appendChild(totalLabel);
    totalCard.appendChild(totalContent);
    statsRow.appendChild(totalCard);

    // Commands count
    const cmdCard = document.createElement('div');
    cmdCard.className = 'stat-card';
    const cmdContent = document.createElement('div');
    cmdContent.className = 'stat-card-content';
    const cmdVal = document.createElement('div');
    cmdVal.className = 'stat-card-value';
    cmdVal.textContent = String(commandCount);
    cmdContent.appendChild(cmdVal);
    const cmdLabel = document.createElement('div');
    cmdLabel.className = 'stat-card-label';
    cmdLabel.textContent = 'Commands';
    cmdContent.appendChild(cmdLabel);
    cmdCard.appendChild(cmdContent);
    statsRow.appendChild(cmdCard);

    // Queries count
    const qryCard = document.createElement('div');
    qryCard.className = 'stat-card';
    const qryContent = document.createElement('div');
    qryContent.className = 'stat-card-content';
    const qryVal = document.createElement('div');
    qryVal.className = 'stat-card-value';
    qryVal.textContent = String(queryCount);
    qryContent.appendChild(qryVal);
    const qryLabel = document.createElement('div');
    qryLabel.className = 'stat-card-label';
    qryLabel.textContent = 'Queries';
    qryContent.appendChild(qryLabel);
    qryCard.appendChild(qryContent);
    statsRow.appendChild(qryCard);

    wrapper.appendChild(statsRow);

    // ── Handlers table ───────────────────────────────────────
    const tableCard = document.createElement('div');
    tableCard.className = 'admin-card';

    const tableHeader = document.createElement('div');
    tableHeader.className = 'admin-card-header';
    const tableTitle = document.createElement('h3');
    tableTitle.textContent = 'Registered Handlers';
    tableHeader.appendChild(tableTitle);
    tableCard.appendChild(tableHeader);

    const tableBody = document.createElement('div');
    tableBody.className = 'admin-card-body';
    tableBody.style.padding = '0';

    const tableEl = createTable({
        columns: [
            {
                key: 'kind',
                label: 'Kind',
                render(val) {
                    return createKindBadge(val);
                },
            },
            {
                key: 'message_name',
                label: 'Message Name',
                render(val) {
                    const span = document.createElement('span');
                    span.style.fontWeight = '500';
                    span.textContent = val || '--';
                    return span;
                },
            },
            {
                key: 'handler_name',
                label: 'Handler Name',
                render(val) {
                    const span = document.createElement('span');
                    span.textContent = val || '--';
                    return span;
                },
            },
            {
                key: 'message_type',
                label: 'Full Type',
                render(val) {
                    const span = document.createElement('span');
                    span.className = 'mono truncate';
                    span.style.maxWidth = '280px';
                    span.style.display = 'inline-block';
                    span.title = val || '';
                    span.textContent = truncateType(val);
                    return span;
                },
            },
        ],
        data: handlers,
        searchable: true,
        sortable: true,
        emptyText: 'No CQRS handlers registered',
    });

    tableBody.appendChild(tableEl);
    tableCard.appendChild(tableBody);
    wrapper.appendChild(tableCard);
}
