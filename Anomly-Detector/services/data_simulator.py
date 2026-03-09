import random
import numpy as np
from datetime import datetime, timezone


class DataSimulator:
    """
    Generates realistic patient vital sign readings with occasional
    anomaly injection to test the detection system.
    """

    PATIENT_IDS = ["P001", "P002", "P003", "P004", "P005"]

    # Normal ranges per vital
    NORMAL = {
        "heart_rate":   {"mean": 75,    "std": 8},
        "spo2":         {"mean": 97,    "std": 1.2},
        "temperature":  {"mean": 37.0,  "std": 0.3},
        "systolic_bp":  {"mean": 120,   "std": 10},
        "diastolic_bp": {"mean": 78,    "std": 7},
    }

    # Anomalous shift ranges
    ANOMALOUS = {
        "heart_rate":   {"mean": 115,   "std": 15},   # tachycardia
        "spo2":         {"mean": 89,    "std": 3},     # hypoxemia
        "temperature":  {"mean": 39.2,  "std": 0.6},   # fever
        "systolic_bp":  {"mean": 160,   "std": 15},    # hypertension
        "diastolic_bp": {"mean": 100,   "std": 10},
    }

    def __init__(self, anomaly_rate=0.20):
        self.anomaly_rate = anomaly_rate

    def generate_reading(self, patient_id=None):
        """Generate a single vital sign reading."""
        if patient_id is None:
            patient_id = random.choice(self.PATIENT_IDS)

        is_anomalous = random.random() < self.anomaly_rate

        if is_anomalous:
            # Pick 1-3 vitals to make anomalous
            anomaly_count = random.randint(1, 3)
            anomalous_keys = random.sample(list(self.NORMAL.keys()), anomaly_count)
        else:
            anomalous_keys = []

        vitals = {}
        for key, normal in self.NORMAL.items():
            if key in anomalous_keys:
                params = self.ANOMALOUS[key]
            else:
                params = normal
            value = np.random.normal(params["mean"], params["std"])

            # Clamp to reasonable ranges
            if key == "heart_rate":
                value = max(40, min(180, value))
            elif key == "spo2":
                value = max(70, min(100, value))
            elif key == "temperature":
                value = max(35.0, min(42.0, value))
            elif key == "systolic_bp":
                value = max(80, min(220, value))
            elif key == "diastolic_bp":
                value = max(40, min(140, value))

            vitals[key] = round(value, 1)

        return {
            "patient_id": patient_id,
            **vitals,
            "timestamp": datetime.now(timezone.utc),
        }

    def generate_batch(self, count=5):
        """Generate readings for all patients."""
        readings = []
        for pid in self.PATIENT_IDS[:count]:
            readings.append(self.generate_reading(pid))
        return readings


simulator = DataSimulator()
