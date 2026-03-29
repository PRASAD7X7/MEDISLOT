import json
import os
import re
import secrets
import sqlite3
from functools import wraps
from pathlib import Path
from datetime import datetime

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from medislot_core import (
    CLINICS,
    DATE_PATTERN,
    DOCTORS,
    SlotTakenError,
    clinic_by_id,
    doctor_by_id,
    serialize_activity_entry,
    serialize_availability_entry,
    serialize_clinic,
    serialize_confirmation_entry,
    serialize_doctor,
)


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "data" / "medislot_auth.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_PATTERN = re.compile(r"^[0-9+\-\s]{7,20}$")
PORT = int(os.environ.get("MEDISLOT_PORT", "8000"))
ADMIN_USERNAME = os.environ.get("MEDISLOT_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("MEDISLOT_ADMIN_PASSWORD", "MediSlot@123")
DEBUG = os.environ.get("MEDISLOT_DEBUG", "0") == "1"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "medislot-dev-secret")
app.config["DATABASE"] = DATABASE_PATH
app.config["APPOINTMENTS_FILE"] = BASE_DIR / "data" / "appointments.json"


def get_db():
    """Open one SQLite connection per request."""
    if "db" not in g:
        app.config["DATABASE"].parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row

    return g.db


def init_db():
    """Create the patients table when it does not exist yet."""
    database = get_db()
    database.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    database.commit()


@app.teardown_appcontext
def close_db(_error=None):
    database = g.pop("db", None)

    if database is not None:
        database.close()


def wants_json_response():
    return request.is_json


def get_payload():
    if request.is_json:
        return request.get_json(silent=True) or {}

    return request.form


def json_error(message, status_code):
    return jsonify({"ok": False, "error": message}), status_code


def ensure_appointments_storage():
    appointments_file = app.config["APPOINTMENTS_FILE"]
    appointments_file.parent.mkdir(parents=True, exist_ok=True)

    if not appointments_file.exists():
        appointments_file.write_text("[]", encoding="utf-8")


def load_booking_appointments():
    ensure_appointments_storage()

    try:
        appointments = json.loads(
            app.config["APPOINTMENTS_FILE"].read_text(encoding="utf-8")
        )
    except json.JSONDecodeError:
        appointments = []

    return appointments if isinstance(appointments, list) else []


def save_booking_appointments(appointments):
    ensure_appointments_storage()
    app.config["APPOINTMENTS_FILE"].write_text(
        json.dumps(appointments, indent=2),
        encoding="utf-8",
    )


def filter_booking_appointments(appointments, query):
    doctor_id = query.get("doctor_id", [None])[0]
    clinic_id = query.get("clinic_id", [None])[0]
    date = query.get("date", [None])[0]

    filtered = appointments

    if doctor_id:
        filtered = [item for item in filtered if item["doctorId"] == doctor_id]

    if clinic_id:
        filtered = [item for item in filtered if item["clinicId"] == clinic_id]

    if date:
        filtered = [item for item in filtered if item["date"] == date]

    return filtered


def find_patient_by_email(email):
    return get_db().execute(
        "SELECT * FROM patients WHERE email = ?",
        (email,),
    ).fetchone()


def find_patient_by_id(patient_id):
    return get_db().execute(
        "SELECT * FROM patients WHERE id = ?",
        (patient_id,),
    ).fetchone()


def validate_registration(payload):
    """Validate registration data and return cleaned values plus an error."""
    name = str(payload.get("name") or payload.get("full_name") or "").strip()
    email = str(payload.get("email") or "").strip().lower()
    phone = str(payload.get("phone") or payload.get("phone_number") or "").strip()
    password = str(payload.get("password") or "")
    confirm_password = str(
        payload.get("confirm_password")
        or payload.get("confirmPassword")
        or ""
    )

    if not name:
        return None, "Full name is required."

    if not EMAIL_PATTERN.match(email):
        return None, "Please enter a valid email address."

    if not PHONE_PATTERN.match(phone):
        return None, "Please enter a valid phone number."

    if len(password) < 6:
        return None, "Password must be at least 6 characters long."

    if confirm_password and password != confirm_password:
        return None, "Password and confirm password must match."

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "password": password,
    }, None


def validate_login(payload):
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")

    if not EMAIL_PATTERN.match(email):
        return None, "Please enter a valid email address."

    if not password:
        return None, "Password is required."

    return {"email": email, "password": password}, None


@app.before_request
def load_logged_in_patient():
    patient_id = session.get("patient_id")
    g.current_patient = find_patient_by_id(patient_id) if patient_id else None


