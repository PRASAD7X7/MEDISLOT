document.addEventListener("DOMContentLoaded", async () => {
  const app = window.MediSlot;
  const form = document.getElementById("booking-form");
  const patientNameInput = document.getElementById("patient-name");
  const phoneInput = document.getElementById("phone-number");
  const doctorTypeSelect = document.getElementById("doctor-type");
  const locationSelect = document.getElementById("location-select");
  const doctorSelect = document.getElementById("doctor-select");
  const dateInput = document.getElementById("appointment-date");
  const timeSelect = document.getElementById("time-slot");
  const slotGrid = document.getElementById("slot-grid");
  const summaryList = document.getElementById("booking-summary");
  const recentAppointmentsList = document.getElementById("recent-appointments");
  const feedback = document.getElementById("booking-feedback");
  const params = new URLSearchParams(window.location.search);
  const activityUrl = form.dataset.activityUrl || "/api/activity";
  const confirmationPath = form.dataset.confirmationPath || "/confirmation.html";

  let doctors = [];
  let clinics = [];

  function showFeedback(message) {
    feedback.textContent = message;
    feedback.classList.remove("hidden");
  }

  function clearFeedback() {
    feedback.textContent = "";
    feedback.classList.add("hidden");
  }

  function updateSummary() {
    const doctor = doctors.find((item) => item.id === doctorSelect.value);
    const clinic = clinics.find((item) => item.id === (doctor ? doctor.clinicId : locationSelect.value));
    const dateText = dateInput.value ? app.formatDate(dateInput.value) : "Not selected";
    const timeText = timeSelect.value || "Not selected";

    summaryList.innerHTML = `
      <li><span>Doctor</span><strong>${doctor ? app.escapeHtml(doctor.name) : "Not selected"}</strong></li>
      <li><span>Clinic</span><strong>${clinic ? app.escapeHtml(clinic.name) : "Not selected"}</strong></li>
      <li><span>Date</span><strong>${app.escapeHtml(dateText)}</strong></li>
      <li><span>Time</span><strong>${app.escapeHtml(timeText)}</strong></li>
    `;
  }

  function renderRecentAppointments(appointments) {
    if (!appointments.length) {
      recentAppointmentsList.innerHTML = `
        <li><span>No appointments yet.</span><strong>Waiting</strong></li>
      `;
      return;
    }

    recentAppointmentsList.innerHTML = appointments
      .slice()
      .sort((left, right) => new Date(right.bookedAt) - new Date(left.bookedAt))
      .slice(0, 4)
      .map(
        (appointment) => `
          <li>
            <span>${app.escapeHtml(appointment.doctorName)}<br />${app.escapeHtml(app.formatDate(appointment.date))}</span>
            <strong>${app.escapeHtml(appointment.time)}</strong>
          </li>
        `
      )
      .join("");
  }

  function filteredDoctors() {
    return doctors.filter((doctor) => {
      const matchesType = !doctorTypeSelect.value || doctor.type === doctorTypeSelect.value;
      const matchesLocation = !locationSelect.value || doctor.clinicId === locationSelect.value;
      return matchesType && matchesLocation;
    });
  }

  function populateDoctorOptions(preferredDoctorId) {
    const options = filteredDoctors();
    const currentValue = preferredDoctorId || doctorSelect.value;

    doctorSelect.innerHTML = '<option value="">Choose a doctor</option>'
      + options
        .map(
          (doctor) => `
            <option value="${app.escapeHtml(doctor.id)}">
              ${app.escapeHtml(`${doctor.name} - ${doctor.clinicName}`)}
            </option>
          `
        )
        .join("");

    const nextValue = options.some((doctor) => doctor.id === currentValue)
      ? currentValue
      : options.length === 1
        ? options[0].id
        : "";

    doctorSelect.value = nextValue;
  }

  function renderSlotButtons(slots) {
    if (!slots.length) {
      slotGrid.innerHTML = '<span class="status-pill neutral">Select a doctor and date to view slots</span>';
      return;
    }

    slotGrid.innerHTML = slots
      .map(
        (slot) => `
          <button
            class="slot-button ${timeSelect.value === slot.time ? "is-selected" : ""}"
            type="button"
            data-slot="${app.escapeHtml(slot.time)}"
            ${slot.booked ? "disabled" : ""}
          >
            ${app.escapeHtml(slot.time)} ${slot.booked ? "Booked" : ""}
          </button>
        `
      )
      .join("");

    slotGrid.querySelectorAll(".slot-button").forEach((button) => {
      button.addEventListener("click", () => {
        timeSelect.value = button.dataset.slot || "";
        renderSlotButtons(slots);
        updateSummary();
      });
    });
  }

  async function loadAvailability() {
    if (!doctorSelect.value || !dateInput.value) {
      timeSelect.innerHTML = '<option value="">Choose a time slot</option>';
      renderSlotButtons([]);
      updateSummary();
      return;
    }

    const doctor = doctors.find((item) => item.id === doctorSelect.value);
    if (!doctor) {
      return;
    }

    const appointments = await app.request(
      `/api/availability?doctor_id=${encodeURIComponent(doctor.id)}&date=${encodeURIComponent(dateInput.value)}`
    );
    const bookedTimes = new Set(appointments.map((item) => item.time));
    const slots = doctor.timeSlots.map((time) => ({
      time,
      booked: bookedTimes.has(time),
    }));
    const selectedTimeStillOpen = slots.some(
      (slot) => slot.time === timeSelect.value && !slot.booked
    );

    timeSelect.innerHTML = '<option value="">Choose a time slot</option>'
      + slots
        .map(
          (slot) => `
            <option value="${app.escapeHtml(slot.time)}" ${slot.booked ? "disabled" : ""}>
              ${app.escapeHtml(slot.time)}${slot.booked ? " - Booked" : ""}
            </option>
          `
        )
        .join("");

    if (!selectedTimeStillOpen) {
      timeSelect.value = "";
    }

    renderSlotButtons(slots);
    updateSummary();
  }

  async function refreshRecentAppointments() {
    const appointments = await app.request(activityUrl);
    renderRecentAppointments(appointments);
  }

  function syncSelectionsFromDoctor() {
    const doctor = doctors.find((item) => item.id === doctorSelect.value);

    if (!doctor) {
      updateSummary();
      return;
    }

    doctorTypeSelect.value = doctor.type;
    locationSelect.value = doctor.clinicId;
    populateDoctorOptions(doctor.id);
    updateSummary();
  }

  function applyQueryPrefill() {
    const doctorId = params.get("doctorId");
    const location = params.get("location");
    const date = params.get("date");

    dateInput.min = app.todayISO();
    dateInput.value = date && date >= app.todayISO() ? date : app.todayISO();

    if (doctorId) {
      const doctor = doctors.find((item) => item.id === doctorId);
      if (doctor) {
        doctorTypeSelect.value = doctor.type;
        locationSelect.value = doctor.clinicId;
        populateDoctorOptions(doctor.id);
        return;
      }
    }

    if (location) {
      locationSelect.value = location;
    }

    populateDoctorOptions();
  }

  try {
    const [{ doctors: doctorData, clinics: clinicData }, appointments] = await Promise.all([
      app.loadBootstrap(),
      app.request(activityUrl),
    ]);

    doctors = doctorData;
    clinics = clinicData;

    const doctorTypes = [...new Set(doctors.map((doctor) => doctor.type))].sort();

    doctorTypeSelect.innerHTML += doctorTypes
      .map((type) => `<option value="${app.escapeHtml(type)}">${app.escapeHtml(type)}</option>`)
      .join("");

    locationSelect.innerHTML += clinics
      .map(
        (clinic) => `
          <option value="${app.escapeHtml(clinic.id)}">
            ${app.escapeHtml(`${clinic.city}, ${clinic.area} - ${clinic.name}`)}
          </option>
        `
      )
      .join("");

    renderRecentAppointments(appointments);
    applyQueryPrefill();
    await loadAvailability();

    doctorTypeSelect.addEventListener("change", async () => {
      clearFeedback();
      populateDoctorOptions();
      await loadAvailability();
    });

    locationSelect.addEventListener("change", async () => {
      clearFeedback();
      populateDoctorOptions();
      await loadAvailability();
    });

    doctorSelect.addEventListener("change", async () => {
      clearFeedback();
      syncSelectionsFromDoctor();
      await loadAvailability();
    });

    dateInput.addEventListener("change", async () => {
      clearFeedback();
      await loadAvailability();
    });

    timeSelect.addEventListener("change", updateSummary);

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearFeedback();

      if (!doctorSelect.value || !timeSelect.value) {
        showFeedback("Please select a doctor and an available time slot.");
        return;
      }

      try {
        const appointment = await app.request("/api/appointments", {
          method: "POST",
          body: {
            patientName: patientNameInput.value.trim(),
            phone: phoneInput.value.trim(),
            doctorId: doctorSelect.value,
            date: dateInput.value,
            time: timeSelect.value,
          },
        });

        window.location.href = `${confirmationPath}?id=${encodeURIComponent(appointment.id)}`;
      } catch (error) {
        showFeedback(error.message);
        await loadAvailability();
        await refreshRecentAppointments();
      }
    });

    updateSummary();
  } catch (error) {
    console.error(error);
    showFeedback("Unable to load booking data. Please refresh the page.");
  }
});
