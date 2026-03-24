document.addEventListener("DOMContentLoaded", async () => {
  const app = window.MediSlot;
  const totalElement = document.getElementById("admin-total");
  const todayElement = document.getElementById("admin-today");
  const locationsElement = document.getElementById("admin-locations");
  const rows = document.getElementById("appointment-rows");
  const emptyState = document.getElementById("admin-empty");
  const tableWrap = document.getElementById("admin-table-wrap");

  try {
    const appointments = await app.request("/api/admin/appointments");
    const sortedAppointments = appointments
      .slice()
      .sort((left, right) => new Date(right.bookedAt) - new Date(left.bookedAt));
    const today = app.todayISO();
    const locations = new Set(sortedAppointments.map((item) => item.clinicId));

    totalElement.textContent = String(sortedAppointments.length);
    todayElement.textContent = String(
      sortedAppointments.filter((item) => item.date === today).length
    );
    locationsElement.textContent = String(locations.size);

    if (!sortedAppointments.length) {
      emptyState.classList.remove("hidden");
      tableWrap.classList.add("hidden");
      return;
    }

    rows.innerHTML = sortedAppointments
      .map(
        (appointment) => `
          <tr>
            <td>${app.escapeHtml(appointment.patientName)}</td>
            <td>${app.escapeHtml(appointment.doctorName)}<br /><span class="tiny-note">${app.escapeHtml(appointment.doctorType)}</span></td>
            <td>${app.escapeHtml(appointment.clinicName)}<br /><span class="tiny-note">${app.escapeHtml(appointment.location)}</span></td>
            <td>${app.escapeHtml(app.formatDate(appointment.date))}</td>
            <td>${app.escapeHtml(appointment.time)}</td>
            <td>${app.escapeHtml(app.formatDateTime(appointment.bookedAt))}</td>
          </tr>
        `
      )
      .join("");
  } catch (error) {
    console.error(error);
    emptyState.classList.remove("hidden");
    tableWrap.classList.add("hidden");
    emptyState.innerHTML = `
      <h3>Unable to load appointments</h3>
      <p>Please refresh the page and try again.</p>
    `;
  }
});
