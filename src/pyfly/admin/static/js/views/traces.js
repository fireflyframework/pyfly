/**
 * PyFly Admin — Traces View.
 *
 * Real-time HTTP trace viewer with SSE live updates,
 * pause/resume toggle, clear functionality, status filter pills,
 * and click-to-detail panel.
 *
 * Data sources:
 *   GET /admin/api/traces     -> { traces: [...], total: N }
 *   SSE /admin/api/sse/traces -> event type "trace"
 */

import { createMethodBadge } from '../components/status-badge.js';
import { sse } from '../sse.js';

/* ── Helpers ──────────────────────────────────────────────────── */

/**
 * Format an ISO timestamp to a compact time string.
 * @param {string|Date} ts
 * @returns {string}
 */
function formatTime(ts) {
    if (!ts) return '--';
    try {
        const d = ts instanceof Date ? ts : new Date(ts);
        return d.toLocaleTimeString(undefined, {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        });
    } catch (_) {
        return '--';
    }
}

/**
 * Return a CSS class for an HTTP status code.
 * @param {number} status
 * @returns {string}
 */
function statusColorClass(status) {
    if (status >= 500) return 'badge-danger';
    if (status >= 400) return 'badge-warning';
    if (status >= 300) return 'badge-info';
    if (status >= 200) return 'badge-success';
    return 'badge-neutral';
}

/**
 * Create a status badge element.
 * @param {number} status
 * @returns {HTMLSpanElement}
 */
function createStatusCodeBadge(status) {
    const badge = document.createElement('span');
    badge.className = `badge ${statusColorClass(status)}`;
    badge.textContent = String(status);
    return badge;
}

/**
 * Get the status group for filtering (e.g. "2xx", "4xx").
 * @param {number} status
 * @returns {string}
 */
function statusGroup(status) {
    if (status >= 500) return '5xx';
    if (status >= 400) return '4xx';
    if (status >= 300) return '3xx';
    if (status >= 200) return '2xx';
    return 'other';
}

/* ── Detail Panel ────────────────────────────────────────────── */

function createDetailPanel() {
    const overlay = document.createElement('div');
    overlay.className = 'detail-panel-overlay';

    const panel = document.createElement('div');
    panel.className = 'detail-panel';

    const panelHeader = document.createElement('div');
    panelHeader.className = 'detail-panel-header';
    const panelTitle = document.createElement('h3');
    panelTitle.textContent = 'Trace Detail';
    panelHeader.appendChild(panelTitle);

    const closeBtn = document.createElement('button');
    closeBtn.className = 'detail-panel-close';
    closeBtn.setAttribute('aria-label', 'Close detail panel');
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    const l1 = document.createElementNS(svgNS, 'line');
    l1.setAttribute('x1', '18'); l1.setAttribute('y1', '6');
    l1.setAttribute('x2', '6');  l1.setAttribute('y2', '18');
    svg.appendChild(l1);
    const l2 = document.createElementNS(svgNS, 'line');
    l2.setAttribute('x1', '6');  l2.setAttribute('y1', '6');
    l2.setAttribute('x2', '18'); l2.setAttribute('y2', '18');
    svg.appendChild(l2);
    closeBtn.appendChild(svg);
    panelHeader.appendChild(closeBtn);
    panel.appendChild(panelHeader);

    const panelBody = document.createElement('div');
    panelBody.className = 'detail-panel-body';
    panel.appendChild(panelBody);

    function hide() {
        overlay.classList.remove('open');
        panel.classList.remove('open');
    }

    closeBtn.addEventListener('click', hide);
    overlay.addEventListener('click', hide);

    function show(trace) {
        panelBody.textContent = '';
        panelTitle.textContent = `${trace.method} ${trace.path}`;

        const kv = document.createElement('table');
        kv.className = 'kv-table';

        const rows = [
            ['Timestamp', formatTime(trace.timestamp)],
            ['Method', () => createMethodBadge(trace.method)],
            ['Path', trace.path || '--'],
            ['Query String', trace.query_string || '--'],
            ['Status', () => createStatusCodeBadge(trace.status)],
            ['Duration', (trace.duration_ms != null ? trace.duration_ms.toFixed(1) : '--') + ' ms'],
            ['Client Host', trace.client_host || '--'],
            ['Content Type', trace.content_type || '--'],
            ['Content Length', trace.content_length != null ? String(trace.content_length) + ' bytes' : '--'],
            ['User Agent', trace.user_agent || '--'],
        ];

        for (const [label, value] of rows) {
            const tr = document.createElement('tr');
            const th = document.createElement('th');
            th.textContent = label;
            tr.appendChild(th);
            const td = document.createElement('td');
            if (typeof value === 'function') {
                td.appendChild(value());
            } else {
                const span = document.createElement('span');
                span.className = label === 'User Agent' ? 'text-sm' : 'mono';
                span.textContent = value;
                td.appendChild(span);
            }
            tr.appendChild(td);
            kv.appendChild(tr);
        }
        panelBody.appendChild(kv);

        overlay.classList.add('open');
        panel.classList.add('open');
    }

    return { overlay, panel, show, hide };
}

