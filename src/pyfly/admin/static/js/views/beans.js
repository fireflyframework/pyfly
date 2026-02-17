/**
 * PyFly Admin — Beans View (stub).
 *
 * Displays registered application beans/components.
 * Full implementation in Task 10.
 */

export async function render(container, api) {
    const wrapper = document.createElement('div');
    wrapper.className = 'view-enter';

    const header = document.createElement('div');
    header.className = 'page-header';
    const h1 = document.createElement('h1');
    h1.textContent = 'Beans';
    const sub = document.createElement('div');
    sub.className = 'page-subtitle';
    sub.textContent = 'application.beans';
    header.appendChild(h1);
    header.appendChild(sub);
    wrapper.appendChild(header);

    const card = document.createElement('div');
    card.className = 'admin-card';
    const body = document.createElement('div');
    body.className = 'admin-card-body empty-state';
    const t = document.createElement('div');
    t.className = 'empty-state-text';
    t.textContent = 'Bean explorer will be implemented in the next task.';
    body.appendChild(t);
    card.appendChild(body);
    wrapper.appendChild(card);

    container.appendChild(wrapper);
}
