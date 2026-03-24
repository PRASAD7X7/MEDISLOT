import json
import os
import re
import secrets
import time
from datetime import datetime
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
APPOINTMENTS_FILE = DATA_DIR / "appointments.json"
PORT = int(os.environ.get("MEDISLOT_PORT", "8000"))
ADMIN_USERNAME = os.environ.get("MEDISLOT_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("MEDISLOT_ADMIN_PASSWORD", "MediSlot@123")
SESSION_COOKIE_NAME = "medislot_admin_session"
SESSION_TTL_SECONDS = int(os.environ.get("MEDISLOT_SESSION_TTL", "28800"))
SESSIONS = {}

PAGE_ROUTES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/doctors.html": "doctors.html",
    "/book.html": "book.html",
    "/locations.html": "locations.html",
    "/contact.html": "contact.html",
    "/confirmation.html": "confirmation.html",
    "/admin.html": "admin.html",
    "/login.html": "login.html",
}

MIME_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}

PHONE_PATTERN = re.compile(r"^[0-9+\-\s]{7,20}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

CLINICS = [
    {
        "id": "clinic-andheri",
        "name": "MediCare Central",
        "city": "Mumbai",
        "area": "Andheri East",
        "address": "102 Sunrise Plaza, Andheri East, Mumbai",
        "phone": "+91 22 4100 2201",
        "hours": "Mon-Sat, 8:00 AM - 8:00 PM",
    },
    {
        "id": "clinic-bandra",
        "name": "Heartline Clinic",
        "city": "Mumbai",
        "area": "Bandra West",
        "address": "18 Seabreeze Avenue, Bandra West, Mumbai",
        "phone": "+91 22 4100 3344",
        "hours": "Mon-Sat, 9:00 AM - 7:00 PM",
    },
    {
        "id": "clinic-kothrud",
        "name": "SmileCraft Dental",
        "city": "Pune",
        "area": "Kothrud",
        "address": "45 Green Arcade, Kothrud, Pune",
        "phone": "+91 20 4455 9200",
        "hours": "Mon-Sat, 9:30 AM - 6:30 PM",
    },
    {
        "id": "clinic-indiranagar",
        "name": "OrthoPlus Center",
        "city": "Bengaluru",
        "area": "Indiranagar",
        "address": "9 Lake View Road, Indiranagar, Bengaluru",
        "phone": "+91 80 4412 1008",
        "hours": "Mon-Sat, 8:30 AM - 7:30 PM",
    },
    {
        "id": "clinic-banjara",
        "name": "Little Steps Clinic",
        "city": "Hyderabad",
        "area": "Banjara Hills",
        "address": "221 Park Lane, Banjara Hills, Hyderabad",
        "phone": "+91 40 3344 1188",
        "hours": "Mon-Sat, 9:00 AM - 8:00 PM",
    },
    {
        "id": "clinic-anna-nagar",
        "name": "SkinSense Clinic",
        "city": "Chennai",
        "area": "Anna Nagar",
        "address": "14 North Avenue, Anna Nagar, Chennai",
        "phone": "+91 44 2877 4520",
        "hours": "Mon-Sat, 10:00 AM - 7:00 PM",
    },
    {
        "id": "clinic-saket",
        "name": "NeuroCare Hub",
        "city": "Delhi",
        "area": "Saket",
        "address": "32 Health Square, Saket, New Delhi",
        "phone": "+91 11 4188 9044",
        "hours": "Mon-Sat, 8:00 AM - 6:00 PM",
    },
    {
        "id": "clinic-edappally",
        "name": "Bloom Women's Care",
        "city": "Kochi",
        "area": "Edappally",
        "address": "7 Riverfront Complex, Edappally, Kochi",
        "phone": "+91 48 4291 7766",
        "hours": "Mon-Sat, 9:00 AM - 6:00 PM",
    },
]

DOCTORS = [
    {
        "id": "doc-aisha-khan",
        "name": "Dr. Aisha Khan",
        "type": "General Physician",
        "clinic_id": "clinic-andheri",
        "experience": "12 years",
        "time_slots": ["09:00 AM", "10:30 AM", "12:00 PM", "03:00 PM", "05:00 PM"],
    },
    {
        "id": "doc-rohan-mehta",
        "name": "Dr. Rohan Mehta",
        "type": "Cardiologist",
        "clinic_id": "clinic-bandra",
        "experience": "15 years",
        "time_slots": ["09:30 AM", "11:00 AM", "01:00 PM", "04:00 PM", "06:00 PM"],
    },
    {
        "id": "doc-neha-patel",
        "name": "Dr. Neha Patel",
        "type": "Dentist",
        "clinic_id": "clinic-kothrud",
        "experience": "9 years",
        "time_slots": ["10:00 AM", "11:30 AM", "01:30 PM", "03:30 PM", "05:30 PM"],
    },
    {
        "id": "doc-arjun-rao",
        "name": "Dr. Arjun Rao",
        "type": "Orthopedic",
        "clinic_id": "clinic-indiranagar",
        "experience": "14 years",
        "time_slots": ["08:30 AM", "10:00 AM", "12:30 PM", "03:00 PM", "05:00 PM"],
    },
    {
        "id": "doc-sana-sheikh",
        "name": "Dr. Sana Sheikh",
        "type": "Pediatrician",
        "clinic_id": "clinic-banjara",
        "experience": "11 years",
        "time_slots": ["09:00 AM", "10:00 AM", "12:00 PM", "02:30 PM", "04:30 PM"],
    },
    {
        "id": "doc-vikram-iyer",
        "name": "Dr. Vikram Iyer",
        "type": "Dermatologist",
        "clinic_id": "clinic-anna-nagar",
        "experience": "10 years",
        "time_slots": ["10:00 AM", "11:00 AM", "01:00 PM", "03:00 PM", "06:00 PM"],
    },
    {
        "id": "doc-kabir-singh",
        "name": "Dr. Kabir Singh",
        "type": "Neurologist",
        "clinic_id": "clinic-saket",
        "experience": "16 years",
        "time_slots": ["08:00 AM", "09:30 AM", "11:30 AM", "02:00 PM", "04:30 PM"],
    },
    {
        "id": "doc-priya-nair",
        "name": "Dr. Priya Nair",
        "type": "Gynecologist",
        "clinic_id": "clinic-edappally",
        "experience": "13 years",
        "time_slots": ["09:30 AM", "11:30 AM", "01:30 PM", "03:30 PM", "05:00 PM"],
    },
]


class SlotTakenError(Exception):
    pass


def ensure_storage():
    APPOINTMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not APPOINTMENTS_FILE.exists():
        APPOINTMENTS_FILE.write_text("[]", encoding="utf-8")


def load_appointments():
    ensure_storage()

    try:
        appointments = json.loads(APPOINTMENTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        appointments = []

    return appointments if isinstance(appointments, list) else []


def save_appointments(appointments):
    ensure_storage()
    APPOINTMENTS_FILE.write_text(
        json.dumps(appointments, indent=2),
        encoding="utf-8",
    )


def clinic_by_id(clinic_id):
    return next((clinic for clinic in CLINICS if clinic["id"] == clinic_id), None)


def doctor_by_id(doctor_id):
    return next((doctor for doctor in DOCTORS if doctor["id"] == doctor_id), None)


def serialize_clinic(clinic):
    doctor_count = sum(1 for doctor in DOCTORS if doctor["clinic_id"] == clinic["id"])
    return {
        **clinic,
        "doctorCount": doctor_count,
    }


def serialize_doctor(doctor):
    clinic = clinic_by_id(doctor["clinic_id"])
    return {
        "id": doctor["id"],
        "name": doctor["name"],
        "type": doctor["type"],
        "clinicId": doctor["clinic_id"],
        "clinicName": clinic["name"] if clinic else "",
        "city": clinic["city"] if clinic else "",
        "area": clinic["area"] if clinic else "",
        "address": clinic["address"] if clinic else "",
        "phone": clinic["phone"] if clinic else "",
        "hours": clinic["hours"] if clinic else "",
        "experience": doctor["experience"],
        "timeSlots": doctor["time_slots"],
    }


def serialize_availability_entry(appointment):
    return {
        "doctorId": appointment["doctorId"],
        "clinicId": appointment["clinicId"],
        "date": appointment["date"],
        "time": appointment["time"],
    }


def serialize_activity_entry(appointment):
    return {
        "id": appointment["id"],
        "doctorName": appointment["doctorName"],
        "doctorType": appointment["doctorType"],
        "clinicName": appointment["clinicName"],
        "location": appointment["location"],
        "date": appointment["date"],
        "time": appointment["time"],
        "bookedAt": appointment["bookedAt"],
    }


def serialize_confirmation_entry(appointment):
    return {
        "id": appointment["id"],
        "doctorName": appointment["doctorName"],
        "doctorType": appointment["doctorType"],
        "clinicName": appointment["clinicName"],
        "location": appointment["location"],
        "date": appointment["date"],
        "time": appointment["time"],
    }


def filter_appointments(appointments, query):
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


def load_body(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length else b"{}"
    return json.loads(raw.decode("utf-8"))


def cleanup_sessions():
    now = time.time()
    expired_tokens = [
        token
        for token, session in SESSIONS.items()
        if session["expiresAt"] <= now
    ]

    for token in expired_tokens:
        SESSIONS.pop(token, None)


def create_session(username):
    cleanup_sessions()
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = {
        "username": username,
        "expiresAt": time.time() + SESSION_TTL_SECONDS,
    }
    return token


def delete_session(token):
    if token:
        SESSIONS.pop(token, None)


def is_valid_admin_credentials(username, password):
    return (
        secrets.compare_digest(username, ADMIN_USERNAME)
        and secrets.compare_digest(password, ADMIN_PASSWORD)
    )


def validate_appointment(payload):
    patient_name = str(payload.get("patientName", "")).strip()
    phone = str(payload.get("phone", "")).strip()
    doctor_id = str(payload.get("doctorId", "")).strip()
    date = str(payload.get("date", "")).strip()
    time = str(payload.get("time", "")).strip()

    if not patient_name:
        raise ValueError("Patient name is required.")

    if not PHONE_PATTERN.match(phone):
        raise ValueError("Please enter a valid phone number.")

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

    appointments = load_appointments()
    already_booked = any(
        item["doctorId"] == doctor_id and item["date"] == date and item["time"] == time
        for item in appointments
    )

    if already_booked:
        raise SlotTakenError("This slot has already been booked. Please choose another one.")

    appointment = {
        "id": f"APT-{int(datetime.utcnow().timestamp() * 1000)}-{len(appointments) + 1}",
        "patientName": patient_name,
        "phone": phone,
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
    save_appointments(appointments)
    return appointment


class MediSlotHandler(BaseHTTPRequestHandler):
    server_version = "MediSlotServer/1.1"

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path.startswith("/api/"):
            self.handle_api_get(parsed)
            return

        if parsed.path == "/logout":
            self.handle_logout()
            return

        self.handle_page_or_static(parsed)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/appointments":
            self.handle_public_booking()
            return

        if parsed.path == "/api/admin/login":
            self.handle_admin_login()
            return

        if parsed.path == "/api/admin/logout":
            self.handle_admin_logout()
            return

        self.send_json({"error": "Route not found."}, HTTPStatus.NOT_FOUND)

    def parse_cookies(self):
        cookies = SimpleCookie()
        raw_header = self.headers.get("Cookie")

        if raw_header:
            cookies.load(raw_header)

        return {
            key: morsel.value
            for key, morsel in cookies.items()
        }

    def current_session(self):
        cleanup_sessions()
        token = self.parse_cookies().get(SESSION_COOKIE_NAME)

        if not token:
            return None

        session = SESSIONS.get(token)

        if not session:
            return None

        if session["expiresAt"] <= time.time():
            delete_session(token)
            return None

        session["expiresAt"] = time.time() + SESSION_TTL_SECONDS
        return {
            "token": token,
            "username": session["username"],
            "expiresAt": session["expiresAt"],
        }

    def require_admin_session(self):
        session = self.current_session()

        if not session:
            self.send_json({"error": "Authentication required."}, HTTPStatus.UNAUTHORIZED)
            return None

        return session

    def session_cookie_value(self, token, max_age):
        return (
            f"{SESSION_COOKIE_NAME}={token}; "
            f"Path=/; Max-Age={max_age}; HttpOnly; SameSite=Lax"
        )

    def send_redirect(self, location, extra_headers=None, status=HTTPStatus.SEE_OTHER):
        self.send_response(status)

        for key, value in extra_headers or []:
            self.send_header(key, value)

        self.send_header("Location", location)
        self.end_headers()

    def handle_logout(self):
        session = self.current_session()

        if session:
            delete_session(session["token"])

        self.send_redirect(
            "/login.html",
            extra_headers=[
                ("Set-Cookie", self.session_cookie_value("expired", 0)),
            ],
        )

    def handle_public_booking(self):
        try:
            payload = load_body(self)
            appointment = validate_appointment(payload)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
            return
        except SlotTakenError as error:
            self.send_json({"error": str(error)}, HTTPStatus.CONFLICT)
            return
        except ValueError as error:
            self.send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        self.send_json(serialize_confirmation_entry(appointment), HTTPStatus.CREATED)

    def handle_admin_login(self):
        try:
            payload = load_body(self)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON payload."}, HTTPStatus.BAD_REQUEST)
            return

        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", ""))

        if not username or not password:
            self.send_json(
                {"error": "Username and password are required."},
                HTTPStatus.BAD_REQUEST,
            )
            return

        if not is_valid_admin_credentials(username, password):
            self.send_json(
                {"error": "Invalid username or password."},
                HTTPStatus.UNAUTHORIZED,
            )
            return

        token = create_session(username)
        self.send_json(
            {"ok": True, "username": username},
            HTTPStatus.OK,
            extra_headers=[
                ("Set-Cookie", self.session_cookie_value(token, SESSION_TTL_SECONDS)),
            ],
        )

    def handle_admin_logout(self):
        session = self.current_session()

        if session:
            delete_session(session["token"])

        self.send_json(
            {"ok": True},
            HTTPStatus.OK,
            extra_headers=[
                ("Set-Cookie", self.session_cookie_value("expired", 0)),
            ],
        )

    def handle_api_get(self, parsed):
        if parsed.path == "/api/bootstrap":
            self.send_json(
                {
                    "doctors": [serialize_doctor(doctor) for doctor in DOCTORS],
                    "clinics": [serialize_clinic(clinic) for clinic in CLINICS],
                }
            )
            return

        if parsed.path == "/api/stats":
            appointments = load_appointments()
            self.send_json(
                {
                    "doctorCount": len(DOCTORS),
                    "clinicCount": len(CLINICS),
                    "appointmentCount": len(appointments),
                }
            )
            return

        if parsed.path == "/api/activity":
            appointments = sorted(
                load_appointments(),
                key=lambda item: item["bookedAt"],
                reverse=True,
            )
            self.send_json([serialize_activity_entry(item) for item in appointments[:4]])
            return

        if parsed.path == "/api/availability":
            query = parse_qs(parsed.query)
            appointments = filter_appointments(load_appointments(), query)
            self.send_json([serialize_availability_entry(item) for item in appointments])
            return

        if parsed.path == "/api/doctors":
            self.send_json([serialize_doctor(doctor) for doctor in DOCTORS])
            return

        if parsed.path == "/api/clinics":
            self.send_json([serialize_clinic(clinic) for clinic in CLINICS])
            return

        if parsed.path == "/api/confirmation":
            appointment_id = parse_qs(parsed.query).get("id", [None])[0]
            appointment = next(
                (
                    item
                    for item in load_appointments()
                    if item["id"] == appointment_id
                ),
                None,
            )

            if not appointment:
                self.send_json({"error": "Appointment not found."}, HTTPStatus.NOT_FOUND)
                return

            self.send_json(serialize_confirmation_entry(appointment))
            return

        if parsed.path.startswith("/api/confirmation/"):
            appointment_id = unquote(parsed.path.rsplit("/", 1)[-1])
            appointment = next(
                (
                    item
                    for item in load_appointments()
                    if item["id"] == appointment_id
                ),
                None,
            )

            if not appointment:
                self.send_json({"error": "Appointment not found."}, HTTPStatus.NOT_FOUND)
                return

            self.send_json(serialize_confirmation_entry(appointment))
            return

        if parsed.path == "/api/admin/session":
            session = self.current_session()
            self.send_json(
                {
                    "authenticated": bool(session),
                    "username": session["username"] if session else None,
                }
            )
            return

        if parsed.path == "/api/admin/appointments":
            if not self.require_admin_session():
                return

            self.send_json(load_appointments())
            return

        if parsed.path == "/api/appointments":
            if not self.require_admin_session():
                return

            query = parse_qs(parsed.query)
            appointments = filter_appointments(load_appointments(), query)
            self.send_json(appointments)
            return

        if parsed.path.startswith("/api/appointments/"):
            if not self.require_admin_session():
                return

            appointment_id = unquote(parsed.path.rsplit("/", 1)[-1])
            appointment = next(
                (
                    item
                    for item in load_appointments()
                    if item["id"] == appointment_id
                ),
                None,
            )

            if not appointment:
                self.send_json({"error": "Appointment not found."}, HTTPStatus.NOT_FOUND)
                return

            self.send_json(appointment)
            return

        self.send_json({"error": "Route not found."}, HTTPStatus.NOT_FOUND)

    def handle_page_or_static(self, parsed):
        path = parsed.path

        if path == "/login.html" and self.current_session():
            self.send_redirect("/admin.html")
            return

        if path == "/admin.html" and not self.current_session():
            self.send_redirect(
                f"/login.html?next={quote(path)}",
                status=HTTPStatus.FOUND,
            )
            return

        if path in PAGE_ROUTES:
            self.serve_file(TEMPLATES_DIR / PAGE_ROUTES[path])
            return

        if path.startswith("/static/"):
            relative_path = path.replace("/static/", "", 1)
            target = (STATIC_DIR / relative_path).resolve()

            try:
                target.relative_to(STATIC_DIR.resolve())
            except ValueError:
                self.send_error(HTTPStatus.FORBIDDEN, "Invalid asset path.")
                return

            self.serve_file(target)
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Page not found.")

    def serve_file(self, file_path):
        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found.")
            return

        content = file_path.read_bytes()
        mime_type = MIME_TYPES.get(file_path.suffix.lower(), "application/octet-stream")

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload, status=HTTPStatus.OK, extra_headers=None):
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)

        for key, value in extra_headers or []:
            self.send_header(key, value)

        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


def run():
    ensure_storage()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), MediSlotHandler)
    print(f"MediSlot running at http://127.0.0.1:{PORT}")
    print(f"Admin login username: {ADMIN_USERNAME}")
    print("Press Ctrl+C to stop the server.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down MediSlot.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
