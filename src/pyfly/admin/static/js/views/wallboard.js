/**
 * PyFly Admin — Wallboard View.
 *
 * Full-screen wallboard mode for large displays showing key metrics
 * as large tiles with real-time SSE updates for memory, threads,
 * and health status.
 *
 * Data sources:
 *   GET  /admin/api/overview
 *   GET  /admin/api/runtime
 *   SSE  /admin/api/sse/runtime  (event: runtime)
 *   SSE  /admin/api/sse/health   (event: health)
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

    // Fetch initial data for both overview and runtime
    const [overview, runtime] = await Promise.all([
        api.get('/overview').catch(() => null),
        api.get('/runtime').catch(() => null),
    ]);

    // Build tile grid
    const grid = document.createElement('div');
    grid.className = 'wallboard-grid';

    // Health tile
    const healthTile = createTile(
        'Health',
        overview?.health?.status || 'UNKNOWN',
        '--admin-success',
    );
    healthTile.id = 'wb-health';
    grid.appendChild(healthTile);

    // Memory tile
    const memoryValue = runtime?.memory?.rss_mb != null
        ? `${runtime.memory.rss_mb.toFixed(1)} MB`
        : '--';
    const memTile = createTile('Memory', memoryValue, '--admin-primary');
    memTile.id = 'wb-memory';
    grid.appendChild(memTile);

    // Threads tile
    const threadTile = createTile(
        'Threads',
        String(runtime?.threads?.active ?? '--'),
        '--admin-info',
    );
    threadTile.id = 'wb-threads';
    grid.appendChild(threadTile);

    // Beans tile
    grid.appendChild(createTile(
        'Beans',
        String(overview?.beans?.total ?? '--'),
        '--admin-warning',
    ));

    // Uptime tile
    grid.appendChild(createTile(
        'Uptime',
        formatUptime(overview?.app?.uptime_seconds),
        '--admin-text',
    ));

    container.appendChild(grid);

    // SSE for live runtime updates (memory + threads)
    sse.connectTyped('/runtime', 'runtime', (data) => {
        const memValue = document.querySelector('#wb-memory .wallboard-tile-value');
        if (memValue && data.memory) {
            memValue.textContent = `${data.memory.rss_mb.toFixed(1)} MB`;
        }

        const threadValue = document.querySelector('#wb-threads .wallboard-tile-value');
        if (threadValue && data.threads) {
            threadValue.textContent = String(data.threads.active);
        }
    });

    // SSE for live health updates
    sse.connectTyped('/health', 'health', (data) => {
        const healthValue = document.querySelector('#wb-health .wallboard-tile-value');
        if (healthValue) {
            healthValue.textContent = data.status || 'UNKNOWN';
        }
    });

    // ESC key exits wallboard mode
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
    };
}
