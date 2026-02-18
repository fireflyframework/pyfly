/**
 * PyFly Admin — Lightweight Canvas Chart Library.
 *
 * Three chart types for the dashboard:
 *   - LineChart   — time-series with smooth curves and gradient fill
 *   - BarChart    — vertical bars with labels and value display
 *   - GaugeChart  — circular gauge with percentage and colour thresholds
 *
 * All colours are read from CSS custom properties so they match the
 * active theme automatically.
 */

/* ── Helpers ──────────────────────────────────────────────────── */

function cssVar(name) {
    return getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim();
}

function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Prepare a canvas for high-DPI rendering and return its 2D context.
 */
function setupCanvas(canvas, width, height) {
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    return ctx;
}

function niceMax(value) {
    if (value <= 0) return 10;
    const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
    const residual = value / magnitude;
    if (residual <= 1) return magnitude;
    if (residual <= 2) return 2 * magnitude;
    if (residual <= 5) return 5 * magnitude;
    return 10 * magnitude;
}

/* ── LineChart ────────────────────────────────────────────────── */

export class LineChart {
    /**
     * @param {HTMLCanvasElement} canvas
     * @param {object} options
     * @param {number[]} options.data        Y-values
     * @param {string[]} [options.labels]    X-axis labels
     * @param {string}  [options.color]      Override line colour (CSS var name)
     * @param {string}  [options.label]      Dataset label
     * @param {boolean} [options.fill]       Show gradient fill (default true)
     * @param {number}  [options.height]     Canvas logical height (default 200)
     */
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = Object.assign({
            data: [],
            labels: [],
            color: '--admin-primary',
            label: '',
            fill: true,
            height: 200,
        }, options);
        this.draw();
    }

    update(data, labels) {
        this.options.data = data;
        if (labels) this.options.labels = labels;
        this.draw();
    }

    draw() {
        const { data, labels, color, fill, height } = this.options;
        if (!data.length) return;

        const rect = this.canvas.parentElement
            ? this.canvas.parentElement.getBoundingClientRect()
            : { width: 600 };
        const width = Math.max(rect.width, 200);
        const ctx = setupCanvas(this.canvas, width, height);

        const lineColor = cssVar(color) || cssVar('--admin-primary');
        const textColor = cssVar('--admin-text-muted') || '#64748b';
        const gridColor = cssVar('--admin-border-subtle') || '#162032';

        const pad = { top: 24, right: 16, bottom: 32, left: 52 };
        const plotW = width - pad.left - pad.right;
        const plotH = height - pad.top - pad.bottom;

        const maxVal = niceMax(Math.max(...data));
        const minVal = 0;
        const range = maxVal - minVal || 1;

        // Grid lines
        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 1;
        const gridCount = 4;
        for (let i = 0; i <= gridCount; i++) {
            const y = pad.top + (plotH / gridCount) * i;
            ctx.beginPath();
            ctx.moveTo(pad.left, y);
            ctx.lineTo(pad.left + plotW, y);
            ctx.stroke();

            // Y-axis labels
            const val = maxVal - (range / gridCount) * i;
            ctx.fillStyle = textColor;
            ctx.font = `11px ${cssVar('--admin-font-mono') || 'monospace'}`;
            ctx.textAlign = 'right';
            ctx.textBaseline = 'middle';
            ctx.fillText(val >= 1000 ? `${(val / 1000).toFixed(1)}k` : Math.round(val).toString(), pad.left - 8, y);
        }

        // Compute points
        const points = data.map((v, i) => ({
            x: pad.left + (i / Math.max(data.length - 1, 1)) * plotW,
            y: pad.top + plotH - ((v - minVal) / range) * plotH,
        }));

        // Gradient fill
        if (fill) {
            const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + plotH);
            grad.addColorStop(0, hexToRgba(lineColor, 0.25));
            grad.addColorStop(1, hexToRgba(lineColor, 0.0));
            ctx.beginPath();
            ctx.moveTo(points[0].x, pad.top + plotH);
            for (const p of points) ctx.lineTo(p.x, p.y);
            ctx.lineTo(points[points.length - 1].x, pad.top + plotH);
            ctx.closePath();
            ctx.fillStyle = grad;
            ctx.fill();
        }

        // Line
        ctx.strokeStyle = lineColor;
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';
        ctx.beginPath();
        for (let i = 0; i < points.length; i++) {
            if (i === 0) {
                ctx.moveTo(points[i].x, points[i].y);
            } else {
                // Smooth curve using quadratic bezier
                const prev = points[i - 1];
                const curr = points[i];
                const cpx = (prev.x + curr.x) / 2;
                ctx.quadraticCurveTo(prev.x + (cpx - prev.x) * 0.8, prev.y, cpx, (prev.y + curr.y) / 2);
                ctx.quadraticCurveTo(curr.x - (curr.x - cpx) * 0.8, curr.y, curr.x, curr.y);
            }
        }
        ctx.stroke();

        // Data points
        for (const p of points) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
            ctx.fillStyle = lineColor;
            ctx.fill();
        }

        // X-axis labels
        if (labels.length) {
            ctx.fillStyle = textColor;
            ctx.font = `10px ${cssVar('--admin-font-mono') || 'monospace'}`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            const step = Math.max(1, Math.floor(labels.length / 6));
            for (let i = 0; i < labels.length; i += step) {
                const x = pad.left + (i / Math.max(labels.length - 1, 1)) * plotW;
                ctx.fillText(labels[i], x, pad.top + plotH + 8);
            }
        }

        // Dataset label
        if (this.options.label) {
            ctx.fillStyle = textColor;
            ctx.font = `500 11px ${cssVar('--admin-font-sans') || 'sans-serif'}`;
            ctx.textAlign = 'left';
            ctx.textBaseline = 'top';
            ctx.fillText(this.options.label, pad.left, 4);
        }
    }
}

