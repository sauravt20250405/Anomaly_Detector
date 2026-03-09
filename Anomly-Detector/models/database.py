from datetime import datetime, timezone

# --- Global Data Store (The "In-Memory" Database) ---
class Storage:
    def __init__(self):
        self.patients = []
        self.vital_signs = []
        self.alerts = []

# This acts as our live database instance
db_storage = Storage()

class Patient:
    def __init__(self, id, name, age, room, status="Stable"):
        self.id = id
        self.name = name
        self.age = age
        self.room = room
        self.status = status
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "room": self.room,
            "status": self.status,
        }

class VitalSign:
    def __init__(self, patient_id, heart_rate, spo2, temperature, systolic_bp, diastolic_bp):
        self.id = len(db_storage.vital_signs) + 1
        self.patient_id = patient_id
        self.heart_rate = heart_rate
        self.spo2 = spo2
        self.temperature = temperature
        self.systolic_bp = systolic_bp
        self.diastolic_bp = diastolic_bp
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "heart_rate": round(self.heart_rate, 1),
            "spo2": round(self.spo2, 1),
            "temperature": round(self.temperature, 1),
            "bp": f"{round(self.systolic_bp)}/{round(self.diastolic_bp)}",
            "timestamp": self.timestamp.strftime("%m/%d/%Y, %I:%M:%S %p"),
        }

class Alert:
    def __init__(self, patient_id, anomaly_score, severity, hr=None, spo2=None, temp=None, sys=None, dia=None):
        self.id = len(db_storage.alerts) + 1
        self.patient_id = patient_id
        self.anomaly_score = anomaly_score
        self.severity = severity
        self.heart_rate = hr
        self.spo2 = spo2
        self.temperature = temp
        self.systolic_bp = sys
        self.diastolic_bp = dia
        self.acknowledged = False
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "anomaly_score": round(self.anomaly_score, 1),
            "severity": self.severity,
            "heart_rate": f"{round(self.heart_rate, 1)} bpm" if self.heart_rate else "—",
            "spo2": f"{round(self.spo2)}%" if self.spo2 else "—",
            "temperature": f"{round(self.temperature, 1)}°C" if self.temperature else "—",
            "bp": f"{round(self.systolic_bp)}/{round(self.diastolic_bp)}" if self.systolic_bp else "—",
            "acknowledged": self.acknowledged,
            "timestamp": self.timestamp.strftime("%m/%d/%Y, %I:%M:%S %p"),
            "timestamp_iso": self.timestamp.isoformat(),
        }

# --- Database Mock Functions ---
def seed_patients():
    """Seeds patients into the global list if empty."""
    if not db_storage.patients:
        patients_data = [
            ("P001", "Eleanor Vance", 67, "ICU-101", "Stable"),
            ("P002", "Marcus Chen", 45, "ICU-102", "Stable"),
            ("P003", "Sarah Mitchell", 72, "ICU-103", "Warning"),
            ("P004", "James Rodriguez", 58, "Ward-204", "Stable"),
            ("P005", "Priya Patel", 34, "Ward-205", "Stable"),
        ]
        for pid, name, age, room, status in patients_data:
            db_storage.patients.append(Patient(pid, name, age, room, status))
        print("[DB-MOCK] Seeded 5 patients into memory.")

# Add this method to your existing Storage class in models/database.py
def add_patient(self, name, age, room):
    new_id = f"P{len(self.patients) + 1:03d}"
    new_p = Patient(new_id, name, age, room)
    self.patients.append(new_p)
    return new_p

# This empty object prevents app.py from crashing when it tries to call db.init_app()
class MockDB:
    def init_app(self, app): pass
    def create_all(self): pass

db = MockDB()