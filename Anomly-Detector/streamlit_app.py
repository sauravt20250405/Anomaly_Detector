import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone, timedelta

from models.anomaly_detector import detector
from services.data_simulator import simulator

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Healthcare Anomaly Detector",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background: #1a1d2e;
        border: 1px solid #2a2d3e;
        border-radius: 12px;
        padding: 16px 20px;
    }
</style>
""", unsafe_allow_html=True)

# ── SQLite helpers (replaces Flask-SQLAlchemy) ───────────────────────────────
DB_PATH = "anomaly_detector_st.db"


def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def _init_db():
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY, name TEXT NOT NULL,
            age INTEGER NOT NULL, room TEXT NOT NULL,
            status TEXT DEFAULT 'Stable'
        );
        CREATE TABLE IF NOT EXISTS vital_signs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL, heart_rate REAL, spo2 REAL,
            temperature REAL, systolic_bp REAL, diastolic_bp REAL,
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL, anomaly_score REAL, severity TEXT,
            heart_rate REAL, spo2 REAL, temperature REAL,
            systolic_bp REAL, diastolic_bp REAL,
            acknowledged INTEGER DEFAULT 0, timestamp TEXT
        );
    """)
    if conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
        conn.executemany("INSERT INTO patients VALUES (?,?,?,?,?)", [
            ("P001", "Eleanor Vance",    67, "ICU-101",  "Stable"),
            ("P002", "Marcus Chen",      45, "ICU-102",  "Stable"),
            ("P003", "Sarah Mitchell",   72, "ICU-103",  "Warning"),
            ("P004", "James Rodriguez",  58, "Ward-204", "Stable"),
            ("P005", "Priya Patel",      34, "Ward-205", "Stable"),
        ])
        conn.commit()
    conn.close()


_init_db()


# ── Data helpers ─────────────────────────────────────────────────────────────
def _process_reading(reading: dict):
    """Run ML detection, persist vital + alert, update patient status."""
    result = detector.detect(reading)
    ts = reading["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    conn = _conn()
    conn.execute(
        "INSERT INTO vital_signs "
        "(patient_id,heart_rate,spo2,temperature,systolic_bp,diastolic_bp,timestamp) "
        "VALUES (?,?,?,?,?,?,?)",
        (reading["patient_id"], reading["heart_rate"], reading["spo2"],
         reading["temperature"], reading["systolic_bp"], reading["diastolic_bp"], ts),
    )
    conn.execute(
        "INSERT INTO alerts "
        "(patient_id,anomaly_score,severity,heart_rate,spo2,temperature,"
        "systolic_bp,diastolic_bp,timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
        (reading["patient_id"], result["anomaly_score"], result["severity"],
         reading["heart_rate"], reading["spo2"], reading["temperature"],
         reading["systolic_bp"], reading["diastolic_bp"], ts),
    )
    status = {"HIGH": "Critical", "MEDIUM": "Warning"}.get(result["severity"], "Stable")
    conn.execute("UPDATE patients SET status=? WHERE id=?", (status, reading["patient_id"]))
    conn.commit()
    conn.close()


def generate_batch():
    for r in simulator.generate_batch(5):
        _process_reading(r)


def _stats() -> dict:
    conn = _conn()
    total_p   = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    active    = conn.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged=0 AND severity IN ('HIGH','MEDIUM')").fetchone()[0]
    avg_score = conn.execute("SELECT COALESCE(AVG(anomaly_score),0) FROM alerts").fetchone()[0]
    high   = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity='HIGH'").fetchone()[0]
    medium = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity='MEDIUM'").fetchone()[0]
    low    = conn.execute("SELECT COUNT(*) FROM alerts WHERE severity='LOW'").fetchone()[0]
    conn.close()
    return dict(total_patients=total_p, active_alerts=active,
                avg_score=round(avg_score, 2), high=high, medium=medium,
                low=low, total=high + medium + low)


def _alerts_df(severity="ALL", limit=50) -> pd.DataFrame:
    conn = _conn()
    q = ("SELECT id,patient_id,anomaly_score,severity,heart_rate,spo2,"
         "temperature,systolic_bp,diastolic_bp,acknowledged,timestamp FROM alerts")
    params: list = []
    if severity != "ALL":
        q += " WHERE severity=?"
        params.append(severity)
    q += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df


def _patients_df() -> pd.DataFrame:
    conn = _conn()
    df = pd.read_sql_query("SELECT * FROM patients", conn)
    conn.close()
    return df


def _vitals_df(patient_id=None, limit=200) -> pd.DataFrame:
    conn = _conn()
    q = "SELECT * FROM vital_signs"
    params: list = []
    if patient_id:
        q += " WHERE patient_id=?"
        params.append(patient_id)
    q += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df


def _acknowledge(alert_id: int):
    conn = _conn()
    conn.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,))
    conn.commit()
    conn.close()


