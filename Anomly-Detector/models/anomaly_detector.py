import numpy as np
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    """
    Isolation Forest anomaly detector for patient vital signs.
    Trained on synthetic 'normal' vital data so that deviations
    produce higher anomaly scores.
    """

    def __init__(self):
        self.model = None
        self._train()

    def _train(self):
        """Train on synthetic normal vital sign data."""
        np.random.seed(42)
        n_samples = 2000

        # Normal ranges
        heart_rate = np.random.normal(75, 8, n_samples)       # 60-90 bpm
        spo2 = np.random.normal(97, 1.2, n_samples)           # 95-100%
        temperature = np.random.normal(37.0, 0.3, n_samples)  # 36.5-37.5°C
        systolic_bp = np.random.normal(120, 10, n_samples)    # 100-140
        diastolic_bp = np.random.normal(78, 7, n_samples)     # 65-90

        X_train = np.column_stack([
            heart_rate, spo2, temperature, systolic_bp, diastolic_bp
        ])

        self.model = IsolationForest(
            n_estimators=150,
            contamination=0.05,
            random_state=42,
            n_jobs=1,  # Must be 1 to avoid deadlock with eventlet monkey-patching
        )
        self.model.fit(X_train)
        print("[ML] Isolation Forest trained on", n_samples, "normal samples.")

    def detect(self, vitals: dict) -> dict:
        """
        Score a single vital-sign reading.

        Args:
            vitals: dict with keys heart_rate, spo2, temperature,
                    systolic_bp, diastolic_bp

        Returns:
            dict with anomaly_score (0-100) and severity (HIGH/MEDIUM/LOW)
        """
        features = np.array([[
            vitals["heart_rate"],
            vitals["spo2"],
            vitals["temperature"],
            vitals["systolic_bp"],
            vitals["diastolic_bp"],
        ]])

        # score_samples returns negative values; more negative = more anomalous
        raw_score = self.model.score_samples(features)[0]

        # Map to 0-100 scale.  Typical normal scores ~ -0.15 to 0.
        # Anomalous scores ~ -0.3 to -0.7+
        anomaly_score = max(0, min(100, ((-raw_score) - 0.10) * 200))

        if anomaly_score >= 70:
            severity = "HIGH"
        elif anomaly_score >= 40:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return {
            "anomaly_score": round(anomaly_score, 1),
            "severity": severity,
        }


# Singleton
detector = AnomalyDetector()
