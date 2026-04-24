"""
Anomaly Detection Module
Uses Z-score, IQR, and Isolation Forest to flag unusual transactions
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any


def zscore_anomalies(df: pd.DataFrame, threshold: float = 2.5) -> pd.Series:
    """Flag transactions where amount is > threshold standard deviations from mean."""
    mean = df["amount"].mean()
    std = df["amount"].std()
    if std == 0:
        return pd.Series([False] * len(df), index=df.index)
    z_scores = (df["amount"] - mean) / std
    return z_scores.abs() > threshold


def iqr_anomalies(df: pd.DataFrame, multiplier: float = 2.0) -> pd.Series:
    """Flag transactions outside IQR * multiplier range."""
    Q1 = df["amount"].quantile(0.25)
    Q3 = df["amount"].quantile(0.75)
    IQR = Q3 - Q1
    upper_bound = Q3 + multiplier * IQR
    return df["amount"] > upper_bound


def isolation_forest_anomalies(df: pd.DataFrame, contamination: float = 0.05) -> pd.Series:
    """Use Isolation Forest for anomaly detection."""
    try:
        from sklearn.ensemble import IsolationForest
        model = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
        features = df[["amount"]].copy()
        # Add day-of-week and day-of-month as features if date exists
        if "date" in df.columns:
            features["day_of_week"] = pd.to_datetime(df["date"]).dt.dayofweek
            features["day_of_month"] = pd.to_datetime(df["date"]).dt.day
        preds = model.fit_predict(features)
        return pd.Series(preds == -1, index=df.index)
    except Exception:
        return pd.Series([False] * len(df), index=df.index)


def frequency_spike_detection(df: pd.DataFrame, window_days: int = 7, threshold_multiplier: float = 2.0) -> pd.Series:
    """Detect unusual frequency spikes in transactions."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    daily_counts = df.groupby(df["date"].dt.date).size()
    mean_daily = daily_counts.mean()
    std_daily = daily_counts.std() if daily_counts.std() > 0 else 1

    spike_dates = daily_counts[daily_counts > mean_daily + threshold_multiplier * std_daily].index
    spike_dates_set = set(spike_dates)

    return df["date"].dt.date.apply(lambda d: d in spike_dates_set)


def detect_all_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run all anomaly detection methods and combine results.
    Returns dataframe with anomaly flags and reasons.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Run detectors
    df["anomaly_zscore"] = zscore_anomalies(df)
    df["anomaly_iqr"] = iqr_anomalies(df)
    df["anomaly_iforest"] = isolation_forest_anomalies(df)
    df["anomaly_freq_spike"] = frequency_spike_detection(df)

    # Suspicious merchant flag (set in categorizer)
    if "is_suspicious_merchant" not in df.columns:
        df["is_suspicious_merchant"] = False

    # Combine: flag if 2+ methods agree OR merchant is suspicious
    anomaly_score = (
        df["anomaly_zscore"].astype(int) +
        df["anomaly_iqr"].astype(int) +
        df["anomaly_iforest"].astype(int)
    )
    df["is_anomaly"] = (anomaly_score >= 2) | df["is_suspicious_merchant"]

    # Generate human-readable reasons
    def build_reasons(row):
        reasons = []
        if row["anomaly_zscore"]:
            reasons.append("Unusually large amount (Z-score)")
        if row["anomaly_iqr"]:
            reasons.append("Exceeds normal spending range (IQR)")
        if row["anomaly_iforest"]:
            reasons.append("Statistical outlier (Isolation Forest)")
        if row["anomaly_freq_spike"]:
            reasons.append("Transaction frequency spike on this day")
        if row.get("is_suspicious_merchant", False):
            reasons.append("Suspicious merchant pattern")
        return "; ".join(reasons) if reasons else ""

    df["anomaly_reason"] = df.apply(build_reasons, axis=1)

    return df


def get_anomaly_summary(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Return list of anomalous transactions for API response."""
    anomalies = df[df["is_anomaly"] == True].copy()
    result = []
    for _, row in anomalies.iterrows():
        result.append({
            "date": str(row["date"].date()),
            "merchant": row["merchant"],
            "amount": float(row["amount"]),
            "category": row.get("category", "Others"),
            "reason": row["anomaly_reason"],
            "severity": "HIGH" if row["amount"] > 500 else "MEDIUM"
        })
    return sorted(result, key=lambda x: x["amount"], reverse=True)
