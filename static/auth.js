document.addEventListener("DOMContentLoaded", () => {
  const registerForm = document.querySelector("[data-register-form]");
  const feedback = document.querySelector("[data-client-feedback]");

  function clearFeedback() {
    if (!feedback) {
      return;
    }

    feedback.textContent = "";
    feedback.classList.add("hidden");
  }

  function showFeedback(message) {
    if (!feedback) {
      return;
    }

    feedback.textContent = message;
    feedback.classList.remove("hidden");
  }

  if (!registerForm) {
    return;
  }

  registerForm.addEventListener("submit", (event) => {
    clearFeedback();

    const name = registerForm.querySelector("[name='name']").value.trim();
    const email = registerForm.querySelector("[name='email']").value.trim();
    const phone = registerForm.querySelector("[name='phone']").value.trim();
    const password = registerForm.querySelector("[name='password']").value;
    const confirmPassword = registerForm.querySelector("[name='confirm_password']").value;
    const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    const phoneValid = /^[0-9+\-\s]{7,20}$/.test(phone);

    if (!name || !email || !phone || !password || !confirmPassword) {
      event.preventDefault();
      showFeedback("Please complete every field before submitting.");
      return;
    }

    if (!emailValid) {
      event.preventDefault();
      showFeedback("Please enter a valid email address.");
      return;
    }

    if (!phoneValid) {
      event.preventDefault();
      showFeedback("Please enter a valid phone number.");
      return;
    }

    if (password.length < 6) {
      event.preventDefault();
      showFeedback("Password must be at least 6 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      event.preventDefault();
      showFeedback("Password and confirm password must match.");
    }
  });

  registerForm.addEventListener("input", clearFeedback);
});
