// Configuration file for frontend
// You can override these values by setting window.AZURE_CLIENT_ID, window.AZURE_TENANT_ID, window.API_BASE_URL
// before loading app.js

window.AZURE_CLIENT_ID = window.AZURE_CLIENT_ID || '';
window.AZURE_TENANT_ID = window.AZURE_TENANT_ID || '';
// Same origin when the UI is served by FastAPI (Render, etc.). Use http://localhost:8000 only when the UI runs on another port (e.g. python -m http.server 8080).
if (typeof window.API_BASE_URL === 'undefined') {
    const port = String(window.location.port || '');
    const splitLocalDev =
        window.location.hostname === 'localhost' && port === '8080';
    window.API_BASE_URL = splitLocalDev ? 'http://localhost:8000' : '';
}

