/**
 * PyFly Admin — Caches View.
 *
 * Displays cache adapter status and provides eviction controls.
 *
 * Data sources:
 *   GET  /admin/api/caches               -> { available, type }
 *   POST /admin/api/caches/{name}/evict   -> { cleared } | { error }
 */

import { showToast } from '../components/toast.js';

/* ── Render ───────────────────────────────────────────────────── */

/**
 * Render the caches view.
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
    h1.textContent = 'Caches';
    headerLeft.appendChild(h1);
    const sub = document.createElement('div');
    sub.className = 'page-subtitle';
    sub.textContent = 'application.caches';
    headerLeft.appendChild(sub);
    header.appendChild(headerLeft);
    wrapper.appendChild(header);

    // Loading
    const loader = document.createElement('div');
    loader.className = 'loading-spinner';
    wrapper.appendChild(loader);
    container.appendChild(wrapper);

    // Fetch cache data
    let data;
    try {
        data = await api.get('/caches');
    } catch (err) {
        wrapper.removeChild(loader);
        const errCard = document.createElement('div');
        errCard.className = 'admin-card';
        const errBody = document.createElement('div');
        errBody.className = 'admin-card-body empty-state';
        const errText = document.createElement('div');
        errText.className = 'empty-state-text';
        errText.textContent = 'Failed to load cache data: ' + err.message;
        errBody.appendChild(errText);
        errCard.appendChild(errBody);
        wrapper.appendChild(errCard);
        return;
    }

    wrapper.removeChild(loader);

    // ── Cache not available ──────────────────────────────────
    if (!data.available) {
        const infoCard = document.createElement('div');
        infoCard.className = 'admin-card';

        const infoBody = document.createElement('div');
        infoBody.className = 'admin-card-body empty-state';

        const infoText = document.createElement('div');
        infoText.className = 'empty-state-text';
        infoText.textContent = 'No cache adapter is configured. Register a CacheAdapter bean to enable caching.';
        infoBody.appendChild(infoText);
        infoCard.appendChild(infoBody);
        wrapper.appendChild(infoCard);
        return;
    }

    // ── Status card ──────────────────────────────────────────
    const statusCard = document.createElement('div');
    statusCard.className = 'admin-card mb-lg';

    const statusHeader = document.createElement('div');
    statusHeader.className = 'admin-card-header';
    const statusTitle = document.createElement('h3');
    statusTitle.textContent = 'Cache Status';
    statusHeader.appendChild(statusTitle);
    statusCard.appendChild(statusHeader);

    const statusBody = document.createElement('div');
    statusBody.className = 'admin-card-body';

    const kvTable = document.createElement('table');
    kvTable.className = 'kv-table';
    const kvTbody = document.createElement('tbody');

    // Available row
    const availRow = document.createElement('tr');
    const availTh = document.createElement('th');
    availTh.textContent = 'Available';
    const availTd = document.createElement('td');
    const availBadge = document.createElement('span');
    availBadge.className = 'badge badge-success';
    const availDot = document.createElement('span');
    availDot.className = 'badge-dot';
    availBadge.appendChild(availDot);
    const availLabel = document.createElement('span');
    availLabel.textContent = 'YES';
    availBadge.appendChild(availLabel);
    availTd.appendChild(availBadge);
    availRow.appendChild(availTh);
    availRow.appendChild(availTd);
    kvTbody.appendChild(availRow);

    // Adapter type row
    const typeRow = document.createElement('tr');
    const typeTh = document.createElement('th');
    typeTh.textContent = 'Adapter Type';
    const typeTd = document.createElement('td');
    const typeSpan = document.createElement('span');
    typeSpan.className = 'text-mono';
    typeSpan.textContent = data.type || '--';
    typeTd.appendChild(typeSpan);
    typeRow.appendChild(typeTh);
    typeRow.appendChild(typeTd);
    kvTbody.appendChild(typeRow);

    kvTable.appendChild(kvTbody);
    statusBody.appendChild(kvTable);
    statusCard.appendChild(statusBody);
    wrapper.appendChild(statusCard);

    // ── Eviction card ────────────────────────────────────────
    const evictCard = document.createElement('div');
    evictCard.className = 'admin-card';

    const evictHeader = document.createElement('div');
    evictHeader.className = 'admin-card-header';
    const evictTitle = document.createElement('h3');
    evictTitle.textContent = 'Cache Management';
    evictHeader.appendChild(evictTitle);
    evictCard.appendChild(evictHeader);

    const evictBody = document.createElement('div');
    evictBody.className = 'admin-card-body';

    const evictDesc = document.createElement('p');
    evictDesc.style.marginBottom = '16px';
    evictDesc.style.fontSize = '0.85rem';
    evictDesc.style.color = 'var(--admin-text-secondary)';
    evictDesc.textContent = 'Clear all entries from the cache. This action cannot be undone.';
    evictBody.appendChild(evictDesc);

    // Button row container
    const btnRow = document.createElement('div');
    btnRow.style.display = 'flex';
    btnRow.style.alignItems = 'center';
    btnRow.style.gap = '12px';

    // Evict all button
    const evictBtn = document.createElement('button');
    evictBtn.className = 'btn btn-danger';
    evictBtn.textContent = 'Evict All';

    // Confirmation message (hidden initially)
    const confirmWrap = document.createElement('span');
    confirmWrap.style.display = 'none';
    confirmWrap.style.alignItems = 'center';
    confirmWrap.style.gap = '8px';

    const confirmText = document.createElement('span');
    confirmText.style.fontSize = '0.85rem';
    confirmText.style.color = 'var(--admin-warning)';
    confirmText.style.fontWeight = '500';
    confirmText.textContent = 'Are you sure?';

    const confirmYes = document.createElement('button');
    confirmYes.className = 'btn btn-danger btn-sm';
    confirmYes.textContent = 'Yes, clear';

    const confirmNo = document.createElement('button');
    confirmNo.className = 'btn btn-sm';
    confirmNo.textContent = 'Cancel';

    confirmWrap.appendChild(confirmText);
    confirmWrap.appendChild(confirmYes);
    confirmWrap.appendChild(confirmNo);

    // Show confirmation on click
    evictBtn.addEventListener('click', () => {
        evictBtn.style.display = 'none';
        confirmWrap.style.display = 'flex';
    });

    // Cancel
    confirmNo.addEventListener('click', () => {
        confirmWrap.style.display = 'none';
        evictBtn.style.display = '';
    });

    // Confirm eviction
    confirmYes.addEventListener('click', async () => {
        confirmYes.disabled = true;
        confirmYes.textContent = 'Clearing...';
        try {
            await api.post('/caches/default/evict', {});
            showToast('Cache cleared successfully', 'success');
        } catch (err) {
            showToast('Failed to clear cache: ' + err.message, 'error');
        } finally {
            confirmWrap.style.display = 'none';
            evictBtn.style.display = '';
            confirmYes.disabled = false;
            confirmYes.textContent = 'Yes, clear';
        }
    });

    btnRow.appendChild(evictBtn);
    btnRow.appendChild(confirmWrap);
    evictBody.appendChild(btnRow);
    evictCard.appendChild(evictBody);
    wrapper.appendChild(evictCard);
}
