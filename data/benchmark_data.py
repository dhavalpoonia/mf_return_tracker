"""
Benchmark and commodity data fetching from Yahoo Finance (yfinance).
Handles Nifty indices, Gold, Silver ETFs for Indian market comparison.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import date, timedelta
from config import BENCHMARKS


@st.cache_data(ttl=86400, show_spinner=False)
def get_benchmark_data(ticker: str, start_date: date, end_date: date) -> pd.DataFrame:
    """
    Fetch historical price data for a benchmark/commodity ticker.
    Returns DataFrame with columns: [date, nav] (we call price 'nav' for consistency).
    """
    try:
        # Add buffer days to ensure we have data covering the full range
        fetch_start = start_date - timedelta(days=10)
        fetch_end = end_date + timedelta(days=5)

        df = yf.download(
            ticker,
            start=fetch_start.isoformat(),
            end=fetch_end.isoformat(),
            progress=False,
            auto_adjust=True,
        )

        if df.empty:
            return pd.DataFrame(columns=["date", "nav"])

        # Handle multi-level columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        result = pd.DataFrame({
            "date": pd.to_datetime(df["Date"]).dt.date,
            "nav": df["Close"].astype(float),
        })

        result = result.dropna(subset=["nav"])
        result = result.sort_values("date").reset_index(drop=True)
        result = result.drop_duplicates(subset=["date"], keep="last")

        return result

    except Exception as e:
        st.warning(f"Could not fetch data for {ticker}: {e}")
        return pd.DataFrame(columns=["date", "nav"])


def get_available_benchmarks() -> dict[str, str]:
    """Return the dictionary of available benchmarks {display_name: ticker}."""
    return BENCHMARKS.copy()


@st.cache_data(ttl=86400, show_spinner=False)
def get_all_benchmark_data(
    selected_benchmarks: list[str],
    start_date: date,
    end_date: date,
) -> dict[str, pd.DataFrame]:
    """
    Fetch data for multiple benchmarks at once.
    Returns {benchmark_name: DataFrame with [date, nav]}.
    """
    result = {}
    for name in selected_benchmarks:
        ticker = BENCHMARKS.get(name)
        if ticker:
            df = get_benchmark_data(ticker, start_date, end_date)
            if not df.empty:
                result[name] = df
    return result
