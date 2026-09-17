/**
 * LogiScale Web - Cliente de API HTTP Unificado
 * Gerencia URLs base, injeção de tokens de autorização e tratamento de erros.
 */

async function apiFetch(endpoint, options = {}) {
    const baseUrl = window.APP_CONFIG.API_BASE_URL.replace(/\/$/, "");
    const cleanEndpoint = endpoint.startsWith("/") ? endpoint : "/" + endpoint;
    const url = baseUrl + cleanEndpoint;

    const headers = options.headers || {};

    // Injeta Token de Autenticação se disponível
    if (window.authService && window.authService.getToken()) {
        headers["Authorization"] = `Bearer ${window.authService.getToken()}`;
    }

    // Define Content-Type JSON para requisições com body que não sejam FormData
    if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
    }

    const config = {
        ...options,
        headers
    };

    try {
        const response = await fetch(url, config);

        if (response.status === 401) {
            console.warn("Sessão expirada ou não autorizada.");
            if (window.abrirModalLogin) {
                window.abrirModalLogin("Sessão expirada. Por favor, faça login novamente.");
            }
        }

        if (response.status === 403) {
            const errData = await response.json().catch(() => ({}));
            mostrarToast(errData.error || "Ação restrita para o perfil Administrador.", "error");
            throw new Error(errData.error || "Acesso negado.");
        }

        return response;
    } catch (error) {
        console.error(`Erro de comunicação na rota ${endpoint}:`, error);
        throw error;
    }
}

async function apiGet(endpoint) {
    const res = await apiFetch(endpoint, { method: "GET" });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Erro na requisição" }));
        throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json();
}

async function apiPost(endpoint, data = {}) {
    const res = await apiFetch(endpoint, {
        method: "POST",
        body: JSON.stringify(data)
    });
    const resData = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new Error(resData.error || `HTTP ${res.status}`);
    }
    return resData;
}

async function apiPut(endpoint, data = {}) {
    const res = await apiFetch(endpoint, {
        method: "PUT",
        body: JSON.stringify(data)
    });
    const resData = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new Error(resData.error || `HTTP ${res.status}`);
    }
    return resData;
}

async function apiDelete(endpoint) {
    const res = await apiFetch(endpoint, { method: "DELETE" });
    const resData = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new Error(resData.error || `HTTP ${res.status}`);
    }
    return resData;
}

async function apiUpload(endpoint, formData) {
    const res = await apiFetch(endpoint, {
        method: "POST",
        body: formData
    });
    const resData = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new Error(resData.error || `HTTP ${res.status}`);
    }
    return resData;
}

async function apiDownload(endpoint, nomeArquivo) {
    const res = await apiFetch(endpoint, { method: "GET" });
    if (!res.ok) {
        throw new Error(`Falha ao baixar arquivo (HTTP ${res.status})`);
    }
    const blob = await res.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = nomeArquivo;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(downloadUrl);
}

window.api = {
    fetch: apiFetch,
    get: apiGet,
    post: apiPost,
    put: apiPut,
    delete: apiDelete,
    upload: apiUpload,
    download: apiDownload
};
