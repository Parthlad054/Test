let currentEmail = "";
let currentOTP = "";
let resendTimer = null;

function showStep(stepId) {
  ["step-email", "step-otp", "step-reset", "step-success"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = id === stepId ? "block" : "none";
  });
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.classList.toggle("loading", loading);
}

function showFieldError(fieldId, errorId, message) {
  const field = document.getElementById(fieldId);
  const error = document.getElementById(errorId);
  if (field) field.classList.toggle("error", !!message);
  if (error) error.textContent = message || "";
}

function startResendTimer(seconds = 60) {
  const timerEl = document.getElementById("resend-timer");
  const resendLink = document.getElementById("resend-otp");
  if (!timerEl || !resendLink) return;
  resendLink.style.pointerEvents = "none";
  resendLink.style.opacity = "0.4";
  let remaining = seconds;
  timerEl.textContent = ` (${remaining}s)`;
  if (resendTimer) clearInterval(resendTimer);
  resendTimer = setInterval(() => {
    remaining--;
    timerEl.textContent = remaining > 0 ? ` (${remaining}s)` : "";
    if (remaining <= 0) {
      clearInterval(resendTimer);
      resendLink.style.pointerEvents = "auto";
      resendLink.style.opacity = "1";
    }
  }, 1000);
}

async function sendOTP(email) {
  const res = await apiFetch("/api/v1/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify({ email })
  });
  return res;
}

document.addEventListener("DOMContentLoaded", () => {
  showStep("step-email");

  // Step 1 — Send OTP
  document.getElementById("form-email").addEventListener("submit", async (e) => {
    e.preventDefault();
    showFieldError("field-email", "error-email", "");
    document.getElementById("error-email-form").textContent = "";
    const email = document.getElementById("input-email").value.trim();
    setLoading("btn-send-otp", true);
    try {
      const res = await sendOTP(email);
      const data = await res.json();
      if (!res.ok) {
        document.getElementById("error-email-form").textContent = data.message || "Failed to send OTP.";
        return;
      }
      currentEmail = email;
      document.getElementById("otp-email-display").textContent = email;
      showStep("step-otp");
      startResendTimer(60);
    } catch (err) {
      document.getElementById("error-email-form").textContent = "Network error. Please try again.";
    } finally {
      setLoading("btn-send-otp", false);
    }
  });

  // Resend OTP
  document.getElementById("resend-otp").addEventListener("click", async (e) => {
    e.preventDefault();
    document.getElementById("error-otp-form").textContent = "";
    try {
      await sendOTP(currentEmail);
      startResendTimer(60);
      document.getElementById("error-otp-form").textContent = "";
      // Show small success inline
      const msg = document.getElementById("error-otp-form");
      msg.style.color = "var(--success)";
      msg.textContent = "OTP resent successfully.";
      setTimeout(() => { msg.textContent = ""; msg.style.color = ""; }, 3000);
    } catch (err) {}
  });

  // Step 2 — Verify OTP
  document.getElementById("form-otp").addEventListener("submit", async (e) => {
    e.preventDefault();
    showFieldError("field-otp", "error-otp", "");
    document.getElementById("error-otp-form").textContent = "";
    const otp = document.getElementById("input-otp").value.trim();
    if (!/^\d{6}$/.test(otp)) {
      showFieldError("field-otp", "error-otp", "Enter a valid 6-digit OTP.");
      return;
    }
    setLoading("btn-verify-otp", true);
    try {
      const res = await apiFetch("/api/v1/auth/verify-otp", {
        method: "POST",
        body: JSON.stringify({ email: currentEmail, otp })
      });
      const data = await res.json();
      if (!res.ok) {
        showFieldError("field-otp", "error-otp", data.message || "Invalid OTP.");
        return;
      }
      currentOTP = otp;
      showStep("step-reset");
    } catch (err) {
      document.getElementById("error-otp-form").textContent = "Network error. Please try again.";
    } finally {
      setLoading("btn-verify-otp", false);
    }
  });

  // Step 3 — Reset Password
  document.getElementById("form-reset").addEventListener("submit", async (e) => {
    e.preventDefault();
    showFieldError("field-new-password", "error-new-password", "");
    showFieldError("field-confirm-password", "error-confirm-password", "");
    document.getElementById("error-reset-form").textContent = "";
    const newPass = document.getElementById("input-new-password").value;
    const confirmPass = document.getElementById("input-confirm-password").value;

    if (newPass.length < 8 || !/[A-Z]/.test(newPass) || !/\d/.test(newPass)) {
      showFieldError("field-new-password", "error-new-password", "Min 8 chars, 1 uppercase, 1 number.");
      return;
    }
    if (newPass !== confirmPass) {
      showFieldError("field-confirm-password", "error-confirm-password", "Passwords do not match.");
      return;
    }
    setLoading("btn-reset", true);
    try {
      const res = await apiFetch("/api/v1/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ email: currentEmail, otp: currentOTP, new_password: newPass })
      });
      const data = await res.json();
      if (!res.ok) {
        document.getElementById("error-reset-form").textContent = data.message || "Reset failed.";
        return;
      }
      showStep("step-success");
    } catch (err) {
      document.getElementById("error-reset-form").textContent = "Network error. Please try again.";
    } finally {
      setLoading("btn-reset", false);
    }
  });
});
