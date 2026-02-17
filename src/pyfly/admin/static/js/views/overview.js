/**
 * PyFly Admin — Overview View.
 *
 * Dashboard landing page showing health status, bean statistics,
 * stereotype breakdown chart, wiring summary, and quick-link cards.
 *
 * Data source: GET /admin/api/overview
 */

import { BarChart } from '../charts.js';
import { createStatusBadge } from '../components/status-badge.js';

/* ── Helpers ──────────────────────────────────────────────────── */

/**
 * Format a duration in seconds to a human-readable string.
 * @param {number} seconds
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
 * Create a stat card element.
 *
 * @param {object}      opts
 * @param {string}      opts.label
 * @param {string|Node} opts.value     Text or DOM node for the value area.
 * @param {string}      opts.iconClass One of: primary, success, warning, danger, info.
 * @returns {HTMLElement}
 */
function createStatCard({ label, value, iconClass = 'primary' }) {
    const card = document.createElement('div');
    card.className = 'stat-card';

    const content = document.createElement('div');
    content.className = 'stat-card-content';

    if (value instanceof Node) {
        content.appendChild(value);
    } else {
        const valEl = document.createElement('div');
        valEl.className = 'stat-card-value';
        valEl.textContent = value != null ? String(value) : '--';
        content.appendChild(valEl);
    }

    const labelEl = document.createElement('div');
    labelEl.className = 'stat-card-label';
    labelEl.textContent = label;
    content.appendChild(labelEl);

    card.appendChild(content);

    const icon = document.createElement('div');
    icon.className = `stat-card-icon ${iconClass}`;
    card.appendChild(icon);

    return card;
}

/**
 * Build a key-value table from an object.
 * @param {Object<string, string|number>} data
 * @returns {HTMLTableElement}
 */
