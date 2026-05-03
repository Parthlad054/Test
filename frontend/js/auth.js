document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");
    const showRegister = document.getElementById("show-register");
    const showLogin = document.getElementById("show-login");

    showRegister.addEventListener("click", (e) => {
        e.preventDefault();
        loginForm.style.display = "none";
        registerForm.style.display = "block";
    });

    showLogin.addEventListener("click", (e) => {
        e.preventDefault();
        registerForm.style.display = "none";
        loginForm.style.display = "block";
    });

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        try {
            const res = await apiFetch("/auth/login", {
                method: "POST",
                body: JSON.stringify({ email, password })
            });

            if (!res.ok) {
                const responseData = await res.json();
                alert(responseData.message || "Login failed");
                return;
            }

            const responseData = await res.json();
            setTokens(responseData.data.access_token, responseData.data.refresh_token);
            window.location.href = "dashboard.html";
        } catch (err) {
            console.error(err);
        }
    });

    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = document.getElementById("reg-email").value;
        const password = document.getElementById("reg-password").value;

        try {
            const res = await apiFetch("/auth/register", {
                method: "POST",
                body: JSON.stringify({ email, password })
            });

            if (!res.ok) {
                const responseData = await res.json();
                alert(responseData.message || "Registration failed");
                return;
            }
            
            alert("Registration successful! Please login.");
            registerForm.style.display = "none";
            loginForm.style.display = "block";
        } catch (err) {
            console.error(err);
        }
    });
});
