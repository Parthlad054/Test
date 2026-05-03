const API_BASE = "http://localhost:8000";

function getAccessToken() {
    return localStorage.getItem("access_token");
}

function setAccessToken(token) {
    localStorage.setItem("access_token", token);
}

function clearAccessToken() {
    localStorage.removeItem("access_token");
}

async function apiFetch(endpoint, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
    };
    const token = getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;

    let response;
    try {
        response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
    } catch (error) {
        throw new Error("Network error. Please check your connection.");
    }

    if (response.status === 401) {
        clearAccessToken();
        if (!window.location.pathname.endsWith("/index.html") && window.location.pathname !== "/") {
            window.location.href = "index.html";
        }
        throw new Error("Unauthorized. Please login again.");
    }

    return response;
}