function buildKvTable(data) {
    const table = document.createElement('table');
    table.className = 'kv-table';
    const tbody = document.createElement('tbody');
    for (const [key, val] of Object.entries(data)) {
        const tr = document.createElement('tr');
        const th = document.createElement('th');
        th.textContent = key;
        const td = document.createElement('td');
        td.textContent = val != null ? String(val) : '--';
        tr.appendChild(th);
        tr.appendChild(td);
        tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    return table;
}

/* ── Quick-link definitions ───────────────────────────────────── */

const QUICK_LINKS = [
    { label: 'Beans',   route: 'beans',   description: 'Explore registered components' },
    { label: 'Health',  route: 'health',  description: 'Service health checks' },
    { label: 'Loggers', route: 'loggers', description: 'Runtime log-level control' },
    { label: 'Metrics', route: 'metrics', description: 'Application metrics' },
];

/* ── Render ───────────────────────────────────────────────────── */

/**
 * Render the overview dashboard.
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
    const h1 = document.createElement('h1');
    h1.textContent = 'Overview';
    header.appendChild(h1);
    wrapper.appendChild(header);

    // Show loading spinner while fetching
    const loader = document.createElement('div');
    loader.className = 'loading-spinner';
    wrapper.appendChild(loader);
    container.appendChild(wrapper);

    // Fetch overview data
    let data;
    try {
        data = await api.get('/overview');
    } catch (err) {
        wrapper.removeChild(loader);
        const errCard = document.createElement('div');
        errCard.className = 'admin-card';
        const errBody = document.createElement('div');
        errBody.className = 'admin-card-body empty-state';
        const errTitle = document.createElement('div');
        errTitle.className = 'empty-state-title';
        errTitle.textContent = 'Failed to load overview';
        errBody.appendChild(errTitle);
        const errText = document.createElement('div');
        errText.className = 'empty-state-text';
        errText.textContent = err.message;
        errBody.appendChild(errText);
        errCard.appendChild(errBody);
        wrapper.appendChild(errCard);
        return;
    }

    // Remove loader
    wrapper.removeChild(loader);

    const app = data.app || {};
    const health = data.health || {};
    const beans = data.beans || {};
    const wiring = data.wiring || {};

    // ── Status cards row (grid-4) ─────────────────────────────
    const statsRow = document.createElement('div');
    statsRow.className = 'grid-4 mb-lg';

    // 1) Health status badge + label
    const healthBadge = createStatusBadge(health.status || 'UNKNOWN');
    const healthCard = createStatCard({ label: 'Health Status', value: healthBadge, iconClass: 'success' });
    statsRow.appendChild(healthCard);

    // 2) Total beans count
    const beansCard = createStatCard({
        label: 'Total Beans',
        value: String(beans.total != null ? beans.total : 0),
        iconClass: 'primary',
    });
    statsRow.appendChild(beansCard);

    // 3) Uptime
    const uptimeCard = createStatCard({
        label: 'Uptime',
        value: formatUptime(app.uptime_seconds),
        iconClass: 'info',
    });
    statsRow.appendChild(uptimeCard);

    // 4) Active profiles
    const profiles = app.profiles || [];
    const profilesCard = createStatCard({
        label: 'Active Profiles',
        value: profiles.length > 0 ? profiles.join(', ') : 'default',
        iconClass: 'warning',
    });
    statsRow.appendChild(profilesCard);

    wrapper.appendChild(statsRow);

    // ── Two-column layout: chart + wiring ─────────────────────
    const midRow = document.createElement('div');
    midRow.className = 'grid-2 mb-lg';

    // Stereotype breakdown bar chart
    const stereotypes = beans.stereotypes || {};
    const chartCard = document.createElement('div');
    chartCard.className = 'admin-card';

    const chartHeader = document.createElement('div');
    chartHeader.className = 'admin-card-header';
    const chartTitle = document.createElement('h3');
    chartTitle.textContent = 'Beans by Stereotype';
    chartHeader.appendChild(chartTitle);
    chartCard.appendChild(chartHeader);

    const chartBody = document.createElement('div');
    chartBody.className = 'admin-card-body';

    const stereotypeLabels = Object.keys(stereotypes);
    const stereotypeValues = Object.values(stereotypes);

    if (stereotypeLabels.length > 0) {
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        const canvas = document.createElement('canvas');
        chartContainer.appendChild(canvas);
        chartBody.appendChild(chartContainer);
        chartCard.appendChild(chartBody);
        midRow.appendChild(chartCard);

        // Render chart after DOM insertion so getBoundingClientRect works.
        requestAnimationFrame(() => {
            new BarChart(canvas, {
                data: stereotypeValues,
                labels: stereotypeLabels,
                height: 220,
            });
        });
    } else {
        const noData = document.createElement('div');
        noData.className = 'text-muted text-sm';
        noData.textContent = 'No stereotype data available';
        chartBody.appendChild(noData);
        chartCard.appendChild(chartBody);
        midRow.appendChild(chartCard);
    }

    // Wiring summary card
    const wiringCard = document.createElement('div');
    wiringCard.className = 'admin-card';

    const wiringHeader = document.createElement('div');
    wiringHeader.className = 'admin-card-header';
    const wiringTitle = document.createElement('h3');
    wiringTitle.textContent = 'Wiring Summary';
    wiringHeader.appendChild(wiringTitle);
    wiringCard.appendChild(wiringHeader);

    const wiringBody = document.createElement('div');
    wiringBody.className = 'admin-card-body';

    const wiringData = {
        'Event Listeners': wiring.event_listeners != null ? wiring.event_listeners : 0,
        'Scheduled Tasks': wiring.scheduled != null ? wiring.scheduled : 0,
    };
    wiringBody.appendChild(buildKvTable(wiringData));

    // Also show app meta info
    if (app.name || app.version) {
        const appSection = document.createElement('div');
        appSection.className = 'mt-lg';
        const appMeta = {};
        if (app.name) appMeta['Application'] = app.name;
        if (app.version) appMeta['Version'] = app.version;
        if (app.description) appMeta['Description'] = app.description;
        appSection.appendChild(buildKvTable(appMeta));
        wiringBody.appendChild(appSection);
    }

    wiringCard.appendChild(wiringBody);
    midRow.appendChild(wiringCard);

    wrapper.appendChild(midRow);

    // ── Quick links ───────────────────────────────────────────
    const linksSection = document.createElement('div');
    linksSection.className = 'mb-lg';

    const linksHeader = document.createElement('h3');
    linksHeader.style.marginBottom = '12px';
    linksHeader.style.fontSize = '0.95rem';
    linksHeader.style.fontWeight = '600';
    linksHeader.textContent = 'Quick Links';
    linksSection.appendChild(linksHeader);

    const linksGrid = document.createElement('div');
    linksGrid.className = 'grid-4';

    for (const link of QUICK_LINKS) {
        const card = document.createElement('div');
        card.className = 'admin-card';
        card.style.cursor = 'pointer';
        card.addEventListener('click', () => {
            window.location.hash = link.route;
        });

        const body = document.createElement('div');
        body.className = 'admin-card-body';

        const name = document.createElement('div');
        name.style.fontWeight = '600';
        name.style.marginBottom = '4px';
        name.textContent = link.label;
        body.appendChild(name);

        const desc = document.createElement('div');
        desc.className = 'text-muted text-sm';
        desc.textContent = link.description;
        body.appendChild(desc);

        card.appendChild(body);
        linksGrid.appendChild(card);
    }

    linksSection.appendChild(linksGrid);
    wrapper.appendChild(linksSection);
}
