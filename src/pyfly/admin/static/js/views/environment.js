/**
 * PyFly Admin — Environment View.
 *
 * Displays active profiles, config sources, and a searchable
 * properties table with type-aware value styling.
 *
 * Data source:  GET /admin/api/env
 *   -> { active_profiles: [...], properties: {...}, sources: [...] }
 */

import { createTable } from '../components/table.js';

/* ── Helpers ──────────────────────────────────────────────────── */

/**
 * Determine the visual type of a property value for styling purposes.
 * @param {*} val
 * @returns {"boolean"|"number"|"string"}
 */
function valueType(val) {
    if (val === true || val === false || val === 'true' || val === 'false') {
        return 'boolean';
    }
    if (typeof val === 'number' || (typeof val === 'string' && val !== '' && !isNaN(Number(val)))) {
        return 'number';
    }
    return 'string';
}

/**
 * Create a styled value element based on its detected type.
 * @param {*} val
 * @returns {HTMLSpanElement}
 */
function renderValue(val) {
    const span = document.createElement('span');
    const type = valueType(val);
    const text = val != null ? String(val) : '';

    span.textContent = text;
    span.className = 'mono';
    span.style.fontSize = '0.8rem';

    if (type === 'boolean') {
        span.style.color = 'var(--admin-warning)';
        span.style.fontWeight = '600';
    } else if (type === 'number') {
        span.style.color = 'var(--admin-info)';
        span.style.fontWeight = '600';
    } else {
        span.style.color = 'var(--admin-text)';
    }

    return span;
}

/**
 * Flatten a nested properties object into dot-notation key/value pairs.
 * @param {object} obj
 * @param {string} prefix
 * @returns {Array<{key: string, value: *}>}
 */
function flattenProperties(obj, prefix = '') {
    const entries = [];
    for (const [k, v] of Object.entries(obj)) {
        const fullKey = prefix ? `${prefix}.${k}` : k;
        if (v != null && typeof v === 'object' && !Array.isArray(v)) {
            entries.push(...flattenProperties(v, fullKey));
        } else {
            entries.push({ key: fullKey, value: v });
        }
    }
    return entries;
}

/* ── Render ───────────────────────────────────────────────────── */

