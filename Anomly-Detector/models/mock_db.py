from datetime import datetime

class MockDB:
    def __init__(self):
        self.patients = {}
        self.alerts = []
        self.vitals_history = {}

    def seed(self):
        # Your initial 5 patients
        initial_data = [
            {"id": "P001", "name": "Eleanor Vance", "age": 67, "room": "ICU-101", "status": "Stable"},
            {"id": "P002", "name": "Marcus Chen", "age": 45, "room": "ICU-102", "status": "Stable"},
            {"id": "P003", "name": "Sarah Mitchell", "age": 72, "room": "ICU-103", "status": "Warning"},
            {"id": "P004", "name": "James Rodriguez", "age": 58, "room": "Ward-204", "status": "Stable"},
            {"id": "P005", "name": "Priya Patel", "age": 34, "room": "Ward-205", "status": "Stable"}
        ]
        for p in initial_data:
            self.patients[p['id']] = p
            self.vitals_history[p['id']] = []

# Global instance
storage = MockDB()
storage.seed()