# ── Generate initial readings on first visit ─────────────────────────────────
if "seeded" not in st.session_state:
    generate_batch()
    generate_batch()
    st.session_state.seeded = True

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏥 Anomaly Detector")
    st.caption("AI-Powered Healthcare Monitoring")
    st.divider()

    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "🚨 Alerts", "📈 Analytics", "📋 Logs"],
        label_visibility="collapsed",
    )

    st.divider()
    if st.button("⚡ Generate Readings", use_container_width=True):
        generate_batch()
        st.rerun()

    stats = _stats()
    st.metric("Total Readings", stats["total"])

# ── PAGE: Dashboard ──────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    st.header("Monitoring Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Patients", stats["total_patients"])
    c2.metric("Active Alerts", stats["active_alerts"])
    c3.metric("Avg Anomaly Score", stats["avg_score"])
    c4.metric("Model Accuracy", "97.2 %")

    st.divider()
    col_chart, col_table = st.columns([1, 2])

    with col_chart:
        st.subheader("Severity Distribution")
        if stats["total"] > 0:
            fig = go.Figure(go.Pie(
                labels=["High", "Medium", "Low"],
                values=[stats["high"], stats["medium"], stats["low"]],
                marker_colors=["#ef4444", "#f59e0b", "#22c55e"],
                hole=0.5, textinfo="value+percent",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e5e7eb", height=320,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", y=-0.15),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data yet — click **Generate Readings**.")

    with col_table:
        st.subheader("Patient Status")
        patients = _patients_df()
        if not patients.empty:
            st.dataframe(
                patients, use_container_width=True, hide_index=True,
                column_config={
                    "id": "Patient ID", "name": "Name",
                    "age": "Age", "room": "Room", "status": "Status",
                },
            )

    st.divider()
    st.subheader("Recent Alerts")
    recent = _alerts_df(limit=10)
    if not recent.empty:
        st.dataframe(
            recent[["patient_id", "anomaly_score", "severity",
                     "heart_rate", "spo2", "temperature", "timestamp"]],
            use_container_width=True, hide_index=True,
            column_config={
                "patient_id": "Patient",
                "anomaly_score": st.column_config.NumberColumn("Score", format="%.1f"),
                "severity": "Severity",
                "heart_rate": st.column_config.NumberColumn("HR (bpm)", format="%.1f"),
                "spo2": st.column_config.NumberColumn("SpO₂ (%)", format="%.1f"),
                "temperature": st.column_config.NumberColumn("Temp (°C)", format="%.1f"),
                "timestamp": "Time",
            },
        )
    else:
        st.info("No alerts yet.")

# ── PAGE: Alerts ─────────────────────────────────────────────────────────────
elif page == "🚨 Alerts":
    st.header("Alerts Feed")

    sev = st.selectbox("Filter by Severity", ["ALL", "HIGH", "MEDIUM", "LOW"])
    alerts = _alerts_df(severity=sev, limit=100)

    if not alerts.empty:
        st.dataframe(
            alerts, use_container_width=True, hide_index=True,
            column_config={
                "id": "ID", "patient_id": "Patient",
                "anomaly_score": st.column_config.NumberColumn("Score", format="%.1f"),
                "severity": "Severity",
                "heart_rate": st.column_config.NumberColumn("HR", format="%.1f"),
                "spo2": st.column_config.NumberColumn("SpO₂", format="%.1f"),
                "temperature": st.column_config.NumberColumn("Temp", format="%.1f"),
                "systolic_bp": st.column_config.NumberColumn("Sys BP", format="%.0f"),
                "diastolic_bp": st.column_config.NumberColumn("Dia BP", format="%.0f"),
                "acknowledged": st.column_config.CheckboxColumn("Ack"),
                "timestamp": "Time",
            },
        )
        with st.expander("Acknowledge an alert"):
            aid = st.number_input("Alert ID", min_value=1, step=1)
            if st.button("✅ Acknowledge"):
                _acknowledge(aid)
                st.success(f"Alert {aid} acknowledged.")
                st.rerun()
    else:
        st.info("No alerts match this filter.")

# ── PAGE: Analytics ──────────────────────────────────────────────────────────
elif page == "📈 Analytics":
    st.header("Analytics")
    alerts = _alerts_df(limit=200)

    if alerts.empty:
        st.info("No data yet — generate readings from the sidebar.")
    else:
        # Trend line
        st.subheader("Anomaly Score Trend")
        sorted_a = alerts.sort_values("timestamp")
        fig = px.line(
            sorted_a, x="timestamp", y="anomaly_score", color="severity",
            color_discrete_map={"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#22c55e"},
            markers=True,
        )
        fig.add_hline(y=70, line_dash="dash", line_color="#ef4444",
                      annotation_text="High Threshold")
        fig.add_hline(y=40, line_dash="dash", line_color="#f59e0b",
                      annotation_text="Medium Threshold")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#e5e7eb", height=400,
            xaxis_title="Time", yaxis_title="Anomaly Score",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Alerts per Patient")
            pc = alerts.groupby("patient_id").size().reset_index(name="count")
            fig2 = px.bar(pc, x="patient_id", y="count",
                          color="count",
                          color_continuous_scale=["#22c55e", "#f59e0b", "#ef4444"])
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e5e7eb", height=300,
            )
            st.plotly_chart(fig2, use_container_width=True)

        with c2:
            st.subheader("Score Distribution")
            fig3 = px.histogram(alerts, x="anomaly_score", nbins=20,
                                color_discrete_sequence=["#6366f1"])
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#e5e7eb", height=300,
                xaxis_title="Anomaly Score", yaxis_title="Count",
            )
            st.plotly_chart(fig3, use_container_width=True)

        st.divider()
        st.subheader("Vital Sign Distributions")
        vitals = _vitals_df(limit=200)
        if not vitals.empty:
            v1, v2, v3 = st.columns(3)
            for col, vital, color, title in [
                (v1, "heart_rate",  "#ef4444", "Heart Rate (bpm)"),
                (v2, "spo2",       "#3b82f6", "SpO₂ (%)"),
                (v3, "temperature", "#f59e0b", "Temperature (°C)"),
            ]:
                with col:
                    f = px.histogram(vitals, x=vital, nbins=25,
                                     color_discrete_sequence=[color], title=title)
                    f.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#e5e7eb", height=250, showlegend=False,
                    )
                    st.plotly_chart(f, use_container_width=True)

# ── PAGE: Logs ───────────────────────────────────────────────────────────────
elif page == "📋 Logs":
    st.header("Alert Logs")

    f1, f2, f3 = st.columns(3)
    with f1:
        sev = st.selectbox("Severity", ["ALL", "HIGH", "MEDIUM", "LOW"], key="lsev")
    with f2:
        pat = st.selectbox("Patient", ["ALL", "P001", "P002", "P003", "P004", "P005"], key="lpat")
    with f3:
        lim = st.slider("Max rows", 10, 500, 100, key="llim")

    conn = _conn()
    q = "SELECT * FROM alerts WHERE 1=1"
    params: list = []
    if sev != "ALL":
        q += " AND severity=?"
        params.append(sev)
    if pat != "ALL":
        q += " AND patient_id=?"
        params.append(pat)
    q += " ORDER BY timestamp DESC LIMIT ?"
    params.append(lim)
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()

    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False)
        st.download_button("📥 Download CSV", csv, "alert_logs.csv", "text/csv")
    else:
        st.info("No logs match the selected filters.")
