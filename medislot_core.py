import re


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
