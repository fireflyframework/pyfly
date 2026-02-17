/**
 * PyFly Admin — Loggers View.
 *
 * Displays application loggers with runtime level management.
 * Supports searching/filtering by name and changing log levels
 * with instant POST feedback and toast notifications.
 *
 * Data source:  GET  /admin/api/loggers
 *   -> { loggers: { "ROOT": { configuredLevel, effectiveLevel }, ... }, levels: [...] }
 * Action:       POST /admin/api/loggers/{name}  body: { level: "DEBUG" }
 */

import { showToast } from '../components/toast.js';

/* ── Helpers ──────────────────────────────────────────────────── */

/** Map log level names to CSS colour values. */
const LEVEL_COLORS = {
    TRACE:    'var(--admin-text-muted)',
    DEBUG:    'var(--admin-info)',
    INFO:     'var(--admin-primary)',
    WARNING:  'var(--admin-warning)',
    WARN:     'var(--admin-warning)',
    ERROR:    'var(--admin-danger)',
    CRITICAL: 'var(--admin-danger)',
    FATAL:    'var(--admin-danger)',
};

/**
 * Create a styled level label element.
 * @param {string} level
 * @returns {HTMLSpanElement}
 */
function createLevelLabel(level) {
    const span = document.createElement('span');
    span.className = 'text-mono';
    span.style.fontSize = '0.8rem';
    span.style.fontWeight = '600';
    span.textContent = level || '--';

    const color = LEVEL_COLORS[(level || '').toUpperCase()] || 'var(--admin-text-muted)';
    span.style.color = color;

    if ((level || '').toUpperCase() === 'CRITICAL' || (level || '').toUpperCase() === 'FATAL') {
        span.style.fontWeight = '700';
    }

    return span;
}

/**
 * Create a search icon SVG.
 * @returns {SVGElement}
 */
function createSearchIcon() {
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('width', '16');
    svg.setAttribute('height', '16');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    const circle = document.createElementNS(svgNS, 'circle');
    circle.setAttribute('cx', '11');
    circle.setAttribute('cy', '11');
    circle.setAttribute('r', '8');
    svg.appendChild(circle);
    const line = document.createElementNS(svgNS, 'line');
    line.setAttribute('x1', '21');
    line.setAttribute('y1', '21');
    line.setAttribute('x2', '16.65');
    line.setAttribute('y2', '16.65');
    svg.appendChild(line);
    return svg;
}

/* ── Render ───────────────────────────────────────────────────── */