/**
 * Render the environment view.
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
    h1.textContent = 'Environment';
    headerLeft.appendChild(h1);
    const sub = document.createElement('div');
    sub.className = 'page-subtitle';
    sub.textContent = 'application.env';
    headerLeft.appendChild(sub);
    header.appendChild(headerLeft);
    wrapper.appendChild(header);

    // Loading
    const loader = document.createElement('div');
    loader.className = 'loading-spinner';
    wrapper.appendChild(loader);
    container.appendChild(wrapper);

    // Fetch environment data
    let envData;
    try {
        envData = await api.get('/env');
    } catch (err) {
        wrapper.removeChild(loader);
        const errCard = document.createElement('div');
        errCard.className = 'admin-card';
        const errBody = document.createElement('div');
        errBody.className = 'admin-card-body empty-state';
        const errText = document.createElement('div');
        errText.className = 'empty-state-text';
        errText.textContent = 'Failed to load environment data: ' + err.message;
        errBody.appendChild(errText);
        errCard.appendChild(errBody);
        wrapper.appendChild(errCard);
        return;
    }

    wrapper.removeChild(loader);

    const activeProfiles = envData.active_profiles || [];
    const properties = envData.properties || {};
    const sources = envData.sources || [];

    // ── Active Profiles card ─────────────────────────────────
    const profileCard = document.createElement('div');
    profileCard.className = 'admin-card mb-lg';

    const profileHeader = document.createElement('div');
    profileHeader.className = 'admin-card-header';
    const profileTitle = document.createElement('h3');
    profileTitle.textContent = 'Active Profiles';
    profileHeader.appendChild(profileTitle);
    profileCard.appendChild(profileHeader);

    const profileBody = document.createElement('div');
    profileBody.className = 'admin-card-body';
    profileBody.style.display = 'flex';
    profileBody.style.alignItems = 'center';
    profileBody.style.gap = '8px';
    profileBody.style.flexWrap = 'wrap';

    if (activeProfiles.length === 0) {
        const noneEl = document.createElement('span');
        noneEl.className = 'text-muted text-sm';
        noneEl.textContent = 'No active profiles';
        profileBody.appendChild(noneEl);
    } else {
        const PROFILE_BADGE_CLASSES = ['badge-info', 'badge-success', 'badge-warning', 'badge-get', 'badge-patch'];
        for (let i = 0; i < activeProfiles.length; i++) {
            const badge = document.createElement('span');
            badge.className = 'badge ' + PROFILE_BADGE_CLASSES[i % PROFILE_BADGE_CLASSES.length];
            const dot = document.createElement('span');
            dot.className = 'badge-dot';
            badge.appendChild(dot);
            const text = document.createTextNode(activeProfiles[i]);
            badge.appendChild(text);
            profileBody.appendChild(badge);
        }
    }

    profileCard.appendChild(profileBody);
    wrapper.appendChild(profileCard);

    // ── Config Sources card ──────────────────────────────────
    if (sources.length > 0) {
        const sourcesCard = document.createElement('div');
        sourcesCard.className = 'admin-card mb-lg';

        const sourcesHeader = document.createElement('div');
        sourcesHeader.className = 'admin-card-header';
        const sourcesTitle = document.createElement('h3');
        sourcesTitle.textContent = 'Config Sources';
        const sourcesCount = document.createElement('span');
        sourcesCount.className = 'card-subtitle';
        sourcesCount.textContent = sources.length + ' loaded';
        sourcesHeader.appendChild(sourcesTitle);
        sourcesHeader.appendChild(sourcesCount);
        sourcesCard.appendChild(sourcesHeader);

        const sourcesBody = document.createElement('div');
        sourcesBody.className = 'admin-card-body';
        sourcesBody.style.padding = '0';

        const sourcesList = document.createElement('div');
        for (let i = 0; i < sources.length; i++) {
            const src = sources[i];
            const item = document.createElement('div');
            item.style.padding = '10px 20px';
            item.style.display = 'flex';
            item.style.alignItems = 'center';
            item.style.gap = '12px';
            if (i < sources.length - 1) {
                item.style.borderBottom = '1px solid var(--admin-border-subtle)';
            }

            const idx = document.createElement('span');
            idx.className = 'text-mono text-xs text-muted';
            idx.textContent = '#' + (i + 1);
            idx.style.minWidth = '28px';
            item.appendChild(idx);

            const name = document.createElement('span');
            name.className = 'text-mono text-sm';
            name.textContent = typeof src === 'string' ? src : (src.name || JSON.stringify(src));
            item.appendChild(name);

            sourcesList.appendChild(item);
        }

        sourcesBody.appendChild(sourcesList);
        sourcesCard.appendChild(sourcesBody);
        wrapper.appendChild(sourcesCard);
    }

    // ── Properties table ─────────────────────────────────────
    const propsFlat = flattenProperties(properties);

    const propsCard = document.createElement('div');
    propsCard.className = 'admin-card';

    const propsHeader = document.createElement('div');
    propsHeader.className = 'admin-card-header';
    const propsTitle = document.createElement('h3');
    propsTitle.textContent = 'Properties';
    const propsCount = document.createElement('span');
    propsCount.className = 'card-subtitle';
    propsCount.textContent = propsFlat.length + ' properties';
    propsHeader.appendChild(propsTitle);
    propsHeader.appendChild(propsCount);
    propsCard.appendChild(propsHeader);

    const propsBody = document.createElement('div');
    propsBody.className = 'admin-card-body';
    propsBody.style.padding = '0';

    const tableEl = createTable({
        columns: [
            {
                key: 'key',
                label: 'Key',
                render(val) {
                    const span = document.createElement('span');
                    span.className = 'mono';
                    span.textContent = val || '';
                    return span;
                },
            },
            {
                key: 'value',
                label: 'Value',
                render(val) {
                    return renderValue(val);
                },
            },
        ],
        data: propsFlat,
        searchable: true,
        sortable: true,
        emptyText: 'No properties found',
    });

    propsBody.appendChild(tableEl);
    propsCard.appendChild(propsBody);
    wrapper.appendChild(propsCard);
}
