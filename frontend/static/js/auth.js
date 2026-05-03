function setFieldError(id, message) {
    const el = document.getElementById(id);
    if (el) el.textContent = message || "";
}

function clearAuthErrors() {
    document.querySelectorAll(".field-error").forEach((el) => {
        el.textContent = "";
    });
    document.querySelectorAll(".field").forEach((el) => {
        el.classList.remove("error");
    });
}

function setLoading(button, loading) {
    button.disabled = loading;
    button.classList.toggle("loading", loading);
}

function validateSignup(fullName, email, password) {
    let valid = true;
    if (fullName.length < 2 || fullName.length > 100) {
        setFieldError("signup-name-error", "Full name must be 2-100 characters.");
        document.getElementById("signup-name-field").classList.add("error");
        valid = false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 255) {
        setFieldError("signup-email-error", "Enter a valid email (max 255 chars).");
        document.getElementById("signup-email-field").classList.add("error");
        valid = false;
    }
    if (password.length < 8 || !/[A-Z]/.test(password) || !/\d/.test(password)) {
        setFieldError("signup-password-error", "Min 8 chars with 1 uppercase and 1 number.");
        document.getElementById("signup-password-field").classList.add("error");
        valid = false;
    }
    return valid;
}

function initAuthPage() {
    const loginTab = document.getElementById("tab-login");
    const signupTab = document.getElementById("tab-signup");
    const loginForm = document.getElementById("login-form");
    const signupForm = document.getElementById("signup-form");

    function showTab(tab) {
        const loginActive = tab === "login";
        loginTab.classList.toggle("active", loginActive);
        signupTab.classList.toggle("active", !loginActive);
        loginForm.style.display = loginActive ? "block" : "none";
        signupForm.style.display = loginActive ? "none" : "block";
        clearAuthErrors();
    }

    loginTab.addEventListener("click", () => showTab("login"));
    signupTab.addEventListener("click", () => showTab("signup"));

    loginForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearAuthErrors();
        const button = document.getElementById("login-submit");
        setLoading(button, true);

        const email = document.getElementById("login-email").value.trim();
        const password = document.getElementById("login-password").value;

        try {
            const response = await apiFetch("/api/v1/auth/login", {
                method: "POST",
                body: JSON.stringify({ email, password })
            });
            const payload = await response.json();
            if (!response.ok) {
                document.getElementById("login-email-field").classList.add("error");
                document.getElementById("login-password-field").classList.add("error");
                setFieldError("login-form-error", payload.message || "Invalid credentials.");
                return;
            }
            setAccessToken(payload.data.access_token);
            showToast("Logged in successfully", "success");
            window.location.href = "dashboard.html";
        } catch (error) {
            setFieldError("login-form-error", error.message);
        } finally {
            setLoading(button, false);
        }
    });

    signupForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearAuthErrors();
        const button = document.getElementById("signup-submit");
        setLoading(button, true);

        const fullName = document.getElementById("signup-name").value.trim();
        const email = document.getElementById("signup-email").value.trim();
        const password = document.getElementById("signup-password").value;
        if (!validateSignup(fullName, email, password)) {
            setLoading(button, false);
            return;
        }

        try {
            const response = await apiFetch("/api/v1/auth/signup", {
                method: "POST",
                body: JSON.stringify({ full_name: fullName, email, password })
            });
            const payload = await response.json();
            if (!response.ok) {
                setFieldError("signup-form-error", payload.message || "Signup failed.");
                return;
            }
            setAccessToken(payload.data.access_token);
            showToast("Signup successful", "success");
            window.location.href = "dashboard.html";
        } catch (error) {
            setFieldError("signup-form-error", error.message);
        } finally {
            setLoading(button, false);
        }
    });
}

document.addEventListener("DOMContentLoaded", initAuthPage);
