/**
 * PyFly Admin API client.
 *
 * Provides a thin wrapper around fetch() for communicating with
 * the admin REST endpoints.
 */
export class AdminAPI {
    /**
     * @param {string} basePath  Base URL prefix (no trailing slash).
     */
    constructor(basePath = '/admin/api') {
        this.basePath = basePath;
    }

    /**
     * Issue a GET request and return parsed JSON.
     *
     * @param {string} endpoint  Path appended to basePath (e.g. "/beans").
     * @returns {Promise<any>}
     */
    async get(endpoint) {
        const resp = await fetch(`${this.basePath}${endpoint}`);
        if (!resp.ok) {
            throw new Error(`API error: ${resp.status}`);
        }
        return resp.json();
    }

    /**
     * Issue a POST request with a JSON body and return parsed JSON.
     *
     * @param {string} endpoint  Path appended to basePath.
     * @param {object} body      JSON-serialisable payload.
     * @returns {Promise<any>}
     */
    async post(endpoint, body = {}) {
        const resp = await fetch(`${this.basePath}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!resp.ok) {
            throw new Error(`API error: ${resp.status}`);
        }
        return resp.json();
    }
}

/** Singleton instance used by all view modules. */
export const api = new AdminAPI();