/**
 * Render the loggers view.
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
    h1.textContent = 'Loggers';
    headerLeft.appendChild(h1);
    const sub = document.createElement('div');
    sub.className = 'page-subtitle';
    sub.textContent = 'application.loggers';
    headerLeft.appendChild(sub);
    header.appendChild(headerLeft);
    wrapper.appendChild(header);

    // Loading
    const loader = document.createElement('div');
    loader.className = 'loading-spinner';
    wrapper.appendChild(loader);
    container.appendChild(wrapper);

    // Fetch loggers data
    let loggersData;
    try {
        loggersData = await api.get('/loggers');
    } catch (err) {
        wrapper.removeChild(loader);
        const errCard = document.createElement('div');
        errCard.className = 'admin-card';
        const errBody = document.createElement('div');
        errBody.className = 'admin-card-body empty-state';
        const errText = document.createElement('div');
        errText.className = 'empty-state-text';
        errText.textContent = 'Failed to load loggers: ' + err.message;
        errBody.appendChild(errText);
        errCard.appendChild(errBody);
        wrapper.appendChild(errCard);
        return;
    }

    wrapper.removeChild(loader);

    const loggersMap = loggersData.loggers || {};
    const levels = loggersData.levels || ['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];

    // Convert loggers map to array for the table
    const loggerEntries = Object.entries(loggersMap).map(([name, info]) => ({
        name,
        configuredLevel: info.configuredLevel || info.configured_level || '--',
        effectiveLevel: info.effectiveLevel || info.effective_level || '--',
    }));

    // ── Stat cards ───────────────────────────────────────────
    const statsRow = document.createElement('div');
    statsRow.className = 'grid-3 mb-lg';

    const totalCard = document.createElement('div');
    totalCard.className = 'stat-card';
    const totalContent = document.createElement('div');
    totalContent.className = 'stat-card-content';
    const totalVal = document.createElement('div');
    totalVal.className = 'stat-card-value';
    totalVal.textContent = String(loggerEntries.length);
    totalContent.appendChild(totalVal);
    const totalLabel = document.createElement('div');
    totalLabel.className = 'stat-card-label';
    totalLabel.textContent = 'Total Loggers';
    totalContent.appendChild(totalLabel);
    totalCard.appendChild(totalContent);
    statsRow.appendChild(totalCard);

    // Count by effective level
    const levelCounts = {};
    for (const entry of loggerEntries) {
        const lvl = entry.effectiveLevel.toUpperCase();
        levelCounts[lvl] = (levelCounts[lvl] || 0) + 1;
    }
    const topLevels = Object.entries(levelCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 2);

    for (const [lvl, count] of topLevels) {
        const card = document.createElement('div');
        card.className = 'stat-card';
        const cardContent = document.createElement('div');
        cardContent.className = 'stat-card-content';
        const cardVal = document.createElement('div');
        cardVal.className = 'stat-card-value';
        cardVal.textContent = String(count);
        cardContent.appendChild(cardVal);
        const cardLabel = document.createElement('div');
        cardLabel.className = 'stat-card-label';
        cardLabel.textContent = lvl + ' Level';
        cardContent.appendChild(cardLabel);
        card.appendChild(cardContent);
        statsRow.appendChild(card);
    }

    wrapper.appendChild(statsRow);

    // ── Loggers table card ───────────────────────────────────
    const tableCard = document.createElement('div');
    tableCard.className = 'admin-card';

    const tableCardHeader = document.createElement('div');
    tableCardHeader.className = 'admin-card-header';
    const tableTitle = document.createElement('h3');
    tableTitle.textContent = 'Loggers';
    tableCardHeader.appendChild(tableTitle);
    tableCard.appendChild(tableCardHeader);

    const tableBody = document.createElement('div');
    tableBody.className = 'admin-card-body';
    tableBody.style.padding = '12px 20px 0';

    // Search bar
    const searchWrap = document.createElement('div');
    searchWrap.className = 'search-input';
    searchWrap.style.marginBottom = '12px';
    searchWrap.appendChild(createSearchIcon());

    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'input';
    searchInput.placeholder = 'Filter loggers by name\u2026';
    searchWrap.appendChild(searchInput);
    tableBody.appendChild(searchWrap);

    // Table container
    const tableWrap = document.createElement('div');
    tableWrap.className = 'admin-table-wrapper';

    const table = document.createElement('table');
    table.className = 'admin-table';

    // Table head
    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');
    const headers = ['Name', 'Configured Level', 'Effective Level', 'Actions'];
    for (const label of headers) {
        const th = document.createElement('th');
        th.textContent = label;
        headRow.appendChild(th);
    }
    thead.appendChild(headRow);
    table.appendChild(thead);

    // Table body
    const tbody = document.createElement('tbody');
    table.appendChild(tbody);

    /**
     * Render the table body based on the current filter.
     * @param {string} filter
     */
    function renderTableBody(filter) {
        tbody.replaceChildren();

        const filtered = filter
            ? loggerEntries.filter((e) => e.name.toLowerCase().includes(filter))
            : loggerEntries;

        if (filtered.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 4;
            td.style.textAlign = 'center';
            td.style.padding = '32px 16px';
            td.style.color = 'var(--admin-text-muted)';
            td.textContent = filter ? 'No loggers match the filter' : 'No loggers found';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }

        for (const entry of filtered) {
            const tr = document.createElement('tr');

            // Name column
            const tdName = document.createElement('td');
            const nameSpan = document.createElement('span');
            nameSpan.className = 'mono';
            nameSpan.textContent = entry.name;
            tdName.appendChild(nameSpan);
            tr.appendChild(tdName);

            // Configured Level column
            const tdConfigured = document.createElement('td');
            tdConfigured.appendChild(createLevelLabel(entry.configuredLevel));
            tr.appendChild(tdConfigured);

            // Effective Level column
            const tdEffective = document.createElement('td');
            tdEffective.appendChild(createLevelLabel(entry.effectiveLevel));
            tr.appendChild(tdEffective);

            // Actions column — level change dropdown
            const tdActions = document.createElement('td');
            const select = document.createElement('select');
            select.className = 'select';
            select.style.width = 'auto';
            select.style.minWidth = '120px';
            select.style.padding = '4px 28px 4px 8px';
            select.style.fontSize = '0.8rem';

            for (const lvl of levels) {
                const option = document.createElement('option');
                option.value = lvl;
                option.textContent = lvl;
                if (lvl.toUpperCase() === entry.configuredLevel.toUpperCase()) {
                    option.selected = true;
                }
                select.appendChild(option);
            }

            select.addEventListener('change', async () => {
                const newLevel = select.value;
                try {
                    await api.post(
                        '/loggers/' + encodeURIComponent(entry.name),
                        { level: newLevel }
                    );
                    // Update local state
                    entry.configuredLevel = newLevel;
                    entry.effectiveLevel = newLevel;

                    // Update the displayed level labels in this row
                    tdConfigured.replaceChildren();
                    tdConfigured.appendChild(createLevelLabel(newLevel));
                    tdEffective.replaceChildren();
                    tdEffective.appendChild(createLevelLabel(newLevel));

                    showToast(
                        'Logger "' + entry.name + '" set to ' + newLevel,
                        'success'
                    );
                } catch (err) {
                    showToast(
                        'Failed to update logger: ' + err.message,
                        'error'
                    );
                    // Reset select to previous value
                    select.value = entry.configuredLevel;
                }
            });

            tdActions.appendChild(select);
            tr.appendChild(tdActions);

            tbody.appendChild(tr);
        }
    }

    // Wire up search filtering
    searchInput.addEventListener('input', () => {
        renderTableBody(searchInput.value.toLowerCase());
    });

    // Initial render
    renderTableBody('');

    tableWrap.appendChild(table);
    tableBody.appendChild(tableWrap);
    tableCard.appendChild(tableBody);
    wrapper.appendChild(tableCard);
}
