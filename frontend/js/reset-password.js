document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("reset-password-form");
    const msg = document.getElementById("reset-message");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const token = document.getElementById("token").value;
        const new_password = document.getElementById("new_password").value;

        try {
            const res = await apiFetch("/auth/reset-password", {
                method: "POST",
                body: JSON.stringify({ token, new_password })
            });

            const data = await res.json();
            
            if (res.ok) {
                msg.style.display = "block";
                msg.style.color = "green";
                msg.innerText = data.message;
                setTimeout(() => {
                    window.location.href = "auth.html";
                }, 2000);
            } else {
                msg.style.display = "block";
                msg.style.color = "red";
                msg.innerText = data.message || "Failed";
            }
        } catch (err) {
            console.error(err);
        }
    });
});