/**
 * Create a table row from a trace object.
 * @param {object} trace
 * @param {function} onClick
 * @returns {HTMLTableRowElement}
 */
function createTraceRow(trace, onClick) {
    const tr = document.createElement('tr');
    tr.classList.add('clickable');
    tr.addEventListener('click', () => onClick(trace));

    // Time
    const tdTime = document.createElement('td');
    tdTime.textContent = formatTime(trace.timestamp);
    tdTime.className = 'text-mono text-sm';
    tr.appendChild(tdTime);

    // Method
    const tdMethod = document.createElement('td');
    tdMethod.appendChild(createMethodBadge(trace.method));
    tr.appendChild(tdMethod);

    // Path
    const tdPath = document.createElement('td');
    const pathSpan = document.createElement('span');
    pathSpan.className = 'mono';
    pathSpan.textContent = trace.path || '--';
    tdPath.appendChild(pathSpan);
    tr.appendChild(tdPath);

    // Status
    const tdStatus = document.createElement('td');
    tdStatus.appendChild(createStatusCodeBadge(trace.status));
    tr.appendChild(tdStatus);

    // Duration
    const tdDuration = document.createElement('td');
    tdDuration.className = 'text-mono text-sm';
    const ms = trace.duration_ms != null ? trace.duration_ms.toFixed(1) : '--';
    tdDuration.textContent = ms + ' ms';
    tr.appendChild(tdDuration);

    return tr;
}

/* ── Render ───────────────────────────────────────────────────── */

