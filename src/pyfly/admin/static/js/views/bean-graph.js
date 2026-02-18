/**
 * PyFly Admin — Bean Dependency Graph View.
 *
 * D3 force-directed graph showing bean dependencies.
 * Nodes colored by stereotype, sized by resolution count.
 * Data source: GET /admin/api/beans/graph
 */

/* global d3 */

const STEREOTYPE_COLORS = {
    service:         '#3b82f6',
    controller:      '#8b5cf6',
    rest_controller: '#a78bfa',
    repository:      '#10b981',
    component:       '#f59e0b',
    configuration:   '#06b6d4',
    none:            '#64748b',
};

/**
 * Build an error/empty card using safe DOM methods only.
 */
function _buildMessageCard(title, text) {
    const card = document.createElement('div');
    card.className = 'admin-card';
    const body = document.createElement('div');
    body.className = 'admin-card-body empty-state';
    const h = document.createElement('div');
    h.className = 'empty-state-title';
    h.textContent = title;
    body.appendChild(h);
    if (text) {
        const p = document.createElement('div');
        p.className = 'empty-state-text';
        p.textContent = text;
        body.appendChild(p);
    }
    card.appendChild(body);
    return card;
}

export async function render(container, api) {
    container.replaceChildren();

    const wrapper = document.createElement('div');
    wrapper.className = 'view-enter';

    // Page header
    const header = document.createElement('div');
    header.className = 'page-header';
    const headerLeft = document.createElement('div');
    const h1 = document.createElement('h1');
    h1.textContent = 'Bean Dependency Graph';
    headerLeft.appendChild(h1);
    const sub = document.createElement('div');
    sub.className = 'page-subtitle';
    sub.textContent = 'force-directed dependency visualization';
    headerLeft.appendChild(sub);
    header.appendChild(headerLeft);
    wrapper.appendChild(header);

    // Fetch graph data
    let data;
    try {
        data = await api.get('/beans/graph');
    } catch (err) {
        wrapper.appendChild(_buildMessageCard('Failed to load graph', err.message));
        container.appendChild(wrapper);
        return;
    }

    if (!data.nodes || data.nodes.length === 0) {
        wrapper.appendChild(_buildMessageCard('No beans registered'));
        container.appendChild(wrapper);
        return;
    }

    // SVG container card
    const card = document.createElement('div');
    card.className = 'admin-card';
    const cardBody = document.createElement('div');
    cardBody.className = 'admin-card-body';
    cardBody.style.padding = '0';
    cardBody.style.overflow = 'hidden';
    card.appendChild(cardBody);
    wrapper.appendChild(card);
    container.appendChild(wrapper);

    const width = cardBody.clientWidth || 900;
    const height = 600;

    // Create SVG with D3
    const svg = d3.select(cardBody)
        .append('svg')
        .attr('width', '100%')
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`);

    // Arrow marker for directed edges
    svg.append('defs').append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 20)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#64748b');

    const g = svg.append('g');

    // Zoom/pan
    const zoom = d3.zoom()
        .scaleExtent([0.2, 4])
        .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoom);

    // Force simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.edges).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => nodeRadius(d) + 5));

    // Draw edges
    const links = g.append('g')
        .selectAll('line')
        .data(data.edges)
        .join('line')
        .attr('stroke', '#64748b')
        .attr('stroke-opacity', 0.4)
        .attr('stroke-width', 1)
        .attr('marker-end', 'url(#arrowhead)');

    // Node radius based on resolution count
    function nodeRadius(d) {
        return Math.max(6, Math.min(20, Math.sqrt((d.resolution_count || 0) + 1) * 4));
    }

    // Draw nodes
    const nodes = g.append('g')
        .selectAll('circle')
        .data(data.nodes)
        .join('circle')
        .attr('r', nodeRadius)
        .attr('fill', d => STEREOTYPE_COLORS[d.stereotype] || STEREOTYPE_COLORS.none)
        .attr('stroke', '#1e293b')
        .attr('stroke-width', 1.5)
        .call(d3.drag()
            .on('start', (event, d) => {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x; d.fy = d.y;
            })
            .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
            .on('end', (event, d) => {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null; d.fy = null;
            })
        );

    // Labels for connected nodes
    const labels = g.append('g')
        .selectAll('text')
        .data(data.nodes)
        .join('text')
        .text(d => d.name)
        .attr('font-size', '10px')
        .attr('fill', '#94a3b8')
        .attr('dx', d => nodeRadius(d) + 4)
        .attr('dy', 4);

    // Tooltip
    const tooltip = d3.select(cardBody)
        .append('div')
        .style('position', 'absolute')
        .style('background', 'var(--admin-card-bg, #1a1a2e)')
        .style('border', '1px solid var(--admin-border, #2d3748)')
        .style('border-radius', '6px')
        .style('padding', '8px 12px')
        .style('font-size', '12px')
        .style('color', 'var(--admin-text, #e2e8f0)')
        .style('pointer-events', 'none')
        .style('opacity', 0)
        .style('z-index', 10);

    nodes
        .on('mouseover', (event, d) => {
            const ttNode = tooltip.node();
            ttNode.textContent = '';

            const strong = document.createElement('strong');
            strong.textContent = d.name;
            ttNode.appendChild(strong);
            ttNode.appendChild(document.createElement('br'));

            const typeSpan = document.createElement('span');
            typeSpan.style.color = 'var(--admin-text-muted)';
            typeSpan.textContent = d.type;
            ttNode.appendChild(typeSpan);
            ttNode.appendChild(document.createElement('br'));

            ttNode.appendChild(document.createTextNode(`Stereotype: ${d.stereotype}`));
            ttNode.appendChild(document.createElement('br'));
            ttNode.appendChild(document.createTextNode(`Resolutions: ${d.resolution_count || 0}`));

            tooltip.style('opacity', 1);
        })
        .on('mousemove', (event) => {
            const rect = cardBody.getBoundingClientRect();
            tooltip
                .style('left', (event.clientX - rect.left + 12) + 'px')
                .style('top', (event.clientY - rect.top - 10) + 'px');
        })
        .on('mouseout', () => tooltip.style('opacity', 0));

    // Click to focus (zoom to node)
    nodes.on('click', (event, d) => {
        event.stopPropagation();
        const transform = d3.zoomIdentity
            .translate(width / 2, height / 2)
            .scale(2)
            .translate(-d.x, -d.y);
        svg.transition().duration(500).call(zoom.transform, transform);
    });

    // Tick
    simulation.on('tick', () => {
        links
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        nodes.attr('cx', d => d.x).attr('cy', d => d.y);
        labels.attr('x', d => d.x).attr('y', d => d.y);
    });

    // Legend
    const legendCard = document.createElement('div');
    legendCard.className = 'admin-card';
    legendCard.style.marginTop = '16px';
    const legendBody = document.createElement('div');
    legendBody.className = 'admin-card-body';
    legendBody.style.display = 'flex';
    legendBody.style.flexWrap = 'wrap';
    legendBody.style.gap = '16px';
    for (const [stereotype, color] of Object.entries(STEREOTYPE_COLORS)) {
        const item = document.createElement('div');
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.gap = '6px';
        const dot = document.createElement('div');
        dot.style.width = '12px';
        dot.style.height = '12px';
        dot.style.borderRadius = '50%';
        dot.style.background = color;
        const label = document.createElement('span');
        label.style.fontSize = '12px';
        label.style.color = 'var(--admin-text-muted)';
        label.textContent = stereotype;
        item.appendChild(dot);
        item.appendChild(label);
        legendBody.appendChild(item);
    }
    legendCard.appendChild(legendBody);
    wrapper.appendChild(legendCard);

    // Cleanup
    return function cleanup() {
        simulation.stop();
    };
}
