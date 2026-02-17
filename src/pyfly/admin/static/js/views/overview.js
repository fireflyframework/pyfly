/**
 * PyFly Admin — Overview View (stub).
 *
 * Displays the application dashboard overview with health status,
 * stat cards, and system summary. Full implementation in Task 10.
 */

/**
 * Render the overview dashboard.
 * @param {HTMLElement} container
 * @param {import('../api.js').AdminAPI} api
 */
export async function render(container, api) {
    const wrapper = document.createElement('div');
    wrapper.className = 'view-enter';

    // Header
    const header = document.createElement('div');
    header.className = 'page-header';
    const h1 = document.createElement('h1');
    h1.textContent = 'Overview';
    header.appendChild(h1);
    wrapper.appendChild(header);

    // Placeholder
    const card = document.createElement('div');
    card.className = 'admin-card';
    const body = document.createElement('div');
    body.className = 'admin-card-body';
    const msg = document.createElement('div');
    msg.className = 'empty-state';
    const title = document.createElement('div');
    title.className = 'empty-state-title';
    title.textContent = 'Dashboard Loading';
    msg.appendChild(title);
    const text = document.createElement('div');
    text.className = 'empty-state-text';
    text.textContent = 'The overview dashboard view will be implemented in the next task.';
    msg.appendChild(text);
    body.appendChild(msg);
    card.appendChild(body);
    wrapper.appendChild(card);

    container.appendChild(wrapper);
}
