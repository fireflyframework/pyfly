/**
 * PyFly Admin — Wallboard View.
 *
 * Full-screen wallboard mode for large displays showing key metrics
 * as a 3x3 grid of tiles with real-time SSE updates for health,
 * runtime (memory, threads, gc, cpu), and server data.
 *
 * Data sources:
 *   GET  /admin/api/overview
 *   GET  /admin/api/runtime
 *   GET  /admin/api/server
 *   SSE  /admin/api/sse/runtime  (event: runtime)
 *   SSE  /admin/api/sse/health   (event: health)
 *   SSE  /admin/api/sse/server   (event: server)
 */

import { sse } from '../sse.js';

/* ── Helpers ──────────────────────────────────────────────────── */

/**
 * Format a duration in seconds to a human-readable string.
 * @param {number|null|undefined} seconds
 * @returns {string}  e.g. "2d 5h 13m"
 */
function formatUptime(seconds) {
    if (seconds == null || seconds < 0) return '--';
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const parts = [];
    if (d > 0) parts.push(`${d}d`);
    if (h > 0 || d > 0) parts.push(`${h}h`);
    parts.push(`${m}m`);
    return parts.join(' ');
}

/**
 * Format a bean total with stereotype breakdown.
 * @param {object|null} beans  The beans object from overview.
 * @returns {string}  e.g. "42" or "--"
 */
function formatBeans(beans) {
    if (!beans || beans.total == null) return '--';
    const stereotypes = beans.stereotypes;
    if (!stereotypes || Object.keys(stereotypes).length === 0) {
        return String(beans.total);
    }
    const parts = Object.entries(stereotypes)
        .map(([k, v]) => `${v} ${k}`)
        .join(', ');
    return `${beans.total} (${parts})`;
}

/**
 * Sum all GC generation collections.
 * @param {object|null} gc  The gc object from runtime.
 * @returns {string}  e.g. "111" or "--"
 */
function formatGC(gc) {
    if (!gc) return '--';
    const total = (gc.gen0_collections || 0)
        + (gc.gen1_collections || 0)
        + (gc.gen2_collections || 0);
    return String(total);
}

/**
 * Format CPU process time.
 * @param {object|null} cpu  The cpu object from runtime.
 * @returns {string}  e.g. "12.5s" or "--"
 */
function formatCPU(cpu) {
    if (!cpu || cpu.process_time_s == null) return '--';
    return `${cpu.process_time_s.toFixed(1)}s`;
}

/**
 * Format server info as "name (Nw)".
 * @param {object|null} server  The server data.
 * @returns {string}  e.g. "granian (1w)" or "--"
 */
function formatServer(server) {
    if (!server || !server.name) return '--';
    const workers = server.workers != null ? ` (${server.workers}w)` : '';
    return `${server.name}${workers}`;
}

/**
 * Format health status with component count.
 * @param {object|null} health  The health data.
 * @returns {string}  e.g. "UP (3)" or "UNKNOWN"
 */
function formatHealth(health) {
    if (!health || !health.status) return 'UNKNOWN';
    const components = health.components;
    if (components && typeof components === 'object') {
        const count = Object.keys(components).length;
        if (count > 0) return `${health.status} (${count})`;
    }
    return health.status;
}

/**
 * Create a wallboard tile element with a large value and label.
 * @param {string} label
 * @param {string} value
 * @param {string} [cssVar]  CSS custom property name for the value colour.
 * @returns {HTMLDivElement}
 */
function createTile(label, value, cssVar) {
    const tile = document.createElement('div');
    tile.className = 'wallboard-tile';

    const valueEl = document.createElement('div');
    valueEl.className = 'wallboard-tile-value';
    if (cssVar) valueEl.style.color = `var(${cssVar})`;
    valueEl.textContent = value;
    tile.appendChild(valueEl);

    const labelEl = document.createElement('div');
    labelEl.className = 'wallboard-tile-label';
    labelEl.textContent = label;
    tile.appendChild(labelEl);

    return tile;
}

/* ── Render ───────────────────────────────────────────────────── */

/**
 * Render the wallboard view.
 * @param {HTMLElement} container
 * @param {import('../api.js').AdminAPI} api
 * @returns {Promise<function>} Cleanup function.
 */
