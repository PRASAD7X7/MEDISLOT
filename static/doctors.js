document.addEventListener("DOMContentLoaded", async () => {
  const app = window.MediSlot;
  const searchInput = document.getElementById("doctor-search");
  const typeSelect = document.getElementById("doctor-type-filter");
  const citySelect = document.getElementById("doctor-city-filter");
  const dateInput = document.getElementById("doctor-date-filter");
  const countElement = document.getElementById("doctors-count");
  const doctorsGrid = document.getElementById("doctors-grid");

  try {
    const { doctors } = await app.loadBootstrap();
    const doctorTypes = [...new Set(doctors.map((doctor) => doctor.type))].sort();
    const cities = [...new Set(doctors.map((doctor) => doctor.city))].sort();

    dateInput.min = app.todayISO();
    dateInput.value = app.todayISO();

    typeSelect.innerHTML += doctorTypes
      .map((type) => `<option value="${app.escapeHtml(type)}">${app.escapeHtml(type)}</option>`)
      .join("");

    citySelect.innerHTML += cities
      .map((city) => `<option value="${app.escapeHtml(city)}">${app.escapeHtml(city)}</option>`)
      .join("");

    async function renderDoctors() {
      const selectedDate = dateInput.value || app.todayISO();
      const availability = await app.request(
        `/api/availability?date=${encodeURIComponent(selectedDate)}`
      );
      const bookedLookup = new Set(
        availability.map((item) => `${item.doctorId}|${item.time}`)
      );
      const query = searchInput.value.trim().toLowerCase();

      const filteredDoctors = doctors.filter((doctor) => {
        const matchesQuery = !query
          || [
            doctor.name,
            doctor.type,
            doctor.clinicName,
            doctor.city,
            doctor.area,
          ]
            .join(" ")
            .toLowerCase()
            .includes(query);

        const matchesType = !typeSelect.value || doctor.type === typeSelect.value;
        const matchesCity = !citySelect.value || doctor.city === citySelect.value;
        return matchesQuery && matchesType && matchesCity;
      });

      countElement.textContent = `${filteredDoctors.length} doctors found for ${app.formatDate(selectedDate)}`;

      if (!filteredDoctors.length) {
        doctorsGrid.innerHTML = `
          <div class="empty-state">
            <h3>No doctors match your filters</h3>
            <p>Try another specialty, city, or search term.</p>
          </div>
        `;
        return;
      }

      doctorsGrid.innerHTML = filteredDoctors
        .map((doctor, index) => {
          const revealClass = index % 3 === 1
            ? "reveal-delay"
            : index % 3 === 2
              ? "reveal-delay-2"
              : "";
          const slotMarkup = doctor.timeSlots
            .map((time) => {
              const booked = bookedLookup.has(`${doctor.id}|${time}`);
              return `
                <span class="status-pill ${booked ? "booked" : "available"}">
                  ${app.escapeHtml(time)} ${booked ? "Booked" : "Available"}
                </span>
              `;
            })
            .join("");

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
                <span class="tag">${app.escapeHtml(doctor.phone)}</span>
                <span class="tag">${app.escapeHtml(doctor.hours)}</span>
              </div>
              <div class="slot-grid">
                ${slotMarkup}
              </div>
              <div class="button-row">
                <a class="button button-primary" href="/book.html?doctorId=${encodeURIComponent(doctor.id)}&date=${encodeURIComponent(selectedDate)}">Book Appointment</a>
              </div>
            </article>
          `;
        })
        .join("");

      app.bindReveal(doctorsGrid);
    }

    searchInput.addEventListener("input", renderDoctors);
    typeSelect.addEventListener("change", renderDoctors);
    citySelect.addEventListener("change", renderDoctors);
    dateInput.addEventListener("change", renderDoctors);

    await renderDoctors();
  } catch (error) {
    console.error(error);
    countElement.textContent = "Unable to load doctors.";
    doctorsGrid.innerHTML = `
      <div class="empty-state">
        <h3>Unable to load doctor data</h3>
        <p>Please try refreshing the page.</p>
      </div>
    `;
  }
});
