document.addEventListener("DOMContentLoaded", () => {
  const app = window.MediSlot;
  const form = document.getElementById("login-form");
  const feedback = document.getElementById("login-feedback");
  const usernameInput = document.getElementById("admin-username");
  const passwordInput = document.getElementById("admin-password");
  const nextParam = new URLSearchParams(window.location.search).get("next");
  const next = nextParam && nextParam.startsWith("/") && !nextParam.startsWith("//")
    ? nextParam
    : "/admin.html";

  function showError(message) {
    feedback.textContent = message;
    feedback.classList.remove("hidden");
  }

  function clearError() {
    feedback.textContent = "";
    feedback.classList.add("hidden");
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();

    try {
      await app.request("/api/admin/login", {
        method: "POST",
        body: {
          username: usernameInput.value.trim(),
          password: passwordInput.value,
        },
      });

      window.location.href = next;
    } catch (error) {
      showError(error.message);
      passwordInput.value = "";
      passwordInput.focus();
    }
  });
});
