/**
 * PyFly Admin — Beans View.
 *
 * Filterable, sortable bean explorer with a slide-in detail panel.
 * Uses the reusable table component with custom cell renderers
 * for stereotype badges and scope labels.
 *
 * Data sources:
 *   GET /admin/api/beans          -> { beans: [...], total: N }
 *   GET /admin/api/beans/{name}   -> bean detail object
 */

import { createTable } from '../components/table.js';

/* ── Helpers ──────────────────────────────────────────────────── */

/** Map stereotype names to badge CSS classes. */
const STEREOTYPE_CLASSES = {
    service:      'badge-info',
    repository:   'badge-success',
    controller:   'badge-get',
    component:    'badge-neutral',
    configuration:'badge-warning',
    filter:       'badge-patch',
};

/**
 * Create a small coloured badge for a stereotype value.
 * @param {string} stereotype
 * @returns {HTMLSpanElement}
 */
function createStereotypeBadge(stereotype) {
    const badge = document.createElement('span');
    const norm = (stereotype || '').toLowerCase();
    const cls = STEREOTYPE_CLASSES[norm] || 'badge-neutral';
    badge.className = `badge ${cls}`;
    badge.textContent = stereotype || '--';
    return badge;
}

/**
 * Truncate a module path, keeping the last two segments.
 * e.g. "myapp.services.user_service.UserService" -> "...user_service.UserService"
 * @param {string} typePath
 * @returns {string}
 */
function truncateType(typePath) {
    if (!typePath) return '--';
    const parts = typePath.split('.');
    if (parts.length <= 2) return typePath;
    return '...' + parts.slice(-2).join('.');
}

/**
 * Create a checkmark or X icon element.
 * @param {boolean} yes
 * @returns {HTMLSpanElement}
 */
function createCheckIcon(yes) {
    const span = document.createElement('span');
    span.style.fontWeight = '600';
    if (yes) {
        span.textContent = '\u2713';
        span.style.color = 'var(--admin-success)';
    } else {
        span.textContent = '\u2717';
        span.style.color = 'var(--admin-danger)';
    }
    return span;
}

/**
 * Build a key-value table from an object, skipping null/undefined entries.
 * @param {Object<string, *>} data
 * @returns {HTMLTableElement}
 */
