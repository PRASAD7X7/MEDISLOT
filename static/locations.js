document.addEventListener("DOMContentLoaded", async () => {
  const app = window.MediSlot;
  const citySelect = document.getElementById("city-filter");
  const areaSelect = document.getElementById("area-filter");
  const countElement = document.getElementById("clinic-count");
  const clinicGrid = document.getElementById("clinic-grid");

  try {
    const { clinics, doctors } = await app.loadBootstrap();
    const cities = [...new Set(clinics.map((clinic) => clinic.city))].sort();

    citySelect.innerHTML += cities
      .map((city) => `<option value="${app.escapeHtml(city)}">${app.escapeHtml(city)}</option>`)
      .join("");

    function populateAreas() {
      const selectedCity = citySelect.value;
      const areas = [...new Set(
        clinics
          .filter((clinic) => !selectedCity || clinic.city === selectedCity)
          .map((clinic) => clinic.area)
      )].sort();

      areaSelect.innerHTML = '<option value="">All areas</option>'
        + areas
          .map((area) => `<option value="${app.escapeHtml(area)}">${app.escapeHtml(area)}</option>`)
          .join("");
    }

    function renderClinics() {
      const filteredClinics = clinics.filter((clinic) => {
        const matchesCity = !citySelect.value || clinic.city === citySelect.value;
        const matchesArea = !areaSelect.value || clinic.area === areaSelect.value;
        return matchesCity && matchesArea;
      });

      countElement.textContent = `${filteredClinics.length} clinics available`;

      if (!filteredClinics.length) {
        clinicGrid.innerHTML = `
          <div class="empty-state">
            <h3>No clinics match this location</h3>
            <p>Try another city or area selection.</p>
          </div>
        `;
        return;
      }

      clinicGrid.innerHTML = filteredClinics
        .map((clinic, index) => {
          const clinicDoctors = doctors.filter((doctor) => doctor.clinicId === clinic.id);
          const revealClass = index % 3 === 1
            ? "reveal-delay"
            : index % 3 === 2
              ? "reveal-delay-2"
              : "";

          return `
            <article class="clinic-card reveal ${revealClass}">
              <div class="clinic-head">
                <div>
                  <p class="mini-tag">${app.escapeHtml(clinic.city)}</p>
                  <h3>${app.escapeHtml(clinic.name)}</h3>
                </div>
                <span class="avatar-badge">${clinicDoctors.length}</span>
              </div>
              <p class="card-copy">${app.escapeHtml(clinic.address)}</p>
              <div class="doctor-meta">
                <span><strong>Area:</strong> ${app.escapeHtml(clinic.area)}</span><br />
                <span><strong>Hours:</strong> ${app.escapeHtml(clinic.hours)}</span><br />
                <span><strong>Contact:</strong> ${app.escapeHtml(clinic.phone)}</span>
              </div>
              <div class="badge-row">
                ${clinicDoctors.map((doctor) => `<span class="tag">${app.escapeHtml(doctor.type)}</span>`).join("")}
              </div>
              <div class="button-row">
                <a class="button button-primary" href="/book.html?location=${encodeURIComponent(clinic.id)}">Book Here</a>
              </div>
            </article>
          `;
        })
        .join("");

      app.bindReveal(clinicGrid);
    }

    citySelect.addEventListener("change", () => {
      populateAreas();
      renderClinics();
    });

    areaSelect.addEventListener("change", renderClinics);

    populateAreas();
    renderClinics();
  } catch (error) {
    console.error(error);
    countElement.textContent = "Unable to load locations.";
    clinicGrid.innerHTML = `
      <div class="empty-state">
        <h3>Unable to load clinic locations</h3>
        <p>Please try refreshing the page.</p>
      </div>
    `;
  }
});