/* ── BarChart ─────────────────────────────────────────────────── */

export class BarChart {
    /**
     * @param {HTMLCanvasElement} canvas
     * @param {object} options
     * @param {number[]}  options.data     Values
     * @param {string[]}  options.labels   Bar labels
     * @param {string[]}  [options.colors] Per-bar CSS var names
     * @param {number}    [options.height] Canvas logical height (default 200)
     */
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = Object.assign({
            data: [],
            labels: [],
            colors: [],
            height: 200,
        }, options);
        this.draw();
    }

    update(data, labels) {
        this.options.data = data;
        if (labels) this.options.labels = labels;
        this.draw();
    }

    draw() {
        const { data, labels, colors, height } = this.options;
        if (!data.length) return;

        const rect = this.canvas.parentElement
            ? this.canvas.parentElement.getBoundingClientRect()
            : { width: 600 };
        const width = Math.max(rect.width, 200);
        const ctx = setupCanvas(this.canvas, width, height);

        const primary = cssVar('--admin-primary') || '#3b82f6';
        const textColor = cssVar('--admin-text-muted') || '#64748b';
        const gridColor = cssVar('--admin-border-subtle') || '#162032';

        const pad = { top: 16, right: 16, bottom: 36, left: 52 };
        const plotW = width - pad.left - pad.right;
        const plotH = height - pad.top - pad.bottom;

        const maxVal = niceMax(Math.max(...data));
        const barCount = data.length;
        const barGap = Math.max(4, plotW * 0.02);
        const barWidth = Math.max(8, (plotW - barGap * (barCount + 1)) / barCount);

        // Grid
        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 1;
        const gridCount = 4;
        for (let i = 0; i <= gridCount; i++) {
            const y = pad.top + (plotH / gridCount) * i;
            ctx.beginPath();
            ctx.moveTo(pad.left, y);
            ctx.lineTo(pad.left + plotW, y);
            ctx.stroke();

            const val = maxVal - (maxVal / gridCount) * i;
            ctx.fillStyle = textColor;
            ctx.font = `11px ${cssVar('--admin-font-mono') || 'monospace'}`;
            ctx.textAlign = 'right';
            ctx.textBaseline = 'middle';
            ctx.fillText(val >= 1000 ? `${(val / 1000).toFixed(1)}k` : Math.round(val).toString(), pad.left - 8, y);
        }

        // Bars
        const totalBarSpace = barWidth * barCount + barGap * (barCount - 1);
        const startX = pad.left + (plotW - totalBarSpace) / 2;

        for (let i = 0; i < barCount; i++) {
            const barH = (data[i] / maxVal) * plotH;
            const x = startX + i * (barWidth + barGap);
            const y = pad.top + plotH - barH;

            const colorVar = colors[i] || '';
            const barColor = colorVar ? (cssVar(colorVar) || primary) : primary;

            // Bar with rounded top corners
            const radius = Math.min(4, barWidth / 2);
            ctx.beginPath();
            ctx.moveTo(x, pad.top + plotH);
            ctx.lineTo(x, y + radius);
            ctx.arcTo(x, y, x + radius, y, radius);
            ctx.lineTo(x + barWidth - radius, y);
            ctx.arcTo(x + barWidth, y, x + barWidth, y + radius, radius);
            ctx.lineTo(x + barWidth, pad.top + plotH);
            ctx.closePath();

            // Gradient fill
            const grad = ctx.createLinearGradient(0, y, 0, pad.top + plotH);
            grad.addColorStop(0, barColor);
            grad.addColorStop(1, hexToRgba(barColor, 0.5));
            ctx.fillStyle = grad;
            ctx.fill();

            // Value on top
            ctx.fillStyle = textColor;
            ctx.font = `600 10px ${cssVar('--admin-font-mono') || 'monospace'}`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            const displayVal = data[i] >= 1000 ? `${(data[i] / 1000).toFixed(1)}k` : data[i].toString();
            ctx.fillText(displayVal, x + barWidth / 2, y - 4);

            // Label below
            if (labels[i]) {
                ctx.fillStyle = textColor;
                ctx.font = `10px ${cssVar('--admin-font-mono') || 'monospace'}`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';
                ctx.fillText(labels[i], x + barWidth / 2, pad.top + plotH + 8);
            }
        }
    }
}

