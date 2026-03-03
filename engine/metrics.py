"""
Return metrics calculations: Absolute Return, XIRR, CAGR, Max Drawdown, Volatility.
"""

import pandas as pd
import numpy as np
from datetime import date

try:
    from pyxirr import xirr as pyxirr_xirr
    HAS_PYXIRR = True
except ImportError:
    HAS_PYXIRR = False


def absolute_return(total_invested: float, current_value: float) -> float:
    """Calculate absolute return percentage."""
    if total_invested <= 0:
        return 0.0
    return ((current_value - total_invested) / total_invested) * 100


def profit_loss(total_invested: float, current_value: float) -> float:
    """Calculate profit/loss amount."""
    return current_value - total_invested


def calculate_xirr(cashflows: list[tuple[date, float]]) -> float | None:
    """
    Calculate XIRR (Extended Internal Rate of Return) for irregular cashflows.
    cashflows: list of (date, amount) — negative for investments, positive for withdrawals/final value.
    Returns annualized return as percentage, or None if calculation fails.
    """
    if not cashflows or len(cashflows) < 2:
        return None

    try:
        if HAS_PYXIRR:
            dates = [cf[0] for cf in cashflows]
            amounts = [cf[1] for cf in cashflows]
            result = pyxirr_xirr(dates, amounts)
            if result is not None and not np.isnan(result):
                return result * 100  # Convert to percentage
        # Fallback: simple Newton-Raphson XIRR
        return _xirr_newton(cashflows)
    except Exception:
        return None


def _xirr_newton(cashflows: list[tuple[date, float]], max_iter: int = 1000) -> float | None:
    """Newton-Raphson method for XIRR calculation."""
    try:
        dates = [cf[0] for cf in cashflows]
        amounts = [cf[1] for cf in cashflows]
        base_date = min(dates)

        # Days from base for each cashflow
        day_fracs = [(d - base_date).days / 365.25 for d in dates]

        # Newton-Raphson
        rate = 0.1  # Initial guess

        for _ in range(max_iter):
            npv = sum(a / (1 + rate) ** t for a, t in zip(amounts, day_fracs))
            dnpv = sum(-t * a / (1 + rate) ** (t + 1) for a, t in zip(amounts, day_fracs))

            if abs(dnpv) < 1e-12:
                break

            new_rate = rate - npv / dnpv

            if abs(new_rate - rate) < 1e-9:
                return new_rate * 100

            rate = new_rate

            # Guard against divergence
            if abs(rate) > 100:
                return None

        return rate * 100
    except Exception:
        return None


def cagr(start_value: float, end_value: float, years: float) -> float:
    """Calculate Compound Annual Growth Rate."""
    if start_value <= 0 or years <= 0:
        return 0.0
    return ((end_value / start_value) ** (1 / years) - 1) * 100


def max_drawdown(value_series: pd.Series) -> float:
    """
    Calculate maximum drawdown (peak-to-trough decline) as a percentage.
    Returns a negative number (e.g., -15.5 for 15.5% drawdown).
    """
    if value_series.empty or len(value_series) < 2:
        return 0.0

    cummax = value_series.cummax()
    drawdowns = (value_series - cummax) / cummax * 100
    return drawdowns.min()


def volatility(value_series: pd.Series) -> float:
    """
    Calculate annualized volatility (standard deviation of daily returns).
    Returns value as percentage.
    """
    if value_series.empty or len(value_series) < 10:
        return 0.0

    daily_returns = value_series.pct_change().dropna()
    return daily_returns.std() * np.sqrt(252) * 100  # Annualized


def calculate_all_metrics(sim_result: pd.DataFrame) -> dict:
    """
    Calculate all metrics for a simulation result.
    Returns dict with metric name → value.
    """
    if sim_result.empty:
        return {
            "Total Invested": 0,
            "Current Value": 0,
            "Profit/Loss": 0,
            "Absolute Return": 0,
            "XIRR": None,
            "Max Drawdown": 0,
        }

    last_row = sim_result.iloc[-1]
    invested = last_row["total_invested"] - last_row.get("total_withdrawn", 0)
    current = last_row["current_value"]

    # XIRR from stored cashflows
    cashflows = sim_result.attrs.get("cashflows", [])
    xirr_val = calculate_xirr(cashflows) if cashflows else None

    return {
        "Total Invested": last_row["total_invested"],
        "Current Value": current,
        "Profit/Loss": profit_loss(invested, current),
        "Absolute Return": absolute_return(invested, current),
        "XIRR": xirr_val,
        "Max Drawdown": max_drawdown(sim_result["current_value"]),
    }
