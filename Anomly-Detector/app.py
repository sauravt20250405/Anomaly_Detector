from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from config import Config
# Import our custom storage and models
from models.database import db_storage, Patient, seed_patients
from services.alert_service import (
    process_vitals, get_dashboard_stats, get_recent_alerts, 
    get_patient_vitals, acknowledge_alert
)
from services.data_simulator import simulator
from services.email_service import send_alert_email
import threading
import time

app = Flask(__name__)
app.config.from_object(Config)

# SocketIO initialization
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

# --- Memory Storage init ---
# We no longer need db.create_all() because we aren't using a physical DB file
seed_patients()
print("[APP] In-memory storage initialized with patient data.")

# --- Page routes ---
@app.route("/")
def dashboard():
    return render_template("dashboard.html", active="dashboard")

@app.route("/alerts")
def alerts_page():
    return render_template("alerts.html", active="alerts")

@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html", active="analytics")

@app.route("/logs")
def logs_page():
    return render_template("logs.html", active="logs")

# --- API endpoints ---
@app.route("/api/stats")
def api_stats():
    return jsonify(get_dashboard_stats())

@app.route("/api/alerts")
def api_alerts():
    severity = request.args.get("severity", "ALL")
    limit = int(request.args.get("limit", 50))
    return jsonify(get_recent_alerts(limit, severity))

@app.route("/api/vitals")
def api_vitals():
    patient_id = request.args.get("patient_id")
    limit = int(request.args.get("limit", 50))
    return jsonify(get_patient_vitals(patient_id, limit))

@app.route("/api/patients")
def api_patients():
    # Fetch from our list in memory instead of SQLAlchemy query
    return jsonify([p.to_dict() for p in db_storage.patients])

@app.route("/api/alerts/<int:alert_id>/acknowledge", methods=["POST"])
def api_acknowledge(alert_id):
    success = acknowledge_alert(alert_id)
    return jsonify({"success": success})

@app.route("/api/alerts/trend")
def api_alert_trend():
    """Return anomaly scores from memory for charting."""
    # We pull from db_storage.alerts directly
    limit = 100
    recent_alerts = sorted(db_storage.alerts, key=lambda x: x.timestamp)[-limit:]
    
    return jsonify([{
        "timestamp": a.timestamp.strftime("%m/%d %H:%M"),
        "score": round(a.anomaly_score, 1),
        "severity": a.severity,
        "patient_id": a.patient_id,
    } for a in recent_alerts])

# --- SocketIO events ---
@socketio.on("connect")
def handle_connect():
    print("[WS] Client connected")

# --- Background simulator ---
def run_simulator():
    print(f"[SIM] Simulator started (interval={Config.SIMULATOR_INTERVAL}s)")
    time.sleep(3)

    while True:
        try:
            # Note: No 'app.app_context()' needed anymore since we aren't using SQLAlchemy!
            readings = simulator.generate_batch(5)
            for reading in readings:
                alert_data = process_vitals(reading)
                socketio.emit("new_alert", alert_data)

                if alert_data["severity"] == "HIGH":
                    send_alert_email(alert_data)

            stats = get_dashboard_stats()
            socketio.emit("stats_update", stats)

        except Exception as e:
            print(f"[SIM] Error: {e}")

        time.sleep(Config.SIMULATOR_INTERVAL)
        
import csv
from io import StringIO
from flask import make_response

# 1. Endpoint to Add a Patient
@app.route("/api/patients/add", methods=["POST"])
def api_add_patient():
    data = request.json
    new_p = db_storage.add_patient(data['name'], int(data['age']), data['room'])
    return jsonify(new_p.to_dict())

# 2. Endpoint to Export Data to CSV
@app.route("/api/export/alerts")
def export_alerts():
    si = StringIO()
    cw = csv.writer(si)
    # Header
    cw.writerow(['ID', 'Patient ID', 'Score', 'Severity', 'Heart Rate', 'Timestamp'])
    
    # Data from memory
    for a in db_storage.alerts:
        cw.writerow([a.id, a.patient_id, a.anomaly_score, a.severity, a.heart_rate, a.timestamp])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=alerts_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

from fpdf import FPDF

@app.route("/api/export/pdf")
def export_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Healthcare AI - Anomaly Report", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    
    # Add summary stats
    stats = get_dashboard_stats()
    pdf.cell(200, 10, txt=f"Total Patients Monitored: {stats['total_patients']}", ln=True)
    pdf.cell(200, 10, txt=f"Avg Anomaly Score: {stats['avg_anomaly_score']}", ln=True)
    pdf.ln(5)

    # Table Header
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(30, 10, "Patient", 1, 0, 'C', True)
    pdf.cell(30, 10, "Score", 1, 0, 'C', True)
    pdf.cell(40, 10, "Severity", 1, 0, 'C', True)
    pdf.cell(90, 10, "Timestamp", 1, 1, 'C', True)

    # Table Data from Memory
    for a in db_storage.alerts[-20:]: # Last 20 alerts
        pdf.cell(30, 10, str(a.patient_id), 1)
        pdf.cell(30, 10, str(round(a.anomaly_score, 1)), 1)
        pdf.cell(40, 10, str(a.severity), 1)
        pdf.cell(90, 10, str(a.timestamp.strftime("%Y-%m-%d %H:%M")), 1, 1)

    response = make_response(pdf.output(dest='S').encode('latin-1'))
    response.headers.set('Content-Disposition', 'attachment', filename='health_report.pdf')
    response.headers.set('Content-Type', 'application/pdf')
    return response


@app.route("/api/patients/<patient_id>/history")
def api_patient_history(patient_id):
    # Filter our in-memory alerts for just this patient
    history = [a.to_dict() for a in db_storage.alerts if a.patient_id == patient_id]
    # Sort by time so the graph looks correct
    sorted_history = sorted(history, key=lambda x: x['timestamp_iso'])
    return jsonify(sorted_history)

# --- Entry point ---
if __name__ == "__main__":
    sim_thread = threading.Thread(target=run_simulator, daemon=True)
    sim_thread.start()

    print("\n" + "=" * 56)
    print("  [+] Healthcare Anomaly Detection System (RAM MODE)")
    print("  [*] Dashboard:  http://localhost:5000")
    print("=" * 56 + "\n")

    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)