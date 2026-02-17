/**
 * PyFly Admin — Mappings View.
 *
 * Displays HTTP request mappings with color-coded method badges,
 * searchable by path or controller name.
 *
 * Data source:
 *   GET /admin/api/mappings -> { mappings: [...], total: N }
 */

import { createMethodBadge } from '../components/status-badge.js';
import { createTable } from '../components/table.js';

/* ── Render ───────────────────────────────────────────────────── */

/**
 * Render the mappings view.
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
    h1.textContent = 'Mappings';
    headerLeft.appendChild(h1);
    const sub = document.createElement('div');
    sub.className = 'page-subtitle';
    sub.textContent = 'application.mappings';
    headerLeft.appendChild(sub);
    header.appendChild(headerLeft);
    wrapper.appendChild(header);

    // Loading
    const loader = document.createElement('div');
    loader.className = 'loading-spinner';
    wrapper.appendChild(loader);
    container.appendChild(wrapper);

    // Fetch mappings
    let data;
    try {
        data = await api.get('/mappings');
    } catch (err) {
        wrapper.removeChild(loader);
        const errCard = document.createElement('div');
        errCard.className = 'admin-card';
        const errBody = document.createElement('div');
        errBody.className = 'admin-card-body empty-state';
        const errText = document.createElement('div');
        errText.className = 'empty-state-text';
        errText.textContent = 'Failed to load mappings: ' + err.message;
        errBody.appendChild(errText);
        errCard.appendChild(errBody);
        wrapper.appendChild(errCard);
        return;
    }

    wrapper.removeChild(loader);

    const mappings = data.mappings || [];
    const total = data.total != null ? data.total : mappings.length;

    // ── Stat card ────────────────────────────────────────────────
    const statsRow = document.createElement('div');
    statsRow.className = 'grid-4 mb-lg';

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
    totalLabel.textContent = 'Total Mappings';
    totalContent.appendChild(totalLabel);
    totalCard.appendChild(totalContent);
    statsRow.appendChild(totalCard);

    wrapper.appendChild(statsRow);

    // ── Empty state ──────────────────────────────────────────────
    if (total === 0) {
        const emptyCard = document.createElement('div');
        emptyCard.className = 'admin-card';
        const emptyBody = document.createElement('div');
        emptyBody.className = 'admin-card-body empty-state';
        const emptyText = document.createElement('div');
        emptyText.className = 'empty-state-text';
        emptyText.textContent = 'No request mappings';
        emptyBody.appendChild(emptyText);
        emptyCard.appendChild(emptyBody);
        wrapper.appendChild(emptyCard);
        return;
    }

    // ── Table ────────────────────────────────────────────────────
    const tableCard = document.createElement('div');
    tableCard.className = 'admin-card';

    const tableHeader = document.createElement('div');
    tableHeader.className = 'admin-card-header';
    const tableTitle = document.createElement('h3');
    tableTitle.textContent = 'Request Mappings';
    tableHeader.appendChild(tableTitle);
    tableCard.appendChild(tableHeader);

    const tableBody = document.createElement('div');
    tableBody.className = 'admin-card-body';
    tableBody.style.padding = '0';

    const tableEl = createTable({
        columns: [
            {
                key: 'method',
                label: 'Method',
                render(val) {
                    return createMethodBadge(val);
                },
            },
            {
                key: 'path',
                label: 'Path',
                render(val) {
                    const span = document.createElement('span');
                    span.className = 'mono';
                    span.textContent = val || '--';
                    return span;
                },
            },
            {
                key: 'controller',
                label: 'Controller',
                render(val) {
                    const span = document.createElement('span');
                    span.textContent = val || '--';
                    return span;
                },
            },
            {
                key: 'handler',
                label: 'Handler',
                render(val) {
                    const span = document.createElement('span');
                    span.className = 'mono';
                    span.textContent = val || '--';
                    return span;
                },
            },
            {
                key: 'status_code',
                label: 'Status Code',
                render(val) {
                    const span = document.createElement('span');
                    span.className = 'mono';
                    span.textContent = val != null ? String(val) : '--';
                    return span;
                },
            },
        ],
        data: mappings,
        searchable: true,
        sortable: true,
        emptyText: 'No request mappings',
    });

    tableBody.appendChild(tableEl);
    tableCard.appendChild(tableBody);
    wrapper.appendChild(tableCard);
}
