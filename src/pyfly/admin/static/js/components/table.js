/**
 * PyFly Admin — Reusable Table Component.
 *
 * Creates sortable, searchable, clickable tables using safe DOM construction.
 */

/**
 * Create a fully-featured data table.
 *
 * @param {object}   config
 * @param {Array<{key: string, label: string, render?: function, sortable?: boolean}>} config.columns
 * @param {object[]} config.data         Array of row objects.
 * @param {function} [config.onRowClick] Callback(rowData) when a row is clicked.
 * @param {boolean}  [config.searchable] Add a filter input above the table.
 * @param {boolean}  [config.sortable]   Enable column-header sort on click.
 * @param {string}   [config.emptyText]  Text shown when there is no data.
 * @returns {HTMLElement}  The wrapper element containing the table.
 */
export function createTable(config) {
    const {
        columns = [],
        data = [],
        onRowClick = null,
        searchable = false,
        sortable = false,
        emptyText = 'No data available',
    } = config;

    // State
    let displayData = [...data];
    let sortKey = null;
    let sortDir = 'asc';
    let filterText = '';

    // Root wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'admin-table-component';

    // Search input
    let searchInput = null;
    if (searchable) {
        const searchWrap = document.createElement('div');
        searchWrap.className = 'search-input';
        searchWrap.style.marginBottom = '12px';

        // Search icon SVG
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
        searchWrap.appendChild(svg);

        searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'input';
        searchInput.placeholder = 'Filter rows\u2026';
        searchInput.addEventListener('input', () => {
            filterText = searchInput.value.toLowerCase();
            applyFilterAndSort();
            renderBody();
        });
        searchWrap.appendChild(searchInput);
        wrapper.appendChild(searchWrap);
    }

    // Table wrapper (for overflow)
    const tableWrap = document.createElement('div');
    tableWrap.className = 'admin-table-wrapper';

    const table = document.createElement('table');
    table.className = 'admin-table';

    // ── Head ──
    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');

    for (const col of columns) {
        const th = document.createElement('th');
        th.textContent = col.label;

        if (sortable && col.sortable !== false) {
            th.classList.add('sortable');
            th.addEventListener('click', () => {
                if (sortKey === col.key) {
                    sortDir = sortDir === 'asc' ? 'desc' : 'asc';
                } else {
                    sortKey = col.key;
                    sortDir = 'asc';
                }
                updateSortIndicators();
                applyFilterAndSort();
                renderBody();
            });
        }

        th.dataset.key = col.key;
        headRow.appendChild(th);
    }
    thead.appendChild(headRow);
    table.appendChild(thead);

    // ── Body ──
    const tbody = document.createElement('tbody');
    table.appendChild(tbody);

    tableWrap.appendChild(table);
    wrapper.appendChild(tableWrap);

    // ── Functions ──

    function applyFilterAndSort() {
        displayData = [...data];

        // Filter
        if (filterText) {
            displayData = displayData.filter((row) =>
                columns.some((col) => {
                    const val = row[col.key];
                    if (val == null) return false;
                    return String(val).toLowerCase().includes(filterText);
                })
            );
        }

        // Sort
        if (sortKey) {
            displayData.sort((a, b) => {
                let va = a[sortKey];
                let vb = b[sortKey];
                if (va == null) va = '';
                if (vb == null) vb = '';
                if (typeof va === 'number' && typeof vb === 'number') {
                    return sortDir === 'asc' ? va - vb : vb - va;
                }
                const sa = String(va).toLowerCase();
                const sb = String(vb).toLowerCase();
                const cmp = sa < sb ? -1 : sa > sb ? 1 : 0;
                return sortDir === 'asc' ? cmp : -cmp;
            });
        }
    }

    function updateSortIndicators() {
        const ths = headRow.querySelectorAll('th');
        for (const th of ths) {
            th.classList.remove('sort-asc', 'sort-desc');
            if (th.dataset.key === sortKey) {
                th.classList.add(sortDir === 'asc' ? 'sort-asc' : 'sort-desc');
            }
        }
    }

    function renderBody() {
        tbody.textContent = '';

        if (displayData.length === 0) {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = columns.length;
            td.style.textAlign = 'center';
            td.style.padding = '32px 16px';
            td.style.color = 'var(--admin-text-muted)';
            td.textContent = emptyText;
            tr.appendChild(td);
            tbody.appendChild(tr);
            return;
        }

        for (const row of displayData) {
            const tr = document.createElement('tr');

            if (onRowClick) {
                tr.classList.add('clickable');
                tr.addEventListener('click', () => onRowClick(row));
            }

            for (const col of columns) {
                const td = document.createElement('td');

                if (col.render) {
                    // Custom render function returns a DOM element or string
                    const rendered = col.render(row[col.key], row);
                    if (typeof rendered === 'string') {
                        td.textContent = rendered;
                    } else if (rendered instanceof Node) {
                        td.appendChild(rendered);
                    } else {
                        td.textContent = rendered != null ? String(rendered) : '';
                    }
                } else {
                    const val = row[col.key];
                    td.textContent = val != null ? String(val) : '';
                }

                tr.appendChild(td);
            }

            tbody.appendChild(tr);
        }
    }

    // Initial render
    applyFilterAndSort();
    renderBody();

    /**
     * Allow external code to update the table data.
     * @param {object[]} newData
     */
    wrapper.updateData = (newData) => {
        data.length = 0;
        data.push(...newData);
        applyFilterAndSort();
        renderBody();
    };

    return wrapper;
}
