/**
 * PyFly Admin — Reusable Filter Toolbar Component.
 *
 * Provides a consistent search + filter pill bar used across views
 * (metrics, loggers, config, environment).
 */

/**
 * Create a search icon SVG.
 * @returns {SVGElement}
 */
function createSearchIcon() {
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
    return svg;
}

/**
 * Create a filter toolbar element.
 *
 * @param {object}   config
 * @param {string}   [config.placeholder]  Search input placeholder.
 * @param {Array<{label: string, value: string}>} [config.pills]  Filter pill options.
 * @param {function} [config.onFilter]     Called with { search, pill } on each change.
 * @param {number}   [config.totalCount]   Initial total item count.
 * @returns {HTMLElement}  The toolbar element with .updateCount(count, total) and .getState().
 */
export function createFilterToolbar(config = {}) {
    const {
        placeholder = 'Search\u2026',
        pills = [],
        onFilter = () => {},
        totalCount = 0,
    } = config;

    let currentSearch = '';
    let currentPill = pills.length > 0 ? pills[0].value : '';

    const toolbar = document.createElement('div');
    toolbar.className = 'filter-toolbar';

    // ── Left: search input ──────────────────────────────────────
    const left = document.createElement('div');
    left.className = 'filter-toolbar-search';

    const searchWrap = document.createElement('div');
    searchWrap.className = 'search-input';
    searchWrap.appendChild(createSearchIcon());

    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'input';
    input.placeholder = placeholder;
    searchWrap.appendChild(input);
    left.appendChild(searchWrap);
    toolbar.appendChild(left);

    // ── Right: pills + count ────────────────────────────────────
    const right = document.createElement('div');
    right.className = 'filter-toolbar-actions';

    const pillButtons = [];
    if (pills.length > 0) {
        const pillsWrap = document.createElement('div');
        pillsWrap.className = 'filter-pills';

        for (const pill of pills) {
            const btn = document.createElement('button');
            btn.className = 'filter-pill';
            btn.textContent = pill.label;
            if (pill.value === currentPill) {
                btn.classList.add('active');
            }
            btn.addEventListener('click', () => {
                currentPill = pill.value;
                pillButtons.forEach((b) => b.classList.remove('active'));
                btn.classList.add('active');
                onFilter({ search: currentSearch, pill: currentPill });
            });
            pillButtons.push(btn);
            pillsWrap.appendChild(btn);
        }
        right.appendChild(pillsWrap);
    }

    const countEl = document.createElement('span');
    countEl.className = 'filter-count';
    countEl.textContent = totalCount > 0 ? `${totalCount} results` : '';
    right.appendChild(countEl);

    toolbar.appendChild(right);

    // Wire search input
    input.addEventListener('input', () => {
        currentSearch = input.value.toLowerCase();
        onFilter({ search: currentSearch, pill: currentPill });
    });

    // ── Public API ──────────────────────────────────────────────

    /** Update the displayed result count. */
    toolbar.updateCount = (count, total) => {
        if (total != null && count !== total) {
            countEl.textContent = `${count} of ${total}`;
        } else {
            countEl.textContent = `${count != null ? count : totalCount} results`;
        }
    };

    /** Get current filter state. */
    toolbar.getState = () => ({ search: currentSearch, pill: currentPill });

    return toolbar;
}
