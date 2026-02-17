/**
 * PyFly Admin — Log Viewer.
 *
 * Displays application log output in a scrollable dark code-block
 * area with auto-scroll toggle and pause/resume controls.
 *
 * Data source:
 *   GET /admin/api/logfile -> log text (may not be available)
 */

/* ── Render ───────────────────────────────────────────────────── */

/**
 * Render the log file viewer.
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
    h1.textContent = 'Log Viewer';
    headerLeft.appendChild(h1);
    const sub = document.createElement('div');
    sub.className = 'page-subtitle';
    sub.textContent = 'application.logfile';
    headerLeft.appendChild(sub);
    header.appendChild(headerLeft);
    wrapper.appendChild(header);

    // Loading
    const loader = document.createElement('div');
    loader.className = 'loading-spinner';
    wrapper.appendChild(loader);
    container.appendChild(wrapper);

    // Fetch log data
    let logData;
    let logAvailable = true;
    try {
        logData = await api.get('/logfile');
    } catch (_err) {
        logAvailable = false;
    }

    wrapper.removeChild(loader);

    // ── Not available state ──────────────────────────────────
    if (!logAvailable || !logData) {
        const infoCard = document.createElement('div');
        infoCard.className = 'admin-card';

        const infoBody = document.createElement('div');
        infoBody.className = 'admin-card-body empty-state';

        const infoText = document.createElement('div');
        infoText.className = 'empty-state-text';
        infoText.textContent = 'Log file viewing is not configured';
        infoBody.appendChild(infoText);
        infoCard.appendChild(infoBody);
        wrapper.appendChild(infoCard);
        return;
    }

    // ── Controls card ────────────────────────────────────────
    const controlsCard = document.createElement('div');
    controlsCard.className = 'admin-card mb-lg';

    const controlsBody = document.createElement('div');
    controlsBody.className = 'admin-card-body';
    controlsBody.style.display = 'flex';
    controlsBody.style.alignItems = 'center';
    controlsBody.style.justifyContent = 'space-between';

    // Left side: auto-scroll toggle
    const leftControls = document.createElement('div');
    leftControls.style.display = 'flex';
    leftControls.style.alignItems = 'center';
    leftControls.style.gap = '8px';

    const autoScrollCheck = document.createElement('input');
    autoScrollCheck.type = 'checkbox';
    autoScrollCheck.id = 'auto-scroll-toggle';
    autoScrollCheck.checked = true;
    autoScrollCheck.style.cursor = 'pointer';

    const autoScrollLabel = document.createElement('label');
    autoScrollLabel.htmlFor = 'auto-scroll-toggle';
    autoScrollLabel.style.fontSize = '0.85rem';
    autoScrollLabel.style.cursor = 'pointer';
    autoScrollLabel.style.userSelect = 'none';
    autoScrollLabel.textContent = 'Auto-scroll';

    leftControls.appendChild(autoScrollCheck);
    leftControls.appendChild(autoScrollLabel);
    controlsBody.appendChild(leftControls);

    // Right side: pause/resume button
    const pauseBtn = document.createElement('button');
    pauseBtn.className = 'btn btn-sm';
    pauseBtn.textContent = 'Pause';
    controlsBody.appendChild(pauseBtn);

    controlsCard.appendChild(controlsBody);
    wrapper.appendChild(controlsCard);

    // ── Log area ─────────────────────────────────────────────
    const logCard = document.createElement('div');
    logCard.className = 'admin-card';

    const logHeader = document.createElement('div');
    logHeader.className = 'admin-card-header';
    const logTitle = document.createElement('h3');
    logTitle.textContent = 'Log Output';
    logHeader.appendChild(logTitle);
    logCard.appendChild(logHeader);

    const logArea = document.createElement('pre');
    logArea.className = 'code-block';
    logArea.style.maxHeight = '600px';
    logArea.style.overflowY = 'auto';
    logArea.style.margin = '0';
    logArea.style.borderRadius = '0';
    logArea.style.border = 'none';
    logArea.style.borderTop = '1px solid var(--admin-border)';

    // Populate with log content
    const logContent = typeof logData === 'string'
        ? logData
        : (logData.content || logData.lines || JSON.stringify(logData, null, 2));
    logArea.textContent = logContent;

    logCard.appendChild(logArea);
    wrapper.appendChild(logCard);

    // Scroll to bottom initially if auto-scroll is on
    if (autoScrollCheck.checked) {
        requestAnimationFrame(() => {
            logArea.scrollTop = logArea.scrollHeight;
        });
    }

    // ── Pause/Resume ─────────────────────────────────────────
    let paused = false;
    pauseBtn.addEventListener('click', () => {
        paused = !paused;
        pauseBtn.textContent = paused ? 'Resume' : 'Pause';
    });

    // Auto-scroll behaviour: when new content is added, scroll to bottom
    const observer = new MutationObserver(() => {
        if (autoScrollCheck.checked && !paused) {
            logArea.scrollTop = logArea.scrollHeight;
        }
    });
    observer.observe(logArea, { childList: true, characterData: true, subtree: true });

    // Cleanup
    return function cleanup() {
        observer.disconnect();
    };
}
