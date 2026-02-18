/**
 * PyFly Admin — Metrics View.
 *
 * Metric browser with searchable list and drill-down detail panel.
 * Split layout: metric names on left, measurement detail on right.
 *
 * Data sources:
 *   GET /admin/api/metrics          -> { names: [...], available: boolean }
 *   GET /admin/api/metrics/{name}   -> { name, measurements: [{statistic, value, tags}, ...] }
 */

import { createFilterToolbar } from '../components/filter-toolbar.js';

/* ── Helpers ──────────────────────────────────────────────────── */

/**
 * Build a measurements table for a single metric.
 * @param {Array<{statistic: string, value: *, tags: object}>} measurements
 * @returns {HTMLElement}
 */
function buildMeasurementsTable(measurements) {
    if (!measurements || measurements.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'text-muted text-sm';
        empty.style.padding = '16px 0';
        empty.textContent = 'No data available';
        return empty;
    }

    const tableWrap = document.createElement('div');
    tableWrap.className = 'admin-table-wrapper';

    const table = document.createElement('table');
    table.className = 'admin-table';

    // Head
    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');
    for (const label of ['Statistic', 'Value', 'Tags']) {
        const th = document.createElement('th');
        th.textContent = label;
        headRow.appendChild(th);
    }
    thead.appendChild(headRow);
    table.appendChild(thead);

    // Body
    const tbody = document.createElement('tbody');
    for (const m of measurements) {
        const tr = document.createElement('tr');

        const tdStat = document.createElement('td');
        tdStat.textContent = m.statistic || '--';
        tr.appendChild(tdStat);

        const tdVal = document.createElement('td');
        const valSpan = document.createElement('span');
        valSpan.className = 'text-mono';
        valSpan.textContent = m.value != null ? String(m.value) : '--';
        tdVal.appendChild(valSpan);
        tr.appendChild(tdVal);

        const tdTags = document.createElement('td');
        if (m.tags && Object.keys(m.tags).length > 0) {
            const tagSpan = document.createElement('span');
            tagSpan.className = 'text-mono text-sm';
            tagSpan.textContent = JSON.stringify(m.tags);
            tdTags.appendChild(tagSpan);
        } else {
            tdTags.className = 'text-muted';
            tdTags.textContent = '--';
        }
        tr.appendChild(tdTags);

        tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    tableWrap.appendChild(table);
    return tableWrap;
}

/* ── Render ───────────────────────────────────────────────────── */

/**
 * Render the metrics browser view.
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
    h1.textContent = 'Metrics';
    headerLeft.appendChild(h1);
    const sub = document.createElement('div');
    sub.className = 'page-subtitle';
    sub.textContent = 'application.metrics';
    headerLeft.appendChild(sub);
    header.appendChild(headerLeft);
    wrapper.appendChild(header);

    // Loading
    const loader = document.createElement('div');
    loader.className = 'loading-spinner';
    wrapper.appendChild(loader);
    container.appendChild(wrapper);

    // Fetch metric names
    let data;
    try {
        data = await api.get('/metrics');
    } catch (err) {
        wrapper.removeChild(loader);
        const errCard = document.createElement('div');
        errCard.className = 'admin-card';
        const errBody = document.createElement('div');
        errBody.className = 'admin-card-body empty-state';
        const errText = document.createElement('div');
        errText.className = 'empty-state-text';
        errText.textContent = 'Failed to load metrics: ' + err.message;
        errBody.appendChild(errText);
        errCard.appendChild(errBody);
        wrapper.appendChild(errCard);
        return;
    }

    wrapper.removeChild(loader);

    // If Prometheus / metrics not available
    if (data.available === false) {
        const infoCard = document.createElement('div');
        infoCard.className = 'admin-card';
        const infoBody = document.createElement('div');
        infoBody.className = 'admin-card-body empty-state';
        const infoText = document.createElement('div');
        infoText.className = 'empty-state-text';
        infoText.textContent = 'Metrics are not available. Ensure Prometheus or a metrics provider is configured.';
        infoBody.appendChild(infoText);
        infoCard.appendChild(infoBody);
        wrapper.appendChild(infoCard);
        return;
    }

    const names = data.names || [];

    if (names.length === 0) {
        const emptyCard = document.createElement('div');
        emptyCard.className = 'admin-card';
        const emptyBody = document.createElement('div');
        emptyBody.className = 'admin-card-body empty-state';
        const emptyText = document.createElement('div');
        emptyText.className = 'empty-state-text';
        emptyText.textContent = 'No metrics registered';
        emptyBody.appendChild(emptyText);
        emptyCard.appendChild(emptyBody);
        wrapper.appendChild(emptyCard);
        return;
    }

    // ── Filter toolbar ──────────────────────────────────────────
    const toolbar = createFilterToolbar({
        placeholder: 'Search metrics...',
        pills: [
            { label: 'All', value: '' },
            { label: 'HTTP', value: 'http' },
            { label: 'System', value: 'system' },
            { label: 'Process', value: 'process' },
            { label: 'Custom', value: 'custom' },
        ],
        onFilter: ({ search, pill }) => {
            renderMetricList(search, pill);
        },
        totalCount: names.length,
    });
    wrapper.appendChild(toolbar);

    // ── Stat cards row ──────────────────────────────────────────
    const statsRow = document.createElement('div');
    statsRow.className = 'grid-4 mb-lg';

    const totalCard = document.createElement('div');
    totalCard.className = 'stat-card';
    const totalContent = document.createElement('div');
    totalContent.className = 'stat-card-content';
    const totalVal = document.createElement('div');
    totalVal.className = 'stat-card-value';
    totalVal.textContent = String(names.length);
    totalContent.appendChild(totalVal);
    const totalLabel = document.createElement('div');
    totalLabel.className = 'stat-card-label';
    totalLabel.textContent = 'Total Metrics';
    totalContent.appendChild(totalLabel);
    totalCard.appendChild(totalContent);
    statsRow.appendChild(totalCard);

    wrapper.appendChild(statsRow);

    // ── Split layout ────────────────────────────────────────────
    const splitLayout = document.createElement('div');
    splitLayout.style.display = 'flex';
    splitLayout.style.gap = '16px';
    splitLayout.style.alignItems = 'flex-start';

    // ── Left panel: metric list ─────────────────────────────────
    const leftPanel = document.createElement('div');
    leftPanel.className = 'admin-card';
    leftPanel.style.width = '300px';
    leftPanel.style.minWidth = '300px';
    leftPanel.style.flexShrink = '0';

    const leftHeader = document.createElement('div');
    leftHeader.className = 'admin-card-header';
    const leftTitle = document.createElement('h3');
    leftTitle.textContent = 'Metrics';
    leftHeader.appendChild(leftTitle);
    const countBadge = document.createElement('span');
    countBadge.className = 'badge badge-neutral';
    countBadge.textContent = String(names.length);
    leftHeader.appendChild(countBadge);
    leftPanel.appendChild(leftHeader);

    const leftBody = document.createElement('div');
    leftBody.style.padding = '12px';

    // Metric list container (scrollable)
    const metricList = document.createElement('div');
    metricList.style.maxHeight = '520px';
    metricList.style.overflowY = 'auto';

    let activeItem = null;

    /**
     * Build and render metric name items, filtered by search text and pill.
     * @param {string} search  Lowercase search text.
     * @param {string} pill    Pill value (prefix filter).
     */
    function renderMetricList(search, pill) {
        metricList.replaceChildren();
        activeItem = null;

        const filtered = names.filter((n) => {
            const lower = n.toLowerCase();
            // Pill filter: metric name must start with the pill value
            if (pill && !lower.startsWith(pill)) return false;
            // Search filter: metric name must include the search text
            if (search && !lower.includes(search)) return false;
            return true;
        });

        // Update toolbar count
        toolbar.updateCount(filtered.length, names.length);

        // Update left panel badge count
        countBadge.textContent = String(filtered.length);

        if (filtered.length === 0) {
            const noMatch = document.createElement('div');
            noMatch.className = 'text-muted text-sm';
            noMatch.style.padding = '12px 8px';
            noMatch.textContent = 'No matching metrics';
            metricList.appendChild(noMatch);
            return;
        }

        for (const name of filtered) {
            const item = document.createElement('div');
            item.style.padding = '8px 12px';
            item.style.cursor = 'pointer';
            item.style.borderRadius = 'var(--admin-radius)';
            item.style.fontSize = '0.85rem';
            item.style.fontFamily = 'var(--admin-font-mono)';
            item.style.transition = 'background var(--admin-transition)';
            item.style.wordBreak = 'break-all';
            item.textContent = name;

            item.addEventListener('mouseenter', () => {
                if (item !== activeItem) {
                    item.style.background = 'var(--admin-surface-hover)';
                }
            });
            item.addEventListener('mouseleave', () => {
                if (item !== activeItem) {
                    item.style.background = '';
                }
            });

            item.addEventListener('click', () => {
                // Deselect previous
                if (activeItem) {
                    activeItem.style.background = '';
                    activeItem.style.color = '';
                }
                activeItem = item;
                item.style.background = 'var(--admin-primary-dim)';
                item.style.color = 'var(--admin-primary)';
                loadMetricDetail(name);
            });

            metricList.appendChild(item);
        }
    }

    renderMetricList('', '');
    leftBody.appendChild(metricList);
    leftPanel.appendChild(leftBody);
    splitLayout.appendChild(leftPanel);

    // ── Right panel: metric detail ──────────────────────────────
    const rightPanel = document.createElement('div');
    rightPanel.style.flex = '1';
    rightPanel.style.minWidth = '0';

    const detailCard = document.createElement('div');
    detailCard.className = 'admin-card';

    const detailBody = document.createElement('div');
    detailBody.className = 'admin-card-body';

    // Initial placeholder
    const placeholder = document.createElement('div');
    placeholder.className = 'empty-state';
    const placeholderText = document.createElement('div');
    placeholderText.className = 'empty-state-text';
    placeholderText.textContent = 'Select a metric from the list to view details';
    placeholder.appendChild(placeholderText);
    detailBody.appendChild(placeholder);

    detailCard.appendChild(detailBody);
    rightPanel.appendChild(detailCard);
    splitLayout.appendChild(rightPanel);

    wrapper.appendChild(splitLayout);

    /**
     * Load and display metric detail data.
     * @param {string} metricName
     */
    async function loadMetricDetail(metricName) {
        detailBody.replaceChildren();

        // Loading state
        const loadingEl = document.createElement('div');
        loadingEl.className = 'loading-spinner';
        detailBody.appendChild(loadingEl);

        try {
            const detail = await api.get('/metrics/' + encodeURIComponent(metricName));
            detailBody.replaceChildren();

            // Metric name header
            const nameHeader = document.createElement('h3');
            nameHeader.style.marginBottom = '16px';
            nameHeader.style.fontSize = '1rem';
            nameHeader.style.fontWeight = '600';
            nameHeader.style.fontFamily = 'var(--admin-font-mono)';
            nameHeader.style.wordBreak = 'break-all';
            nameHeader.textContent = detail.name || metricName;
            detailBody.appendChild(nameHeader);

            // Measurements table
            const measurements = detail.measurements || [];
            detailBody.appendChild(buildMeasurementsTable(measurements));
        } catch (err) {
            detailBody.replaceChildren();
            const errMsg = document.createElement('div');
            errMsg.className = 'text-muted text-sm';
            errMsg.style.padding = '16px 0';
            errMsg.textContent = 'Failed to load metric detail: ' + err.message;
            detailBody.appendChild(errMsg);
        }
    }
}
