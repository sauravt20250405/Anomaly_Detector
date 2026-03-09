from models.database import db_storage, Alert, VitalSign, Patient
from models.anomaly_detector import detector
from datetime import datetime

def process_vitals(vitals_data: dict) -> dict:
    """Process vitals using memory storage instead of SQL."""
    
    # 1. Store vitals in memory
    vital = VitalSign(
        patient_id=vitals_data["patient_id"],
        heart_rate=vitals_data["heart_rate"],
        spo2=vitals_data["spo2"],
        temperature=vitals_data["temperature"],
        systolic_bp=vitals_data["systolic_bp"],
        diastolic_bp=vitals_data["diastolic_bp"]
    )
    db_storage.vital_signs.append(vital)

    # 2. Run anomaly detection
    result = detector.detect(vitals_data)

    # 3. Create alert in memory
    alert = Alert(
        patient_id=vitals_data["patient_id"],
        anomaly_score=result["anomaly_score"],
        severity=result["severity"],
        hr=vitals_data["heart_rate"],
        spo2=vitals_data["spo2"],
        temp=vitals_data["temperature"],
        sys=vitals_data["systolic_bp"],
        dia=vitals_data["diastolic_bp"]
    )
    db_storage.alerts.append(alert)

    # 4. Update patient status in the global list
    for p in db_storage.patients:
        if p.id == vitals_data["patient_id"]:
            if result["severity"] == "HIGH":
                p.status = "Critical"
            elif result["severity"] == "MEDIUM":
                p.status = "Warning"
            else:
                p.status = "Stable"
            break

    return alert.to_dict()

def get_dashboard_stats() -> dict:
    """Calculate statistics using list logic."""
    total_patients = len(db_storage.patients)
    
    # Filter active alerts (unacknowledged HIGH/MEDIUM)
    active_alerts_list = [a for a in db_storage.alerts 
                          if not a.acknowledged and a.severity in ["HIGH", "MEDIUM"]]
    active_alerts = len(active_alerts_list)

    # Calculate Average Score
    if db_storage.alerts:
        avg_score = sum(a.anomaly_score for a in db_storage.alerts) / len(db_storage.alerts)
    else:
        avg_score = 0.0

    # Severity distribution
    high_count = sum(1 for a in db_storage.alerts if a.severity == "HIGH")
    medium_count = sum(1 for a in db_storage.alerts if a.severity == "MEDIUM")
    low_count = sum(1 for a in db_storage.alerts if a.severity == "LOW")

    return {
        "total_patients": total_patients,
        "active_alerts": active_alerts,
        "avg_anomaly_score": round(avg_score, 2),
        "model_accuracy": 97.2,
        "severity_distribution": {
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
            "total": len(db_storage.alerts),
        },
    }

def get_recent_alerts(limit=50, severity_filter=None):
    """Get alerts from the in-memory list."""
    alerts = db_storage.alerts
    if severity_filter and severity_filter != "ALL":
        alerts = [a for a in alerts if a.severity == severity_filter]
    
    # Sort by timestamp (newest first) and limit
    sorted_alerts = sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    return [a.to_dict() for a in sorted_alerts[:limit]]

def get_patient_vitals(patient_id=None, limit=50):
    """Get vital signs from the in-memory list."""
    vitals = db_storage.vital_signs
    if patient_id:
        vitals = [v for v in vitals if v.patient_id == patient_id]
        
    sorted_vitals = sorted(vitals, key=lambda x: x.timestamp, reverse=True)
    return [v.to_dict() for v in sorted_vitals[:limit]]

def acknowledge_alert(alert_id: int) -> bool:
    """Mark alert as acknowledged in the list."""
    for alert in db_storage.alerts:
        if alert.id == alert_id:
            alert.acknowledged = True
            return True
    return False