@app.context_processor
def inject_current_patient():
    return {"current_patient": g.get("current_patient")}


def resolve_next_target(candidate, fallback):
    target = str(candidate or "").strip()
    return target if target.startswith("/") and not target.startswith("//") else fallback


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.current_patient is None:
            flash("Please sign in to access your dashboard.", "error")
            next_target = resolve_next_target(
                request.full_path.rstrip("?"),
                url_for("dashboard"),
            )
            return redirect(url_for("login", next=next_target))

        return view(*args, **kwargs)

    return wrapped_view


def patient_api_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.current_patient is None:
            return json_error("Please sign in to continue.", 401)

        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("admin_username") is None:
            next_target = resolve_next_target(
                request.full_path.rstrip("?"),
                url_for("admin_dashboard"),
            )
            return redirect(url_for("admin_login_page", next=next_target))

        return view(*args, **kwargs)

    return wrapped_view


def admin_api_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("admin_username") is None:
            return json_error("Authentication required.", 401)

        return view(*args, **kwargs)

    return wrapped_view


def is_valid_admin_credentials(username, password):
    return (
        secrets.compare_digest(username, ADMIN_USERNAME)
        and secrets.compare_digest(password, ADMIN_PASSWORD)
    )


def appointment_matches_patient(appointment, patient):
    patient_id = appointment.get("patientId")
    patient_email = str(appointment.get("patientEmail", "")).strip().lower()

    if patient_id == patient["id"]:
        return True

    if patient_email and patient_email == patient["email"]:
        return True

    return (
        appointment.get("patientName") == patient["name"]
        and appointment.get("phone") == patient["phone"]
    )


def patient_appointments(patient):
    return [
        appointment
        for appointment in load_booking_appointments()
        if appointment_matches_patient(appointment, patient)
    ]


def find_patient_appointment(appointment_id, patient):
    return next(
        (
            appointment
            for appointment in patient_appointments(patient)
            if appointment["id"] == appointment_id
        ),
        None,
    )


