# MediSlot

MediSlot now runs as a single Flask application that serves:

- the public website
- patient registration and sign in
- protected patient booking
- admin login and appointment review

## Install dependencies

```bash
pip install Flask
```

## Run the merged app

Preferred:

```bash
python app.py
```

Compatibility launcher:

```bash
python server.py
```

Or double-click:

- `start_medislot.bat`

The merged app runs on:

- `http://127.0.0.1:8000/`

## Main routes

Public pages:

- `/`
- `/index.html`
- `/doctors.html`
- `/locations.html`
- `/contact.html`

Patient authentication:

- `/register`
- `/login`
- `/dashboard`
- `/book`
- `/confirmation?id=...`

Admin:

- `/login.html`
- `/admin.html`

## Patient flow

1. Open `http://127.0.0.1:8000/register`
2. Create a patient account
3. Sign in at `http://127.0.0.1:8000/login`
4. Book an appointment at `http://127.0.0.1:8000/book`
5. View the result on `/confirmation?id=...`

## Database and storage

Patient accounts:

- SQLite database: `data/medislot_auth.db`
- Schema file: `schema.sql`

Appointments:

- JSON file: `data/appointments.json`

## Admin login

- URL: `http://127.0.0.1:8000/login.html`
- Default username: `admin`
- Default password: `MediSlot@123`

You can change the admin credentials with environment variables:

- `MEDISLOT_ADMIN_USER`
- `MEDISLOT_ADMIN_PASSWORD`

You can change the app port with:

- `MEDISLOT_PORT`
