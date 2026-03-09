import os
from dotenv import load_dotenv

load_dotenv()

# Build default SQLite path next to this file
_basedir = os.path.abspath(os.path.dirname(__file__))
_default_db = "sqlite:///" + os.path.join(_basedir, "anomaly_detector.db")


class Config:
    """Application configuration."""
    SECRET_KEY = os.getenv("SECRET_KEY", "healthcare-anomaly-secret-key-2026")

    # Database — defaults to local SQLite; set DATABASE_URL for PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", _default_db)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SMTP Email
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    ALERT_RECIPIENTS = os.getenv("ALERT_RECIPIENTS", "").split(",")

    # Anomaly Detection Thresholds
    HIGH_RISK_THRESHOLD = 70   # anomaly score > 70 → HIGH
    MEDIUM_RISK_THRESHOLD = 40  # anomaly score > 40 → MEDIUM
    # Below 40 → LOW

    # Simulator
    SIMULATOR_INTERVAL = 15  # seconds between vital sign readings
    ANOMALY_INJECTION_RATE = 0.20  # 20% chance of anomalous reading

    # Email rate limiting
    EMAIL_COOLDOWN_MINUTES = 5  # max 1 email per patient per N minutes