def create_patient_appointment(payload, patient):
    doctor_id = str(payload.get("doctorId", "")).strip()
    date = str(payload.get("date", "")).strip()
    time = str(payload.get("time", "")).strip()

    doctor = doctor_by_id(doctor_id)
    if not doctor:
        raise ValueError("Please select a valid doctor.")

    clinic = clinic_by_id(doctor["clinic_id"])
    if not clinic:
        raise ValueError("Unable to resolve the clinic for this doctor.")

    if not DATE_PATTERN.match(date):
        raise ValueError("Please select a valid appointment date.")

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as error:
        raise ValueError("Please select a valid appointment date.") from error

    if time not in doctor["time_slots"]:
        raise ValueError("Please choose a valid time slot.")

    appointments = load_booking_appointments()
    already_booked = any(
        item["doctorId"] == doctor_id and item["date"] == date and item["time"] == time
        for item in appointments
    )

    if already_booked:
        raise SlotTakenError("This slot has already been booked. Please choose another one.")

    appointment = {
        "id": f"APT-{int(datetime.utcnow().timestamp() * 1000)}-{len(appointments) + 1}",
        "patientId": patient["id"],
        "patientName": patient["name"],
        "patientEmail": patient["email"],
        "phone": patient["phone"],
        "doctorId": doctor["id"],
        "doctorName": doctor["name"],
        "doctorType": doctor["type"],
        "clinicId": clinic["id"],
        "clinicName": clinic["name"],
        "city": clinic["city"],
        "area": clinic["area"],
        "location": f'{clinic["city"]}, {clinic["area"]}',
        "date": date,
        "time": time,
        "bookedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }

    appointments.append(appointment)
    save_booking_appointments(appointments)
    return appointment


@app.route("/")
@app.route("/index.html")
def home():
    return render_template("index.html")


@app.get("/doctors.html")
def doctors_page():
    return render_template("doctors.html")


@app.get("/locations.html")
def locations_page():
    return render_template("locations.html")


@app.get("/contact.html")
def contact_page():
    return render_template("contact.html")


@app.get("/confirmation.html")
def legacy_confirmation_page():
    return render_template("confirmation.html")


@app.get("/book.html")
def legacy_book_redirect():
    next_target = "/book"
    query_string = request.query_string.decode("utf-8").strip()

    if query_string:
        next_target = f"{next_target}?{query_string}"

    return redirect(next_target)


@app.get("/sign-in")
@app.get("/sign-in.html")
@app.get("/signin")
@app.get("/signin.html")
@app.get("/user-login")
@app.get("/user-login.html")
def legacy_sign_in_redirect():
    next_target = request.args.get("next")
    return redirect(url_for("login", next=next_target) if next_target else url_for("login"))


@app.get("/admin-login.html")
@app.get("/login.html")
def admin_login_page():
    if session.get("admin_username"):
        return redirect(url_for("admin_dashboard"))

    return render_template("admin-login.html")


@app.get("/admin.html")
@admin_required
def admin_dashboard():
    return render_template("admin.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET" and g.current_patient is not None:
        return redirect(url_for("dashboard"))

    form_values = {"name": "", "email": "", "phone": ""}
    page_error = None

    if request.method == "POST":
        payload = get_payload()
        cleaned_data, page_error = validate_registration(payload)
        form_values = {
            "name": str(payload.get("name") or payload.get("full_name") or "").strip(),
            "email": str(payload.get("email") or "").strip().lower(),
            "phone": str(payload.get("phone") or payload.get("phone_number") or "").strip(),
        }

        if page_error:
            if wants_json_response():
                return json_error(page_error, 400)

            return render_template(
                "register.html",
                form_values=form_values,
                page_error=page_error,
            ), 400

        if find_patient_by_email(cleaned_data["email"]):
            page_error = "An account with this email already exists."

            if wants_json_response():
                return json_error(page_error, 409)

            return render_template(
                "register.html",
                form_values=form_values,
                page_error=page_error,
            ), 409

        get_db().execute(
            """
            INSERT INTO patients (name, email, phone, password)
            VALUES (?, ?, ?, ?)
            """,
            (
                cleaned_data["name"],
                cleaned_data["email"],
                cleaned_data["phone"],
                generate_password_hash(cleaned_data["password"]),
            ),
        )
        get_db().commit()

        if wants_json_response():
            return jsonify(
                {
                    "ok": True,
                    "message": "Registration successful.",
                    "redirect": url_for("login"),
                }
            ), 201

        flash("Registration successful. Please sign in to continue.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", form_values=form_values, page_error=page_error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET" and g.current_patient is not None:
        return redirect(resolve_next_target(request.args.get("next"), url_for("dashboard")))

    form_values = {"email": ""}
    page_error = None

    if request.method == "POST":
        payload = get_payload()
        cleaned_data, page_error = validate_login(payload)
        next_target = resolve_next_target(
            payload.get("next") or request.args.get("next"),
            url_for("dashboard"),
        )
        form_values = {
            "email": str(payload.get("email") or "").strip().lower(),
        }

        if page_error:
            if wants_json_response():
                return json_error(page_error, 400)

            return render_template(
                "login.html",
                form_values=form_values,
                page_error=page_error,
            ), 400

        patient = find_patient_by_email(cleaned_data["email"])

        if patient is None or not check_password_hash(patient["password"], cleaned_data["password"]):
            page_error = "Invalid email or password."

            if wants_json_response():
                return json_error(page_error, 401)

            return render_template(
                "login.html",
                form_values=form_values,
                page_error=page_error,
            ), 401

        session.clear()
        session["patient_id"] = patient["id"]

        if wants_json_response():
            return jsonify(
                {
                    "ok": True,
                    "message": "Login successful.",
                    "redirect": next_target,
                    "patient": {
                        "id": patient["id"],
                        "name": patient["name"],
                        "email": patient["email"],
                        "phone": patient["phone"],
                    },
                }
            )

        flash(f"Welcome back, {patient['name']}!", "success")
        return redirect(next_target)

    return render_template("login.html", form_values=form_values, page_error=page_error)


@app.get("/dashboard")
@login_required
def dashboard():
    appointments = sorted(
        patient_appointments(g.current_patient),
        key=lambda item: item["bookedAt"],
        reverse=True,
    )[:4]
    return render_template("dashboard.html", appointments=appointments)


@app.get("/book")
@login_required
def book():
    return render_template("patient-book.html")


@app.get("/confirmation")
@login_required
def booking_confirmation():
    appointment_id = str(request.args.get("id", "")).strip()
    appointment = (
        find_patient_appointment(appointment_id, g.current_patient)
        if appointment_id
        else None
    )
    return render_template(
        "patient-confirmation.html",
        appointment=appointment,
        appointment_id=appointment_id,
    )


@app.get("/api/bootstrap")
def api_bootstrap():
    return jsonify(
        {
            "doctors": [serialize_doctor(doctor) for doctor in DOCTORS],
            "clinics": [serialize_clinic(clinic) for clinic in CLINICS],
        }
    )


@app.get("/api/stats")
def api_stats():
    appointments = load_booking_appointments()
    return jsonify(
        {
            "doctorCount": len(DOCTORS),
            "clinicCount": len(CLINICS),
            "appointmentCount": len(appointments),
        }
    )


@app.get("/api/activity")
def api_activity():
    appointments = sorted(
        load_booking_appointments(),
        key=lambda item: item["bookedAt"],
        reverse=True,
    )
    return jsonify([serialize_activity_entry(item) for item in appointments[:4]])


@app.get("/api/patient/session")
def api_patient_session():
    return jsonify(
        {
            "authenticated": g.current_patient is not None,
            "patient": (
                {
                    "id": g.current_patient["id"],
                    "name": g.current_patient["name"],
                    "email": g.current_patient["email"],
                    "phone": g.current_patient["phone"],
                }
                if g.current_patient is not None
                else None
            ),
        }
    )


@app.get("/api/patient/appointments")
@patient_api_required
def api_patient_appointments():
    appointments = sorted(
        patient_appointments(g.current_patient),
        key=lambda item: item["bookedAt"],
        reverse=True,
    )
    return jsonify([serialize_activity_entry(item) for item in appointments])


@app.get("/api/availability")
def api_availability():
    query = request.args.to_dict(flat=False)
    appointments = filter_booking_appointments(load_booking_appointments(), query)
    return jsonify([serialize_availability_entry(item) for item in appointments])


@app.get("/api/doctors")
def api_doctors():
    return jsonify([serialize_doctor(doctor) for doctor in DOCTORS])


@app.get("/api/clinics")
def api_clinics():
    return jsonify([serialize_clinic(clinic) for clinic in CLINICS])


@app.route("/api/appointments", methods=["GET", "POST"])
def api_appointments():
    if request.method == "GET":
        if session.get("admin_username") is None:
            return json_error("Authentication required.", 401)

        query = request.args.to_dict(flat=False)
        appointments = filter_booking_appointments(load_booking_appointments(), query)
        return jsonify(appointments)

    if g.current_patient is None:
        return json_error("Please sign in to continue.", 401)

    payload = request.get_json(silent=True)

    if payload is None:
        return json_error("Invalid JSON payload.", 400)

    try:
        appointment = create_patient_appointment(payload, g.current_patient)
    except SlotTakenError as error:
        return json_error(str(error), 409)
    except ValueError as error:
        return json_error(str(error), 400)

    return jsonify(serialize_confirmation_entry(appointment)), 201


@app.get("/api/appointments/<appointment_id>")
@admin_api_required
def api_appointment_detail(appointment_id):
    appointment = next(
        (
            item
            for item in load_booking_appointments()
            if item["id"] == appointment_id
        ),
        None,
    )

    if appointment is None:
        return json_error("Appointment not found.", 404)

    return jsonify(appointment)


@app.get("/api/confirmation")
def api_confirmation_query():
    appointment_id = str(request.args.get("id", "")).strip()
    appointment = next(
        (
            item
            for item in load_booking_appointments()
            if item["id"] == appointment_id
        ),
        None,
    )

    if appointment is None:
        return json_error("Appointment not found.", 404)

    return jsonify(serialize_confirmation_entry(appointment))


@app.get("/api/confirmation/<appointment_id>")
def api_confirmation(appointment_id):
    appointment = next(
        (
            item
            for item in load_booking_appointments()
            if item["id"] == appointment_id
        ),
        None,
    )

    if appointment is None:
        return json_error("Appointment not found.", 404)

    return jsonify(serialize_confirmation_entry(appointment))


@app.get("/api/admin/session")
def api_admin_session():
    username = session.get("admin_username")
    return jsonify(
        {
            "authenticated": bool(username),
            "username": username,
        }
    )


@app.post("/api/admin/login")
def api_admin_login():
    payload = request.get_json(silent=True)

    if payload is None:
        return json_error("Invalid JSON payload.", 400)

    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))

    if not username or not password:
        return json_error("Username and password are required.", 400)

    if not is_valid_admin_credentials(username, password):
        return json_error("Invalid username or password.", 401)

    session["admin_username"] = username
    return jsonify({"ok": True, "username": username})


@app.post("/api/admin/logout")
def api_admin_logout():
    session.pop("admin_username", None)
    return jsonify({"ok": True})


@app.get("/api/admin/appointments")
@admin_api_required
def api_admin_appointments():
    return jsonify(load_booking_appointments())


@app.route("/logout", methods=["GET", "POST"])
def logout():
    was_admin = session.get("admin_username") is not None
    session.clear()

    if request.method == "GET" and was_admin:
        return redirect(url_for("admin_login_page"))

    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


with app.app_context():
    init_db()


def run():
    app.run(debug=DEBUG, port=PORT)


if __name__ == "__main__":
    run()
