"""
Event detector — identifies significant dips and rises in NAV time series.
"""

import pandas as pd
import numpy as np
from datetime import timedelta


def detect_events(
    nav_series: pd.DataFrame,
    dip_threshold: float = -5.0,
    rise_threshold: float = 10.0,
    window_days: int = 7,
) -> list[dict]:
    """
    Detect significant price events in a NAV time series.

    Args:
        nav_series: DataFrame with [date, nav] or [date, current_value]
        dip_threshold: Percentage drop to flag as dip (negative, e.g., -5.0)
        rise_threshold: Percentage rise to flag as rise (positive, e.g., 10.0)
        window_days: Rolling window for calculating change

    Returns:
        List of event dicts: {date, type, magnitude, nav_before, nav_after}
    """
    if nav_series.empty or len(nav_series) < window_days:
        return []

    df = nav_series.copy()
    value_col = "nav" if "nav" in df.columns else "current_value"

    # Calculate rolling returns over the window
    df["pct_change"] = df[value_col].pct_change(periods=window_days) * 100

    events = []
    last_event_date = None

    for _, row in df.iterrows():
        if pd.isna(row["pct_change"]):
            continue

        # Skip events too close to each other (at least 14 days apart)
        if last_event_date and (row["date"] - last_event_date).days < 14:
            continue

        if row["pct_change"] <= dip_threshold:
            events.append({
                "date": row["date"],
                "type": "dip",
                "magnitude": round(row["pct_change"], 2),
                "nav_value": round(row[value_col], 2),
            })
            last_event_date = row["date"]

        elif row["pct_change"] >= rise_threshold:
            events.append({
                "date": row["date"],
                "type": "rise",
                "magnitude": round(row["pct_change"], 2),
                "nav_value": round(row[value_col], 2),
            })
            last_event_date = row["date"]

    # Keep only the most significant events (top 10)
    if len(events) > 10:
        events.sort(key=lambda x: abs(x["magnitude"]), reverse=True)
        events = events[:10]
        events.sort(key=lambda x: x["date"])

    return events


def detect_drawdown_periods(
    nav_series: pd.DataFrame,
    threshold: float = -10.0,
) -> list[dict]:
    """
    Detect sustained drawdown periods where NAV drops more than threshold from peak.
    Returns list of {start_date, end_date, peak_value, trough_value, drawdown_pct}.
    """
    if nav_series.empty:
        return []

    df = nav_series.copy()
    value_col = "nav" if "nav" in df.columns else "current_value"

    df["peak"] = df[value_col].cummax()
    df["drawdown"] = (df[value_col] - df["peak"]) / df["peak"] * 100

    periods = []
    in_drawdown = False
    start_date = None
    peak_val = None

    for _, row in df.iterrows():
        if row["drawdown"] <= threshold and not in_drawdown:
            in_drawdown = True
            start_date = row["date"]
            peak_val = row["peak"]
        elif row["drawdown"] > threshold / 2 and in_drawdown:
            # Drawdown recovered
            trough_row = df[(df["date"] >= start_date) & (df["date"] <= row["date"])]
            trough_val = trough_row[value_col].min()
            periods.append({
                "start_date": start_date,
                "end_date": row["date"],
                "peak_value": round(peak_val, 2),
                "trough_value": round(trough_val, 2),
                "drawdown_pct": round((trough_val - peak_val) / peak_val * 100, 2),
            })
            in_drawdown = False

    return periods