export async function render(container, api) {
    document.body.classList.add('wallboard-mode');
    container.replaceChildren();

    // Fetch initial data from all three endpoints
    const [overview, runtime, server] = await Promise.all([
        api.get('/overview').catch(() => null),
        api.get('/runtime').catch(() => null),
        api.get('/server').catch(() => null),
    ]);

    // Build 3x3 tile grid
    const grid = document.createElement('div');
    grid.className = 'wallboard-grid';

    // ── Row 1 ──────────────────────────────────────────────────

    // Health tile — status with component count
    const healthTile = createTile(
        'Health',
        formatHealth(overview?.health),
        '--admin-success',
    );
    healthTile.id = 'wb-health';
    grid.appendChild(healthTile);

    // Memory tile — RSS in MB
    const memoryValue = runtime?.memory?.rss_mb != null
        ? `${runtime.memory.rss_mb.toFixed(1)} MB`
        : '--';
    const memTile = createTile('Memory', memoryValue, '--admin-primary');
    memTile.id = 'wb-memory';
    grid.appendChild(memTile);

    // CPU tile — process time
    const cpuTile = createTile('CPU', formatCPU(runtime?.cpu), '--admin-info');
    cpuTile.id = 'wb-cpu';
    grid.appendChild(cpuTile);

    // ── Row 2 ──────────────────────────────────────────────────

    // Beans tile — total with breakdown
    const beansTile = createTile(
        'Beans',
        formatBeans(overview?.beans),
        '--admin-warning',
    );
    beansTile.id = 'wb-beans';
    grid.appendChild(beansTile);

    // Threads tile — active count
    const threadTile = createTile(
        'Threads',
        String(runtime?.threads?.active ?? '--'),
        '--admin-text',
    );
    threadTile.id = 'wb-threads';
    grid.appendChild(threadTile);

    // GC tile — total collections across all generations
    const gcTile = createTile('GC', formatGC(runtime?.gc), '--admin-danger');
    gcTile.id = 'wb-gc';
    grid.appendChild(gcTile);

    // ── Row 3 ──────────────────────────────────────────────────

    // Server tile — name with worker count
    const serverTile = createTile(
        'Server',
        formatServer(server),
        '--admin-primary',
    );
    serverTile.id = 'wb-server';
    grid.appendChild(serverTile);

    // Uptime tile — formatted duration
    const uptimeTile = createTile(
        'Uptime',
        formatUptime(overview?.app?.uptime_seconds),
        '--admin-text',
    );
    uptimeTile.id = 'wb-uptime';
    grid.appendChild(uptimeTile);

    // Requests tile — placeholder until metrics available
    const requestsTile = createTile('Requests', '--', '--admin-info');
    requestsTile.id = 'wb-requests';
    grid.appendChild(requestsTile);

    container.appendChild(grid);

    // ── SSE live updates ───────────────────────────────────────

    // SSE for live runtime updates (memory, threads, gc, cpu)
    sse.connectTyped('/runtime', 'runtime', (data) => {
        const memValue = document.querySelector('#wb-memory .wallboard-tile-value');
        if (memValue && data.memory) {
            memValue.textContent = `${data.memory.rss_mb.toFixed(1)} MB`;
        }

        const threadValue = document.querySelector('#wb-threads .wallboard-tile-value');
        if (threadValue && data.threads) {
            threadValue.textContent = String(data.threads.active);
        }

        const gcValue = document.querySelector('#wb-gc .wallboard-tile-value');
        if (gcValue && data.gc) {
            gcValue.textContent = formatGC(data.gc);
        }

        const cpuValue = document.querySelector('#wb-cpu .wallboard-tile-value');
        if (cpuValue && data.cpu) {
            cpuValue.textContent = formatCPU(data.cpu);
        }
    });

    // SSE for live health updates
    sse.connectTyped('/health', 'health', (data) => {
        const healthValue = document.querySelector('#wb-health .wallboard-tile-value');
        if (healthValue) {
            healthValue.textContent = formatHealth(data);
        }
    });

    // SSE for live server updates
    sse.connectTyped('/server', 'server', (data) => {
        const serverValue = document.querySelector('#wb-server .wallboard-tile-value');
        if (serverValue) {
            serverValue.textContent = formatServer(data);
        }
    });

    // ── ESC key exits wallboard mode ───────────────────────────

    function escHandler(e) {
        if (e.key === 'Escape') window.location.hash = '';
    }
    document.addEventListener('keydown', escHandler);

    // Exit hint
    const hint = document.createElement('div');
    hint.className = 'wallboard-hint';
    hint.textContent = 'Press ESC to exit wallboard mode';
    container.appendChild(hint);

    return function cleanup() {
        document.body.classList.remove('wallboard-mode');
        document.removeEventListener('keydown', escHandler);
        sse.disconnect('/runtime');
        sse.disconnect('/health');
        sse.disconnect('/server');
    };
}
