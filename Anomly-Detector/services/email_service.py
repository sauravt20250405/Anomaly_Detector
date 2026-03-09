import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from config import Config


# Track last email time per patient for rate limiting
_last_email_sent = {}


def should_send_email(patient_id: str) -> bool:
    """Check rate limit — max 1 email per patient per cooldown period."""
    now = datetime.now(timezone.utc)
    last = _last_email_sent.get(patient_id)
    if last and (now - last) < timedelta(minutes=Config.EMAIL_COOLDOWN_MINUTES):
        return False
    return True


def send_alert_email(alert_data: dict):
    """
    Send HTML email notification for a HIGH severity alert.
    Respects rate limiting per patient.
    """
    patient_id = alert_data.get("patient_id", "Unknown")

    if not Config.SMTP_EMAIL or not Config.SMTP_PASSWORD:
        print(f"[EMAIL] ⚠ SMTP not configured. Would send alert for {patient_id}: "
              f"Score={alert_data.get('anomaly_score')}, Severity={alert_data.get('severity')}")
        return False

    if not should_send_email(patient_id):
        print(f"[EMAIL] Rate limited for {patient_id}. Skipping.")
        return False

    recipients = [r.strip() for r in Config.ALERT_RECIPIENTS if r.strip()]
    if not recipients:
        print("[EMAIL] No recipients configured.")
        return False

    subject = f"🚨 HIGH RISK ALERT — Patient {patient_id}"

    html_body = f"""
    <html>
    <body style="font-family: 'Segoe UI', sans-serif; background: #0f111a; color: #e5e7eb; padding: 24px;">
        <div style="max-width: 600px; margin: auto; background: #1a1d2e; border-radius: 12px; padding: 32px; border: 1px solid #2a2d3e;">
            <h2 style="color: #ef4444; margin-top: 0;">🚨 Critical Anomaly Detected</h2>
            <p style="color: #9ca3af;">The AI anomaly detection system has flagged a <strong style="color: #ef4444;">HIGH RISK</strong> alert.</p>

            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr><td style="padding: 8px 0; color: #9ca3af;">Patient ID</td><td style="padding: 8px 0; color: #fff; font-weight: 600;">{patient_id}</td></tr>
                <tr><td style="padding: 8px 0; color: #9ca3af;">Anomaly Score</td><td style="padding: 8px 0; color: #ef4444; font-weight: 600;">{alert_data.get('anomaly_score', '—')}</td></tr>
                <tr><td style="padding: 8px 0; color: #9ca3af;">Heart Rate</td><td style="padding: 8px 0; color: #fff;">{alert_data.get('heart_rate', '—')}</td></tr>
                <tr><td style="padding: 8px 0; color: #9ca3af;">SpO₂</td><td style="padding: 8px 0; color: #fff;">{alert_data.get('spo2', '—')}</td></tr>
                <tr><td style="padding: 8px 0; color: #9ca3af;">Temperature</td><td style="padding: 8px 0; color: #fff;">{alert_data.get('temperature', '—')}</td></tr>
                <tr><td style="padding: 8px 0; color: #9ca3af;">Blood Pressure</td><td style="padding: 8px 0; color: #fff;">{alert_data.get('bp', '—')}</td></tr>
                <tr><td style="padding: 8px 0; color: #9ca3af;">Time</td><td style="padding: 8px 0; color: #fff;">{alert_data.get('timestamp', '—')}</td></tr>
            </table>

            <p style="color: #9ca3af; font-size: 13px;">Please review the patient immediately on the <a href="http://localhost:5000/alerts" style="color: #6366f1;">Anomaly Dashboard</a>.</p>
            <hr style="border-color: #2a2d3e; margin: 20px 0;">
            <p style="color: #6b7280; font-size: 11px;">AI Healthcare Anomaly Detection System © 2026</p>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = Config.SMTP_EMAIL
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_EMAIL, Config.SMTP_PASSWORD)
            server.send_message(msg)

        _last_email_sent[patient_id] = datetime.now(timezone.utc)
        print(f"[EMAIL] ✅ Alert email sent for {patient_id} to {recipients}")
        return True

    except Exception as e:
        print(f"[EMAIL] ❌ Failed to send: {e}")
        return False
