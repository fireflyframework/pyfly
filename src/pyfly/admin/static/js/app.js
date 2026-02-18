/**
 * PyFly Admin — SPA Entry Point.
 *
 * Hash-based router that dynamically imports view modules,
 * manages the sidebar active state, persists theme preference,
 * and sets up an auto-refresh interval.
 */

import { api } from './api.js';
import { sse } from './sse.js';
import { renderSidebar, updateSidebarActive } from './components/sidebar.js';
import { showToast } from './components/toast.js';

/* ── Route Registry ───────────────────────────────────────────── */

const routes = {
    '':           () => import('./views/overview.js'),
    'beans':      () => import('./views/beans.js'),
    'health':     () => import('./views/health.js'),
    'env':        () => import('./views/environment.js'),
    'config':     () => import('./views/config.js'),
    'loggers':    () => import('./views/loggers.js'),
    'metrics':    () => import('./views/metrics.js'),
    'scheduled':  () => import('./views/scheduled.js'),
    'mappings':   () => import('./views/mappings.js'),
    'caches':     () => import('./views/caches.js'),
    'cqrs':       () => import('./views/cqrs.js'),
    'transactions': () => import('./views/transactions.js'),
    'traces':     () => import('./views/traces.js'),
    'logfile':    () => import('./views/logfile.js'),
    'instances':  () => import('./views/instances.js'),
};

/* ── Application State ────────────────────────────────────────── */

let settings = {
    title: 'PyFly Admin',
    theme: 'dark',
    refreshInterval: 10000,
    serverMode: false,
};

let currentRoute = '';
let refreshTimer = null;
let currentCleanup = null;  // Cleanup function from current view

/* ── DOM References ───────────────────────────────────────────── */

const sidebar = document.getElementById('sidebar');
const content = document.getElementById('content');
const navbar  = document.getElementById('navbar');

/* ── Theme Management ─────────────────────────────────────────── */

function getTheme() {
    return localStorage.getItem('pyfly-admin-theme') || settings.theme || 'dark';
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('pyfly-admin-theme', theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    setTheme(current === 'dark' ? 'light' : 'dark');
}

/* ── Navbar ───────────────────────────────────────────────────── */

function renderNavbar() {
    navbar.textContent = '';

    // Left: mobile toggle + title
    const left = document.createElement('div');
    left.className = 'admin-navbar-left';

    // Mobile hamburger
    const mobileToggle = document.createElement('button');
    mobileToggle.className = 'mobile-toggle';
    mobileToggle.setAttribute('aria-label', 'Toggle navigation');
    const svgNS = 'http://www.w3.org/2000/svg';
    const menuSvg = document.createElementNS(svgNS, 'svg');
    menuSvg.setAttribute('viewBox', '0 0 24 24');
    menuSvg.setAttribute('fill', 'none');
    menuSvg.setAttribute('stroke', 'currentColor');
    menuSvg.setAttribute('stroke-width', '2');
    for (const y of [4, 12, 20]) {
        const line = document.createElementNS(svgNS, 'line');
        line.setAttribute('x1', '3');
        line.setAttribute('y1', String(y));
        line.setAttribute('x2', '21');
        line.setAttribute('y2', String(y));
        menuSvg.appendChild(line);
    }
    mobileToggle.appendChild(menuSvg);
    mobileToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        mobileOverlay.classList.toggle('open');
    });
    left.appendChild(mobileToggle);

    const title = document.createElement('span');
    title.className = 'admin-navbar-title';
    title.textContent = settings.title;
    left.appendChild(title);

    navbar.appendChild(left);

    // Right: refresh label + theme toggle
    const right = document.createElement('div');
    right.className = 'admin-navbar-right';

    const refreshLabel = document.createElement('span');
    refreshLabel.className = 'refresh-label';
    refreshLabel.textContent = `refresh: ${settings.refreshInterval / 1000}s`;
    right.appendChild(refreshLabel);

    // Theme toggle button
    const themeBtn = document.createElement('button');
    themeBtn.className = 'theme-toggle';
    themeBtn.setAttribute('aria-label', 'Toggle theme');

    // Sun icon (shown in dark mode)
    const sunSvg = document.createElementNS(svgNS, 'svg');
    sunSvg.setAttribute('class', 'icon-sun');
    sunSvg.setAttribute('viewBox', '0 0 24 24');
    sunSvg.setAttribute('fill', 'none');
    sunSvg.setAttribute('stroke', 'currentColor');
    sunSvg.setAttribute('stroke-width', '2');
    sunSvg.setAttribute('stroke-linecap', 'round');
    sunSvg.setAttribute('stroke-linejoin', 'round');
    const sunPaths = [
        'M12 2a10 10 0 100 20 10 10 0 000-20z', // simplified circle
    ];
    // Sun: circle + rays
    const sunCircle = document.createElementNS(svgNS, 'circle');
    sunCircle.setAttribute('cx', '12');
    sunCircle.setAttribute('cy', '12');
    sunCircle.setAttribute('r', '5');
    sunSvg.appendChild(sunCircle);
    const rays = [
        [12, 1, 12, 3], [12, 21, 12, 23],
        [4.22, 4.22, 5.64, 5.64], [18.36, 18.36, 19.78, 19.78],
        [1, 12, 3, 12], [21, 12, 23, 12],
        [4.22, 19.78, 5.64, 18.36], [18.36, 5.64, 19.78, 4.22],
    ];
    for (const [x1, y1, x2, y2] of rays) {
        const line = document.createElementNS(svgNS, 'line');
        line.setAttribute('x1', String(x1));
        line.setAttribute('y1', String(y1));
        line.setAttribute('x2', String(x2));
        line.setAttribute('y2', String(y2));
        sunSvg.appendChild(line);
    }
    themeBtn.appendChild(sunSvg);

    // Moon icon (shown in light mode)
    const moonSvg = document.createElementNS(svgNS, 'svg');
    moonSvg.setAttribute('class', 'icon-moon');
    moonSvg.setAttribute('viewBox', '0 0 24 24');
    moonSvg.setAttribute('fill', 'none');
    moonSvg.setAttribute('stroke', 'currentColor');
    moonSvg.setAttribute('stroke-width', '2');
    moonSvg.setAttribute('stroke-linecap', 'round');
    moonSvg.setAttribute('stroke-linejoin', 'round');
    const moonPath = document.createElementNS(svgNS, 'path');
    moonPath.setAttribute('d', 'M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z');
    moonSvg.appendChild(moonPath);
    themeBtn.appendChild(moonSvg);

    themeBtn.addEventListener('click', toggleTheme);
    right.appendChild(themeBtn);

    navbar.appendChild(right);
}

