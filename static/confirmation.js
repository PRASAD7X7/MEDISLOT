document.addEventListener("DOMContentLoaded", async () => {
  const app = window.MediSlot;
  const container = document.getElementById("confirmation-state");
  const appointmentId = new URLSearchParams(window.location.search).get("id");

  if (!appointmentId) {
    container.innerHTML = `
      <div class="notice-card reveal">
        <h2>No appointment was selected.</h2>
        <p class="contact-copy">Book an appointment first to view the confirmation page.</p>
        <div class="button-row">
          <a class="button button-primary" href="/book.html">Book Appointment</a>
        </div>
      </div>
    `;
    app.bindReveal(container);
    return;
  }

  try {
    const appointment = await app.request(`/api/confirmation/${encodeURIComponent(appointmentId)}`);

    container.innerHTML = `
      <div class="success-card reveal">
        <div class="success-mark">+</div>
        <p class="section-tag">Booking Successful</p>
        <h2>Your appointment has been booked successfully</h2>
        <p class="contact-copy">
          MediSlot has saved your appointment and blocked the selected slot.
        </p>
        <div class="detail-grid">
          <div class="detail-card">
            <p class="mini-tag">Doctor Name</p>
            <h3>${app.escapeHtml(appointment.doctorName)}</h3>
          </div>
          <div class="detail-card">
            <p class="mini-tag">Clinic Name</p>
            <h3>${app.escapeHtml(appointment.clinicName)}</h3>
          </div>
          <div class="detail-card">
            <p class="mini-tag">Date</p>
            <h3>${app.escapeHtml(app.formatDate(appointment.date))}</h3>
          </div>
          <div class="detail-card">
            <p class="mini-tag">Time</p>
            <h3>${app.escapeHtml(appointment.time)}</h3>
          </div>
        </div>
        <div class="button-row">
          <a class="button button-primary" href="/book.html">Book Another Appointment</a>
          <a class="button button-secondary" href="/login.html">Admin Login</a>
        </div>
      </div>
    `;

    app.bindReveal(container);
  } catch (error) {
    console.error(error);
    container.innerHTML = `
      <div class="notice-card reveal">
        <h2>Appointment not found</h2>
        <p class="contact-copy">The requested booking could not be loaded from the backend.</p>
        <div class="button-row">
          <a class="button button-primary" href="/book.html">Book Appointment</a>
        </div>
      </div>
    `;
    app.bindReveal(container);
  }
});