/* ── DonutChart ───────────────────────────────────────────────── */

export class DonutChart {
    /**
     * @param {HTMLCanvasElement} canvas
     * @param {object} options
     * @param {number[]}  options.data     Values (proportional slices)
     * @param {string[]}  options.labels   Slice labels
     * @param {string[]}  [options.colors] Per-slice CSS var names or hex colours
     * @param {number}    [options.size]   Canvas logical size (default 180)
     * @param {string}    [options.centerLabel]  Text in the centre
     * @param {string}    [options.centerValue]  Large value in the centre
     */
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = Object.assign({
            data: [],
            labels: [],
            colors: [
                '--admin-primary', '--admin-success', '--admin-warning',
                '--admin-info', '--admin-danger', '--admin-text-muted',
            ],
            size: 180,
            centerLabel: '',
            centerValue: '',
        }, options);
        this.draw();
    }

    draw() {
        const { data, labels, colors, size, centerLabel, centerValue } = this.options;
        if (!data.length) return;

        const ctx = setupCanvas(this.canvas, size, size);
        const total = data.reduce((a, b) => a + b, 0);
        if (total <= 0) return;

        const cx = size / 2;
        const cy = size / 2;
        const outerRadius = (size - 16) / 2;
        const innerRadius = outerRadius * 0.62;

        const textColor = cssVar('--admin-text') || '#e2e8f0';
        const mutedColor = cssVar('--admin-text-muted') || '#64748b';

        const defaultColors = [
            '--admin-primary', '--admin-success', '--admin-warning',
            '--admin-info', '--admin-danger', '--admin-text-muted',
        ];

        let startAngle = -Math.PI / 2;

        for (let i = 0; i < data.length; i++) {
            const sliceAngle = (data[i] / total) * Math.PI * 2;
            const endAngle = startAngle + sliceAngle;

            const colorVar = colors[i] || defaultColors[i % defaultColors.length];
            const color = colorVar.startsWith('#')
                ? colorVar
                : (cssVar(colorVar) || cssVar(defaultColors[i % defaultColors.length]));

            ctx.beginPath();
            ctx.arc(cx, cy, outerRadius, startAngle, endAngle);
            ctx.arc(cx, cy, innerRadius, endAngle, startAngle, true);
            ctx.closePath();
            ctx.fillStyle = color;
            ctx.fill();

            startAngle = endAngle;
        }

        // Centre text
        if (centerValue) {
            ctx.fillStyle = textColor;
            ctx.font = `700 ${Math.round(size * 0.17)}px ${cssVar('--admin-font-mono') || 'monospace'}`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(centerValue, cx, centerLabel ? cy - 6 : cy);
        }

        if (centerLabel) {
            ctx.fillStyle = mutedColor;
            ctx.font = `500 ${Math.round(size * 0.065)}px ${cssVar('--admin-font-sans') || 'sans-serif'}`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(centerLabel, cx, cy + size * 0.12);
        }
    }

    /** Get resolved colour values for building a legend. */
    getColors() {
        const defaultColors = [
            '--admin-primary', '--admin-success', '--admin-warning',
            '--admin-info', '--admin-danger', '--admin-text-muted',
        ];
        return this.options.data.map((_, i) => {
            const cv = this.options.colors[i] || defaultColors[i % defaultColors.length];
            return cv.startsWith('#') ? cv : (cssVar(cv) || '#3b82f6');
        });
    }
}

