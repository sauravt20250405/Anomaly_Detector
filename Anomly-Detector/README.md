# 🏥 Healthcare Anomaly Detection System

An AI-powered real-time patient monitoring system that detects anomalies in vital signs using **Isolation Forest** machine learning. The system continuously simulates patient vitals, scores them for anomalies, and raises severity-based alerts.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Deployed-red)
![ML](https://img.shields.io/badge/ML-Isolation%20Forest-green)

---

## Features

- **Real-Time Anomaly Detection** — Isolation Forest model trained on 2,000 synthetic normal vital-sign samples scores each reading on a 0–100 scale.
- **Severity Classification** — Alerts are classified as **HIGH** (≥70), **MEDIUM** (≥40), or **LOW** (<40) based on anomaly score.
- **Patient Monitoring Dashboard** — KPI cards, severity distribution chart, patient status table, and recent alerts.
- **Alerts Feed** — Filterable alerts table with acknowledge functionality.
- **Analytics** — Anomaly score trend lines, per-patient alert counts, score histograms, and vital sign distributions.
- **Alert Logs** — Full log history with severity/patient filters and CSV export.
- **Data Simulator** — Generates realistic vital signs (heart rate, SpO₂, temperature, blood pressure) with configurable anomaly injection rate (default 20%).
- **Email Notifications** — Optional SMTP-based email alerts for HIGH severity detections with per-patient rate limiting.

---

## Tech Stack

- **Frontend:** Streamlit (for cloud deployment) / Flask + Jinja2 (local)
- **ML Model:** scikit-learn Isolation Forest
- **Database:** SQLite
- **Charts:** Plotly
- **Language:** Python 3.10+

---

## Project Structure

```
Anomly-Detector/
├── streamlit_app.py          # Streamlit frontend (for Streamlit Cloud)
├── app.py                    # Flask backend (for local development)
├── config.py                 # App configuration & thresholds
├── requirements.txt          # Python dependencies
├── anomaly_detector.db       # SQLite database (auto-generated)
├── .streamlit/
│   └── config.toml           # Streamlit dark theme
├── models/
│   ├── anomaly_detector.py   # Isolation Forest ML model
│   └── database.py           # SQLAlchemy models (Flask version)
├── services/
│   ├── alert_service.py      # Alert processing pipeline
│   ├── data_simulator.py     # Vital sign data generator
│   └── email_service.py      # SMTP email notifications
├── templates/                # Jinja2 HTML templates (Flask version)
│   ├── base.html
│   ├── dashboard.html
│   ├── alerts.html
│   ├── analytics.html
│   └── logs.html
└── static/
    └── css/
        └── style.css
```

---

## How It Works

1. **Data Simulation** — The simulator generates vital signs for 5 patients. Each reading has a 20% chance of containing anomalous values (e.g. tachycardia, hypoxemia, fever, hypertension).
2. **ML Scoring** — Each reading is fed to the Isolation Forest model. The raw score is mapped to a 0–100 anomaly scale.
3. **Alert Creation** — Based on the score, an alert is created with HIGH / MEDIUM / LOW severity.
4. **Patient Status Update** — The patient's status is updated to Critical, Warning, or Stable accordingly.
5. **Notification** — HIGH severity alerts trigger an email notification (if SMTP is configured).

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
git clone https://github.com/<your-username>/Anomly-Detector.git
cd Anomly-Detector
pip install -r requirements.txt
```

### Run with Streamlit (Recommended)

```bash
streamlit run streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### Run with Flask (Local)

```bash
pip install flask flask-socketio flask-sqlalchemy eventlet
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## Streamlit Cloud Deployment

1. Push the repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in.
3. Click **New app** → select the repo, branch `main`, and set main file to `streamlit_app.py`.
4. Click **Deploy**.

> **Note:** The SQLite database is ephemeral on Streamlit Cloud. Initial seed data is auto-generated on first visit. Click **"⚡ Generate Readings"** in the sidebar to simulate new patient vitals.

---

## Configuration

Key settings in `config.py`:

| Setting | Default | Description |
|---|---|---|
| `HIGH_RISK_THRESHOLD` | 70 | Anomaly score ≥ 70 → HIGH severity |
| `MEDIUM_RISK_THRESHOLD` | 40 | Anomaly score ≥ 40 → MEDIUM severity |
| `SIMULATOR_INTERVAL` | 15s | Seconds between simulated readings (Flask) |
| `ANOMALY_INJECTION_RATE` | 0.20 | 20% chance of anomalous reading |
| `EMAIL_COOLDOWN_MINUTES` | 5 | Rate limit: 1 email per patient per 5 min |

### Email Alerts (Optional)

Create a `.env` file in the project root:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_RECIPIENTS=doctor1@hospital.com,doctor2@hospital.com
```

---

## Sample Patients

| ID | Name | Age | Room | Initial Status |
|---|---|---|---|---|
| P001 | Eleanor Vance | 67 | ICU-101 | Stable |
| P002 | Marcus Chen | 45 | ICU-102 | Stable |
| P003 | Sarah Mitchell | 72 | ICU-103 | Warning |
| P004 | James Rodriguez | 58 | Ward-204 | Stable |
| P005 | Priya Patel | 34 | Ward-205 | Stable |

---

## License

This project is open source and available under the [MIT License](LICENSE).
