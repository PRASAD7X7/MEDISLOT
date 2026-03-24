document.addEventListener("DOMContentLoaded", async () => {
  const app = window.MediSlot;

  try {
    const today = app.todayISO();
    const [{ doctors, clinics }, stats, availability] = await Promise.all([
      app.loadBootstrap(),
      app.request("/api/stats"),
      app.request(`/api/availability?date=${encodeURIComponent(today)}`),
    ]);

    const metricContainer = document.getElementById("hero-metrics");
    const doctorsContainer = document.getElementById("featured-doctors");
    const locationsContainer = document.getElementById("location-preview");

    if (metricContainer) {
      metricContainer.innerHTML = [
        { value: `${doctors.length}+`, label: "Doctors listed" },
        { value: `${clinics.length}`, label: "Clinic locations" },
        { value: `${stats.appointmentCount}`, label: "Appointments stored" },
      ]
        .map(
          (metric) => `
            <div class="metric-card">
              <strong>${app.escapeHtml(metric.value)}</strong>
              <span>${app.escapeHtml(metric.label)}</span>
            </div>
          `
        )
        .join("");
    }

    if (doctorsContainer) {
      doctorsContainer.innerHTML = doctors
        .slice(0, 3)
        .map((doctor, index) => {
          const bookedCount = availability.filter(
            (item) => item.doctorId === doctor.id && item.date === today
          ).length;
          const openCount = doctor.timeSlots.length - bookedCount;
          const revealClass = index === 0
            ? ""
            : index === 1
              ? "reveal-delay"
              : "reveal-delay-2";

          return `
            <article class="doctor-card reveal ${revealClass}">
              <div class="doctor-head">
                <div>
                  <p class="mini-tag">${app.escapeHtml(doctor.type)}</p>
                  <h3>${app.escapeHtml(doctor.name)}</h3>
                </div>
                <span class="avatar-badge">${app.escapeHtml(app.getInitials(doctor.name))}</span>
              </div>
              <div class="doctor-meta">
                <span><strong>Clinic:</strong> ${app.escapeHtml(doctor.clinicName)}</span><br />
                <span><strong>Location:</strong> ${app.escapeHtml(`${doctor.city}, ${doctor.area}`)}</span><br />
                <span><strong>Experience:</strong> ${app.escapeHtml(doctor.experience)}</span>
              </div>
              <div class="badge-row">
                <span class="status-pill available">${openCount} slots open today</span>
                <span class="tag">${app.escapeHtml(doctor.phone)}</span>
              </div>
              <div class="button-row">
                <a class="button button-primary" href="/book.html?doctorId=${encodeURIComponent(doctor.id)}">Book Now</a>
                <a class="button button-secondary" href="/doctors.html">View Details</a>
              </div>
            </article>
          `;
        })
        .join("");
    }

    if (locationsContainer) {
      locationsContainer.innerHTML = clinics
        .slice(0, 3)
        .map((clinic, index) => {
          const revealClass = index === 0
            ? ""
            : index === 1
              ? "reveal-delay"
              : "reveal-delay-2";

          return `
            <article class="location-card reveal ${revealClass}">
              <p class="mini-tag">${app.escapeHtml(clinic.city)}</p>
              <h3>${app.escapeHtml(clinic.name)}</h3>
              <p class="card-copy">${app.escapeHtml(clinic.area)} - ${app.escapeHtml(clinic.hours)}</p>
              <div class="badge-row">
                <span class="tag">${clinic.doctorCount} doctors</span>
                <span class="tag">${app.escapeHtml(clinic.phone)}</span>
              </div>
              <a class="button button-secondary" href="/book.html?location=${encodeURIComponent(clinic.id)}">Book at this clinic</a>
            </article>
          `;
        })
        .join("");
    }

    app.bindReveal(document);
  } catch (error) {
    console.error(error);
  }
});
