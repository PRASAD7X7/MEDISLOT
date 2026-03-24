document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("contact-form");
  const feedback = document.getElementById("contact-feedback");

  if (!form || !feedback) {
    return;
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    feedback.textContent = "Thanks for contacting MediSlot. We will get back to you shortly.";
    feedback.classList.remove("hidden");
    form.reset();
  });
});
