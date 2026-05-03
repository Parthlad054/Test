function getInitials(name) {
    const source = (name || "User").trim();
    const parts = source.split(/\s+/).filter(Boolean);
    const first = parts[0]?.[0] || "U";
    const second = parts[1]?.[0] || parts[0]?.[1] || "S";
    return `${first}${second}`.toUpperCase();
}

function colorFromName(name) {
    const text = name || "User";
    let hash = 0;
    for (let i = 0; i < text.length; i += 1) hash = text.charCodeAt(i) + ((hash << 5) - hash);
    const hue = Math.abs(hash) % 360;
    return `hsl(${hue}, 55%, 45%)`;
}

function avatarMarkup(name) {
    const initials = getInitials(name);
    const color = colorFromName(name);
    return `<span class="avatar" style="background:${color}">${initials}</span>`;
}

async function loadCurrentUser() {
    const response = await apiFetch("/api/v1/auth/me");
    if (!response.ok) return null;
    const payload = await response.json();
    return payload.data;
}

function applyNavActive() {
    const path = window.location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".nav-link").forEach((link) => {
        const href = link.getAttribute("href");
        link.classList.toggle("active", href === path);
    });
}

function installToastRoot() {
    if (document.querySelector(".toast-wrap")) return;
    const root = document.createElement("div");
    root.className = "toast-wrap";
    document.body.appendChild(root);
}

function showToast(message, type = "success") {
    installToastRoot();
    const root = document.querySelector(".toast-wrap");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    root.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

async function setupTopbar() {
    const user = await loadCurrentUser();
    if (!user) return null;

    const name = user.full_name || user.email;
    document.querySelectorAll("[data-user-avatar]").forEach((node) => {
        node.innerHTML = avatarMarkup(name);
    });
    document.querySelectorAll("[data-user-name]").forEach((node) => {
        node.textContent = name;
    });
    document.querySelectorAll("[data-user-role]").forEach((node) => {
        node.textContent = (user.role || "member").toUpperCase();
    });

    document.querySelectorAll("[data-logout]").forEach((button) => {
        button.addEventListener("click", () => {
            clearAccessToken();
            window.location.href = "index.html";
        });
    });

    return user;
}

function requireAuth() {
    if (!getAccessToken()) {
        window.location.href = "index.html";
        return false;
    }
    return true;
}
