/**
 * SSE (Server-Sent Events) connection manager with auto-reconnect.
 *
 * EventSource natively retries on connection loss so reconnection is
 * handled by the browser.  This manager keeps track of open connections
 * so they can be torn down when navigating away from a view.
 */
export class SSEManager {
    /**
     * @param {string} basePath  Base URL prefix for SSE endpoints.
     */
    constructor(basePath = '/admin/api/sse') {
        this.basePath = basePath;
        /** @type {Map<string, EventSource>} */
        this.connections = new Map();
    }

    /**
     * Open an SSE connection for generic "message" events.
     *
     * @param {string}   endpoint   Path appended to basePath.
     * @param {function} onMessage  Callback receiving parsed JSON data.
     * @param {function} [onError]  Optional error callback.
     * @returns {EventSource}
     */
    connect(endpoint, onMessage, onError = null) {
        const url = `${this.basePath}${endpoint}`;
        if (this.connections.has(url)) {
            this.disconnect(url);
        }

        const source = new EventSource(url);
        source.onmessage = (event) => {
            try {
                onMessage(JSON.parse(event.data));
            } catch (e) {
                console.error('SSE parse error:', e);
            }
        };
        source.onerror = () => {
            if (onError) onError();
            // Auto-reconnect is built into EventSource
        };
        this.connections.set(url, source);
        return source;
    }

    /**
     * Open an SSE connection listening for a specific named event type.
     *
     * @param {string}   endpoint   Path appended to basePath.
     * @param {string}   eventType  SSE event name to listen for.
     * @param {function} onMessage  Callback receiving parsed JSON data.
     * @returns {EventSource}
     */
    connectTyped(endpoint, eventType, onMessage) {
        const url = `${this.basePath}${endpoint}`;
        if (this.connections.has(url)) {
            this.disconnect(url);
        }

        const source = new EventSource(url);
        source.addEventListener(eventType, (event) => {
            try {
                onMessage(JSON.parse(event.data));
            } catch (e) {
                console.error('SSE parse error:', e);
            }
        });
        this.connections.set(url, source);
        return source;
    }

    /**
     * Close a single SSE connection.
     *
     * @param {string} endpoint  Either a path or the full URL key.
     */
    disconnect(endpoint) {
        const url = endpoint.startsWith('/') ? `${this.basePath}${endpoint}` : endpoint;
        const source = this.connections.get(url);
        if (source) {
            source.close();
            this.connections.delete(url);
        }
    }

    /** Close every open SSE connection. */
    disconnectAll() {
        for (const source of this.connections.values()) {
            source.close();
        }
        this.connections.clear();
    }
}

/** Singleton instance used by all view modules. */
export const sse = new SSEManager();