function buildKvTable(data) {
    const table = document.createElement('table');
    table.className = 'kv-table';
    const tbody = document.createElement('tbody');
    for (const [key, val] of Object.entries(data)) {
        if (val == null) continue;
        const tr = document.createElement('tr');
        const th = document.createElement('th');
        th.textContent = key;
        const td = document.createElement('td');
        if (val instanceof Node) {
            td.appendChild(val);
        } else if (Array.isArray(val)) {
            td.textContent = val.length > 0 ? val.join(', ') : '--';
        } else {
            td.textContent = String(val);
        }
        tr.appendChild(th);
        tr.appendChild(td);
        tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    return table;
}

/* ── Detail Panel ─────────────────────────────────────────────── */

/**
 * Create the detail panel overlay + panel structure (initially hidden).
 * Returns { overlay, panel, show(beanDetail), hide() }.
 */
function createDetailPanel() {
    // Overlay
    const overlay = document.createElement('div');
    overlay.className = 'detail-panel-overlay';

    // Panel
    const panel = document.createElement('div');
    panel.className = 'detail-panel';

    // Header
    const panelHeader = document.createElement('div');
    panelHeader.className = 'detail-panel-header';
    const panelTitle = document.createElement('h3');
    panelTitle.textContent = 'Bean Detail';
    panelHeader.appendChild(panelTitle);

    const closeBtn = document.createElement('button');
    closeBtn.className = 'detail-panel-close';
    closeBtn.setAttribute('aria-label', 'Close detail panel');
    // X icon via SVG
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    const line1 = document.createElementNS(svgNS, 'line');
    line1.setAttribute('x1', '18');
    line1.setAttribute('y1', '6');
    line1.setAttribute('x2', '6');
    line1.setAttribute('y2', '18');
    svg.appendChild(line1);
    const line2 = document.createElementNS(svgNS, 'line');
    line2.setAttribute('x1', '6');
    line2.setAttribute('y1', '6');
    line2.setAttribute('x2', '18');
    line2.setAttribute('y2', '18');
    svg.appendChild(line2);
    closeBtn.appendChild(svg);
    panelHeader.appendChild(closeBtn);
    panel.appendChild(panelHeader);

    // Body
    const panelBody = document.createElement('div');
    panelBody.className = 'detail-panel-body';
    panel.appendChild(panelBody);

    // Close handlers
    function hide() {
        overlay.classList.remove('open');
        panel.classList.remove('open');
    }

    closeBtn.addEventListener('click', hide);
    overlay.addEventListener('click', hide);

    /**
     * Populate and show the panel with bean detail data.
     * @param {object} bean
     */
    function show(bean) {
        panelBody.replaceChildren();
        panelTitle.textContent = bean.name || 'Bean Detail';

        // Basic info
        const basicSection = document.createElement('div');
        basicSection.className = 'mb-lg';
        const basicHeader = document.createElement('h4');
        basicHeader.textContent = 'Basic Information';
        basicHeader.style.marginBottom = '8px';
        basicHeader.style.fontSize = '0.85rem';
        basicHeader.style.fontWeight = '600';
        basicSection.appendChild(basicHeader);

        const basicData = {
            'Name': bean.name,
            'Type': bean.type,
            'Module': bean.module,
            'File': bean.file_path || bean.file,
            'Scope': bean.scope,
            'Stereotype': bean.stereotype ? createStereotypeBadge(bean.stereotype) : null,
            'Initialized': bean.initialized != null ? (bean.initialized ? 'Yes' : 'No') : null,
        };
        basicSection.appendChild(buildKvTable(basicData));
        panelBody.appendChild(basicSection);

        // Docstring
        if (bean.docstring) {
            const docSection = document.createElement('div');
            docSection.className = 'mb-lg';
            const docHeader = document.createElement('h4');
            docHeader.textContent = 'Documentation';
            docHeader.style.marginBottom = '8px';
            docHeader.style.fontSize = '0.85rem';
            docHeader.style.fontWeight = '600';
            docSection.appendChild(docHeader);
            const docBlock = document.createElement('div');
            docBlock.className = 'code-block';
            docBlock.textContent = bean.docstring;
            docSection.appendChild(docBlock);
            panelBody.appendChild(docSection);
        }

        // Dependencies
        const deps = bean.dependencies || [];
        if (deps.length > 0) {
            const depSection = document.createElement('div');
            depSection.className = 'mb-lg';
            const depHeader = document.createElement('h4');
            depHeader.textContent = 'Dependencies';
            depHeader.style.marginBottom = '8px';
            depHeader.style.fontSize = '0.85rem';
            depHeader.style.fontWeight = '600';
            depSection.appendChild(depHeader);
            const depList = document.createElement('div');
            depList.className = 'flex flex-col gap-sm';
            for (const dep of deps) {
                const depItem = document.createElement('div');
                depItem.className = 'text-mono text-sm';
                depItem.style.padding = '6px 10px';
                depItem.style.background = 'var(--admin-bg)';
                depItem.style.borderRadius = 'var(--admin-radius-sm)';
                depItem.style.border = '1px solid var(--admin-border-subtle)';
                depItem.textContent = typeof dep === 'string' ? dep : (dep.name || String(dep));
                depList.appendChild(depItem);
            }
            depSection.appendChild(depList);
            panelBody.appendChild(depSection);
        }

        // Metadata (primary, order, profile, conditions)
        const meta = {};
        if (bean.primary != null) meta['Primary'] = String(bean.primary);
        if (bean.order != null) meta['Order'] = String(bean.order);
        if (bean.profile) meta['Profile'] = Array.isArray(bean.profile) ? bean.profile.join(', ') : bean.profile;
        if (bean.conditions) meta['Conditions'] = Array.isArray(bean.conditions) ? bean.conditions.join(', ') : bean.conditions;

        if (Object.keys(meta).length > 0) {
            const metaSection = document.createElement('div');
            metaSection.className = 'mb-lg';
            const metaHeader = document.createElement('h4');
            metaHeader.textContent = 'Metadata';
            metaHeader.style.marginBottom = '8px';
            metaHeader.style.fontSize = '0.85rem';
            metaHeader.style.fontWeight = '600';
            metaSection.appendChild(metaHeader);
            metaSection.appendChild(buildKvTable(meta));
            panelBody.appendChild(metaSection);
        }

        // Show panel
        overlay.classList.add('open');
        panel.classList.add('open');
    }

    return { overlay, panel, show, hide };
}

/* ── Render ───────────────────────────────────────────────────── */

/**
 * Render the beans explorer view.
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
    h1.textContent = 'Beans';
    headerLeft.appendChild(h1);
    const sub = document.createElement('div');
    sub.className = 'page-subtitle';
    sub.textContent = 'application.beans';
    headerLeft.appendChild(sub);
    header.appendChild(headerLeft);
    wrapper.appendChild(header);

    // Loading
    const loader = document.createElement('div');
    loader.className = 'loading-spinner';
    wrapper.appendChild(loader);
    container.appendChild(wrapper);

    // Fetch beans
    let data;
    try {
        data = await api.get('/beans');
    } catch (err) {
        wrapper.removeChild(loader);
        const errCard = document.createElement('div');
        errCard.className = 'admin-card';
        const errBody = document.createElement('div');
        errBody.className = 'admin-card-body empty-state';
        const errText = document.createElement('div');
        errText.className = 'empty-state-text';
        errText.textContent = 'Failed to load beans: ' + err.message;
        errBody.appendChild(errText);
        errCard.appendChild(errBody);
        wrapper.appendChild(errCard);
        return;
    }

    wrapper.removeChild(loader);

    const beansList = data.beans || [];
    const total = data.total != null ? data.total : beansList.length;

    // ── Stat cards row ────────────────────────────────────────
    const statsRow = document.createElement('div');
    statsRow.className = 'grid-4 mb-lg';

    // Total beans
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
    totalLabel.textContent = 'Total Beans';
    totalContent.appendChild(totalLabel);
    totalCard.appendChild(totalContent);
    statsRow.appendChild(totalCard);

    // Stereotype breakdown mini badges
    const stereotypeCounts = {};
    for (const bean of beansList) {
        const st = bean.stereotype || 'other';
        stereotypeCounts[st] = (stereotypeCounts[st] || 0) + 1;
    }

    // Show up to 3 top stereotypes as stat cards
    const sortedStereotypes = Object.entries(stereotypeCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3);

    const iconClasses = ['primary', 'info', 'success'];
    for (let i = 0; i < sortedStereotypes.length; i++) {
        const [stereo, count] = sortedStereotypes[i];
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
        cardLabel.textContent = stereo;
        cardContent.appendChild(cardLabel);
        card.appendChild(cardContent);
        const cardIcon = document.createElement('div');
        cardIcon.className = `stat-card-icon ${iconClasses[i] || 'primary'}`;
        card.appendChild(cardIcon);
        statsRow.appendChild(card);
    }

    wrapper.appendChild(statsRow);

    // ── Detail panel ──────────────────────────────────────────
    const detailPanel = createDetailPanel();
    document.body.appendChild(detailPanel.overlay);
    document.body.appendChild(detailPanel.panel);

    // ── Table ─────────────────────────────────────────────────
    const tableCard = document.createElement('div');
    tableCard.className = 'admin-card';

    const tableHeader = document.createElement('div');
    tableHeader.className = 'admin-card-header';
    const tableTitle = document.createElement('h3');
    tableTitle.textContent = 'Registered Beans';
    tableHeader.appendChild(tableTitle);
    tableCard.appendChild(tableHeader);

    const tableBody = document.createElement('div');
    tableBody.className = 'admin-card-body';
    tableBody.style.padding = '0';

    const tableEl = createTable({
        columns: [
            {
                key: 'name',
                label: 'Name',
                render(val) {
                    const span = document.createElement('span');
                    span.className = 'mono';
                    span.textContent = val || '--';
                    return span;
                },
            },
            {
                key: 'type',
                label: 'Type',
                render(val) {
                    const span = document.createElement('span');
                    span.className = 'mono truncate';
                    span.style.maxWidth = '240px';
                    span.style.display = 'inline-block';
                    span.title = val || '';
                    span.textContent = truncateType(val);
                    return span;
                },
            },
            {
                key: 'scope',
                label: 'Scope',
                render(val) {
                    const span = document.createElement('span');
                    span.className = 'badge badge-neutral';
                    span.textContent = val || 'singleton';
                    return span;
                },
            },
            {
                key: 'stereotype',
                label: 'Stereotype',
                render(val) {
                    return createStereotypeBadge(val);
                },
            },
            {
                key: 'initialized',
                label: 'Initialized',
                render(val) {
                    return createCheckIcon(!!val);
                },
            },
        ],
        data: beansList,
        searchable: true,
        sortable: true,
        emptyText: 'No beans found',
        onRowClick: async (row) => {
            // Fetch full detail for this bean
            try {
                const detail = await api.get(`/beans/${encodeURIComponent(row.name)}`);
                detailPanel.show(detail);
            } catch (_err) {
                // Fall back to the row data we already have
                detailPanel.show(row);
            }
        },
    });

    tableBody.appendChild(tableEl);
    tableCard.appendChild(tableBody);
    wrapper.appendChild(tableCard);

    // Cleanup: remove detail panel elements from body on navigation
    return function cleanup() {
        detailPanel.hide();
        if (detailPanel.overlay.parentNode) {
            detailPanel.overlay.parentNode.removeChild(detailPanel.overlay);
        }
        if (detailPanel.panel.parentNode) {
            detailPanel.panel.parentNode.removeChild(detailPanel.panel);
        }
    };
}