/* ── GaugeChart ───────────────────────────────────────────────── */

export class GaugeChart {
    /**
     * @param {HTMLCanvasElement} canvas
     * @param {object} options
     * @param {number}  options.value       Current value (0-100)
     * @param {string}  [options.label]     Label text
     * @param {number}  [options.size]      Canvas logical size (default 160)
     * @param {object}  [options.thresholds] { warning: 60, danger: 80 }
     */
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.options = Object.assign({
            value: 0,
            label: '',
            size: 160,
            thresholds: { warning: 60, danger: 80 },
        }, options);
        this.animatedValue = 0;
        this._animationId = null;
        this.animate();
    }

    update(value) {
        this.options.value = Math.max(0, Math.min(100, value));
        this.animate();
    }

    animate() {
        if (this._animationId) cancelAnimationFrame(this._animationId);
        const target = this.options.value;
        const start = this.animatedValue;
        const duration = 600;
        const startTime = performance.now();

        const step = (now) => {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            this.animatedValue = start + (target - start) * eased;
            this.draw();
            if (progress < 1) {
                this._animationId = requestAnimationFrame(step);
            }
        };
        this._animationId = requestAnimationFrame(step);
    }

    draw() {
        const { label, size, thresholds } = this.options;
        const value = this.animatedValue;
        const ctx = setupCanvas(this.canvas, size, size);

        const cx = size / 2;
        const cy = size / 2;
        const radius = (size - 24) / 2;
        const lineWidth = 10;

        // Determine colour based on thresholds
        let color;
        if (value >= thresholds.danger) {
            color = cssVar('--admin-danger') || '#f43f5e';
        } else if (value >= thresholds.warning) {
            color = cssVar('--admin-warning') || '#f59e0b';
        } else {
            color = cssVar('--admin-success') || '#10b981';
        }

        const bgColor = cssVar('--admin-border-subtle') || '#162032';
        const textColor = cssVar('--admin-text') || '#e2e8f0';
        const mutedColor = cssVar('--admin-text-muted') || '#64748b';

        // Arc angles: 3/4 circle (from ~7:30 to ~4:30)
        const startAngle = Math.PI * 0.75;
        const endAngle = Math.PI * 2.25;
        const sweep = endAngle - startAngle;

        // Background track
        ctx.beginPath();
        ctx.arc(cx, cy, radius, startAngle, endAngle);
        ctx.strokeStyle = bgColor;
        ctx.lineWidth = lineWidth;
        ctx.lineCap = 'round';
        ctx.stroke();

        // Value arc
        const valueAngle = startAngle + (value / 100) * sweep;
        ctx.beginPath();
        ctx.arc(cx, cy, radius, startAngle, valueAngle);
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.lineCap = 'round';
        ctx.stroke();

        // Percentage text
        ctx.fillStyle = textColor;
        ctx.font = `700 ${Math.round(size * 0.2)}px ${cssVar('--admin-font-mono') || 'monospace'}`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${Math.round(value)}%`, cx, cy - 4);

        // Label text
        if (label) {
            ctx.fillStyle = mutedColor;
            ctx.font = `500 ${Math.round(size * 0.075)}px ${cssVar('--admin-font-sans') || 'sans-serif'}`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(label, cx, cy + size * 0.16);
        }
    }
}
