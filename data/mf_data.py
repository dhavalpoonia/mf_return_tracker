"""
Mutual Fund NAV data fetching from mfapi.in (free, no API key).
"""

import requests
import pandas as pd
import streamlit as st
from datetime import datetime


MFAPI_BASE = "https://api.mfapi.in"


@st.cache_data(ttl=86400, show_spinner=False)
def search_funds(query: str) -> list[dict]:
    """
    Search mutual fund schemes by name.
    Returns list of {schemeCode, schemeName}.
    """
    try:
        resp = requests.get(f"{MFAPI_BASE}/mf/search", params={"q": query}, timeout=15)
        resp.raise_for_status()
        results = resp.json()
        # Filter to only Direct Growth plans for cleaner results
        filtered = []
        for item in results:
            name = item.get("schemeName", "").upper()
            if "DIRECT" in name and "GROWTH" in name:
                filtered.append(item)
        return filtered if filtered else results  # Fallback to all if no direct plans found
    except Exception as e:
        st.error(f"Error searching funds: {e}")
        return []


@st.cache_data(ttl=86400, show_spinner=False)
def get_nav_history(scheme_code: str) -> pd.DataFrame:
    """
    Fetch full NAV history for a scheme.
    Returns DataFrame with columns: [date, nav] sorted by date ascending.
    """
    try:
        resp = requests.get(f"{MFAPI_BASE}/mf/{scheme_code}", timeout=30)
        resp.raise_for_status()
        data = resp.json()

        nav_data = data.get("data", [])
        if not nav_data:
            return pd.DataFrame(columns=["date", "nav"])

        records = []
        for entry in nav_data:
            try:
                dt = datetime.strptime(entry["date"], "%d-%m-%Y").date()
                nav = float(entry["nav"])
                records.append({"date": dt, "nav": nav})
            except (ValueError, KeyError):
                continue

        df = pd.DataFrame(records)
        df = df.sort_values("date").reset_index(drop=True)
        df = df.drop_duplicates(subset=["date"], keep="last")
        return df

    except Exception as e:
        st.error(f"Error fetching NAV for scheme {scheme_code}: {e}")
        return pd.DataFrame(columns=["date", "nav"])


@st.cache_data(ttl=86400, show_spinner=False)
def get_scheme_info(scheme_code: str) -> dict:
    """
    Get scheme metadata (name, category, fund house, etc.).
    """
    try:
        resp = requests.get(f"{MFAPI_BASE}/mf/{scheme_code}", timeout=15)
        resp.raise_for_status()
        data = resp.json()
        meta = data.get("meta", {})
        return {
            "scheme_code": meta.get("scheme_code", scheme_code),
            "scheme_name": meta.get("scheme_name", "Unknown"),
            "fund_house": meta.get("fund_house", "Unknown"),
            "scheme_type": meta.get("scheme_type", "Unknown"),
            "scheme_category": meta.get("scheme_category", "Unknown"),
        }
    except Exception:
        return {"scheme_code": scheme_code, "scheme_name": "Unknown"}


@st.cache_data(ttl=3600, show_spinner=False)
def get_latest_nav(scheme_code: str) -> float | None:
    """Get the latest NAV for a scheme."""
    try:
        resp = requests.get(f"{MFAPI_BASE}/mf/{scheme_code}/latest", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        nav_list = data.get("data", [])
        if nav_list:
            return float(nav_list[0]["nav"])
    except Exception:
        pass
    return None