/**
 * Render the traces view.
 * @param {HTMLElement} container
 * @param {import('../api.js').AdminAPI} api
 * @returns {function} Cleanup function to disconnect SSE.
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
    h1.textContent = 'Traces';
    headerLeft.appendChild(h1);
    const sub = document.createElement('div');
    sub.className = 'page-subtitle';
    sub.textContent = 'application.traces';
    headerLeft.appendChild(sub);
    header.appendChild(headerLeft);

    // Header right: Pause/Resume + Clear buttons
    const headerRight = document.createElement('div');
    headerRight.style.display = 'flex';
    headerRight.style.gap = '8px';

    const pauseBtn = document.createElement('button');
    pauseBtn.className = 'btn btn-sm';
    pauseBtn.textContent = 'Pause';

    const clearBtn = document.createElement('button');
    clearBtn.className = 'btn btn-sm';
    clearBtn.textContent = 'Clear';

    headerRight.appendChild(pauseBtn);
    headerRight.appendChild(clearBtn);
    header.appendChild(headerRight);
    wrapper.appendChild(header);

    // Loading
    const loader = document.createElement('div');
    loader.className = 'loading-spinner';
    wrapper.appendChild(loader);
    container.appendChild(wrapper);

    // Fetch initial traces
    let data;
    try {
        data = await api.get('/traces');
    } catch (err) {
        wrapper.removeChild(loader);
        const errCard = document.createElement('div');
        errCard.className = 'admin-card';
        const errBody = document.createElement('div');
        errBody.className = 'admin-card-body empty-state';
        const errText = document.createElement('div');
        errText.className = 'empty-state-text';
        errText.textContent = 'Failed to load traces: ' + err.message;
        errBody.appendChild(errText);
        errCard.appendChild(errBody);
        wrapper.appendChild(errCard);
        return;
    }

    wrapper.removeChild(loader);

    // Trace data (mutable array)
    const traces = data.traces || [];

    // ── Detail panel ─────────────────────────────────────────
    const { overlay, panel, show } = createDetailPanel();
    wrapper.appendChild(overlay);
    wrapper.appendChild(panel);

    // ── Stats row ────────────────────────────────────────────
    const statsRow = document.createElement('div');
    statsRow.className = 'grid-2 mb-lg';

    const totalCard = document.createElement('div');
    totalCard.className = 'stat-card';
    const totalContent = document.createElement('div');
    totalContent.className = 'stat-card-content';
    const totalVal = document.createElement('div');
    totalVal.className = 'stat-card-value';
    totalVal.textContent = String(traces.length);
    totalContent.appendChild(totalVal);
    const totalLabel = document.createElement('div');
    totalLabel.className = 'stat-card-label';
    totalLabel.textContent = 'Total Traces';
    totalContent.appendChild(totalLabel);
    totalCard.appendChild(totalContent);
    statsRow.appendChild(totalCard);

    const avgCard = document.createElement('div');
    avgCard.className = 'stat-card';
    const avgContent = document.createElement('div');
    avgContent.className = 'stat-card-content';
    const avgVal = document.createElement('div');
    avgVal.className = 'stat-card-value';
    const avgDuration = traces.length > 0
        ? (traces.reduce((sum, t) => sum + (t.duration_ms || 0), 0) / traces.length).toFixed(1)
        : '0.0';
    avgVal.textContent = avgDuration + ' ms';
    avgContent.appendChild(avgVal);
    const avgLabel = document.createElement('div');
    avgLabel.className = 'stat-card-label';
    avgLabel.textContent = 'Avg Duration';
    avgContent.appendChild(avgLabel);
    avgCard.appendChild(avgContent);
    statsRow.appendChild(avgCard);

    wrapper.appendChild(statsRow);

    // ── Status filter pills ──────────────────────────────────
    let activeFilter = '';
    const pillBar = document.createElement('div');
    pillBar.className = 'filter-pills mb-md';

    const filterOptions = ['All', '2xx', '3xx', '4xx', '5xx'];
    const pillButtons = [];

    for (const label of filterOptions) {
        const pill = document.createElement('button');
        pill.className = 'filter-pill';
        pill.textContent = label;
        if (label === 'All') pill.classList.add('active');
        pill.addEventListener('click', () => {
            activeFilter = label === 'All' ? '' : label;
            for (const p of pillButtons) p.classList.remove('active');
            pill.classList.add('active');
            renderTraces();
        });
        pillButtons.push(pill);
        pillBar.appendChild(pill);
    }
    wrapper.appendChild(pillBar);

    // ── Trace table ──────────────────────────────────────────
    const tableCard = document.createElement('div');
    tableCard.className = 'admin-card';

    const tableHeader = document.createElement('div');
    tableHeader.className = 'admin-card-header';
    const tableTitle = document.createElement('h3');
    tableTitle.textContent = 'HTTP Traces';
    tableHeader.appendChild(tableTitle);

    const liveIndicator = document.createElement('span');
    liveIndicator.className = 'badge badge-success';
    const liveDot = document.createElement('span');
    liveDot.className = 'badge-dot';
    liveIndicator.appendChild(liveDot);
    const liveText = document.createElement('span');
    liveText.textContent = 'LIVE';
    liveIndicator.appendChild(liveText);
    tableHeader.appendChild(liveIndicator);

    tableCard.appendChild(tableHeader);

    const tableWrap = document.createElement('div');
    tableWrap.className = 'admin-table-wrapper';
    tableWrap.style.maxHeight = '500px';
    tableWrap.style.overflowY = 'auto';

    const table = document.createElement('table');
    table.className = 'admin-table';

    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');
    const colHeaders = ['Time', 'Method', 'Path', 'Status', 'Duration'];
    for (const label of colHeaders) {
        const th = document.createElement('th');
        th.textContent = label;
        headRow.appendChild(th);
    }
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    function renderTraces() {
        tbody.replaceChildren();
        const filtered = activeFilter
            ? traces.filter((t) => statusGroup(t.status) === activeFilter)
            : traces;

        if (filtered.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 5;
            td.style.textAlign = 'center';
            td.style.padding = '32px 16px';
            td.style.color = 'var(--admin-text-muted)';
            td.textContent = activeFilter ? `No ${activeFilter} traces` : 'No traces recorded';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }
        for (const trace of filtered) {
            tbody.appendChild(createTraceRow(trace, show));
        }
    }

    renderTraces();
    table.appendChild(tbody);
    tableWrap.appendChild(table);
    tableCard.appendChild(tableWrap);
    wrapper.appendChild(tableCard);

    // ── Stats updater ────────────────────────────────────────
    function updateStats() {
        totalVal.textContent = String(traces.length);
        if (traces.length > 0) {
            const avg = traces.reduce((s, t) => s + (t.duration_ms || 0), 0) / traces.length;
            avgVal.textContent = avg.toFixed(1) + ' ms';
        } else {
            avgVal.textContent = '0.0 ms';
        }
    }

    // ── SSE: Real-time trace updates ─────────────────────────
    let paused = false;

    sse.connectTyped('/traces', 'trace', (traceData) => {
        if (paused) return;
        traces.unshift(traceData);

        // Only insert into DOM if the trace matches the active filter
        if (!activeFilter || statusGroup(traceData.status) === activeFilter) {
            const newRow = createTraceRow(traceData, show);
            if (tbody.firstChild) {
                tbody.insertBefore(newRow, tbody.firstChild);
            } else {
                tbody.replaceChildren();
                tbody.appendChild(newRow);
            }
        }
        updateStats();
    });

    // ── Pause/Resume ─────────────────────────────────────────
    pauseBtn.addEventListener('click', () => {
        paused = !paused;
        pauseBtn.textContent = paused ? 'Resume' : 'Pause';
        if (paused) {
            liveText.textContent = 'PAUSED';
            liveIndicator.className = 'badge badge-warning';
        } else {
            liveText.textContent = 'LIVE';
            liveIndicator.className = 'badge badge-success';
        }
    });

    // ── Clear ────────────────────────────────────────────────
    clearBtn.addEventListener('click', () => {
        traces.length = 0;
        renderTraces();
        updateStats();
    });

    // ── Cleanup ──────────────────────────────────────────────
    return function cleanup() {
        sse.disconnect('/traces');
    };
}
