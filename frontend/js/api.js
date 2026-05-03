const API_BASE = "http://localhost:8000";

function getToken() {
    return localStorage.getItem("access_token");
}

function setTokens(access, refresh) {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
}

function clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
}

async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        "Content-Type": "application/json",
        ...options.headers
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
        });

        if (response.status === 401) {
            clearTokens();
            window.location.href = "index.html";
            throw new Error("Unauthorized");
        }

        return response;
    } catch (err) {
        throw new Error(err?.message || "Network error. Please check your connection.");
    }
}