/* ── Mobile Overlay ───────────────────────────────────────────── */

let mobileOverlay;

function setupMobileOverlay() {
    mobileOverlay = document.createElement('div');
    mobileOverlay.className = 'mobile-overlay';
    mobileOverlay.addEventListener('click', () => {
        sidebar.classList.remove('open');
        mobileOverlay.classList.remove('open');
    });
    document.body.appendChild(mobileOverlay);
}

/* ── Router ───────────────────────────────────────────────────── */

function getRouteFromHash() {
    const hash = window.location.hash.replace('#', '');
    return hash || '';
}

async function navigateTo(route) {
    // Cleanup previous view
    if (currentCleanup) {
        try { currentCleanup(); } catch (_) { /* ignore */ }
        currentCleanup = null;
    }

    // Disconnect SSE when navigating away
    sse.disconnectAll();

    currentRoute = route;
    window.location.hash = route;

    // Update sidebar
    updateSidebarActive(sidebar, currentRoute);

    // Close mobile sidebar
    sidebar.classList.remove('open');
    if (mobileOverlay) mobileOverlay.classList.remove('open');

    // Show loading
    content.textContent = '';
    const loader = document.createElement('div');
    loader.className = 'loading-spinner';
    content.appendChild(loader);

    // Resolve view
    const loader_ = routes[route];
    if (!loader_) {
        content.textContent = '';
        const msg = document.createElement('div');
        msg.className = 'empty-state';
        const h = document.createElement('div');
        h.className = 'empty-state-title';
        h.textContent = 'View not found';
        msg.appendChild(h);
        const p = document.createElement('div');
        p.className = 'empty-state-text';
        p.textContent = `No view registered for "${route}"`;
        msg.appendChild(p);
        content.appendChild(msg);
        return;
    }

    try {
        const mod = await loader_();
        content.textContent = '';
        content.classList.remove('view-enter');
        // Force reflow to restart animation
        void content.offsetWidth;
        content.classList.add('view-enter');

        if (mod.render) {
            const result = await mod.render(content, api);
            // Views may return a cleanup function
            if (typeof result === 'function') {
                currentCleanup = result;
            }
        }
    } catch (err) {
        console.error(`Failed to load view "${route}":`, err);
        content.textContent = '';
        const errDiv = document.createElement('div');
        errDiv.className = 'empty-state';
        const h = document.createElement('div');
        h.className = 'empty-state-title';
        h.textContent = 'Failed to load view';
        errDiv.appendChild(h);
        const p = document.createElement('div');
        p.className = 'empty-state-text';
        p.textContent = err.message;
        errDiv.appendChild(p);
        content.appendChild(errDiv);
        showToast(`Failed to load view: ${err.message}`, 'error');
    }
}

/* ── Auto-Refresh ─────────────────────────────────────────────── */

function setupAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(() => {
        // Only auto-refresh the overview view (other views use SSE or manual refresh)
        if (currentRoute === '' || currentRoute === 'overview') {
            const loader = routes[currentRoute];
            if (loader) {
                // Re-render current view silently
                // Views should handle their own refresh logic
            }
        }
    }, settings.refreshInterval);
}

/* ── Initialisation ───────────────────────────────────────────── */

async function init() {
    // Apply persisted theme
    setTheme(getTheme());

    // Setup mobile overlay
    setupMobileOverlay();

    // Fetch settings from the server
    try {
        settings = await api.get('/settings');
    } catch (err) {
        console.warn('Could not fetch admin settings, using defaults:', err.message);
    }

    // Render sidebar
    renderSidebar(sidebar, getRouteFromHash(), {
        serverMode: settings.serverMode,
        onNavigate: (route) => navigateTo(route),
    });

    // Render navbar
    renderNavbar();

    // Setup auto-refresh
    setupAutoRefresh();

    // Listen for hash changes
    window.addEventListener('hashchange', () => {
        const route = getRouteFromHash();
        if (route !== currentRoute) {
            navigateTo(route);
        }
    });

    // Navigate to initial route
    await navigateTo(getRouteFromHash());
}

// Start the application
init().catch((err) => {
    console.error('Admin dashboard failed to initialise:', err);
});
