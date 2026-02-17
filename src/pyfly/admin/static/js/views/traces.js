/**
 * PyFly Admin — Traces View.
 *
 * Real-time HTTP trace viewer with SSE live updates,
 * pause/resume toggle, and clear functionality.
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
 * Create a table row from a trace object.
 * @param {object} trace
 * @param {string[]} columns  Column keys for ordering
 * @returns {HTMLTableRowElement}
 */
function createTraceRow(trace) {
    const tr = document.createElement('tr');

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

    // ── Stats row ────────────────────────────────────────────
    const statsRow = document.createElement('div');
    statsRow.className = 'grid-2 mb-lg';

    // Total traces stat
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

    // Average duration stat
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

    // Table head
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

    // Table body
    const tbody = document.createElement('tbody');

    function renderTraces() {
        tbody.replaceChildren();
        if (traces.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 5;
            td.style.textAlign = 'center';
            td.style.padding = '32px 16px';
            td.style.color = 'var(--admin-text-muted)';
            td.textContent = 'No traces recorded';
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }
        for (const trace of traces) {
            tbody.appendChild(createTraceRow(trace));
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
        // Prepend new trace
        traces.unshift(traceData);
        // Insert at top of tbody
        const newRow = createTraceRow(traceData);
        if (tbody.firstChild) {
            tbody.insertBefore(newRow, tbody.firstChild);
        } else {
            // Was showing empty state, clear it first
            tbody.replaceChildren();
            tbody.appendChild(newRow);
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
