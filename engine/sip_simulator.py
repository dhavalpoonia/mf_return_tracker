"""
SIP/Lumpsum/Withdrawal simulation engine.
Simulates real-world mutual fund investment scenarios with custom SIP dates.
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


def _find_nearest_nav_date(nav_df: pd.DataFrame, target_date: date, direction: str = "forward") -> int | None:
    """
    Find the index of the nearest NAV date to the target date.
    direction='forward' finds the next available date (for buying on non-trading days).
    direction='backward' finds the previous available date.
    """
    dates = nav_df["date"].values

    if direction == "forward":
        mask = nav_df["date"] >= target_date
        if mask.any():
            return nav_df[mask].index[0]
    else:
        mask = nav_df["date"] <= target_date
        if mask.any():
            return nav_df[mask].index[-1]
    return None


def _get_sip_dates(sip_day: int, start_date: date, end_date: date) -> list[date]:
    """
    Generate list of SIP dates from start to end.
    SIP day is clamped to valid day for each month (e.g., 31st → 28th in Feb).
    """
    dates = []
    current = start_date.replace(day=min(sip_day, 28))

    # If start_date's day is after sip_day, start from this month
    # Otherwise, use the current month
    if start_date.day > sip_day:
        current = current + relativedelta(months=1)
    elif start_date.day <= sip_day:
        current = start_date.replace(day=min(sip_day, 28))

    while current <= end_date:
        # Clamp day to valid range for this month
        import calendar
        max_day = calendar.monthrange(current.year, current.month)[1]
        actual_date = current.replace(day=min(sip_day, max_day))
        dates.append(actual_date)
        current = current + relativedelta(months=1)

    return dates


def simulate_investment(
    nav_data: pd.DataFrame,
    sip_amount: float,
    sip_day: int,
    start_date: date,
    end_date: date,
    lumpsum_events: list[dict] | None = None,
    step_up_pct: float = 0.0,
) -> pd.DataFrame:
    """
    Simulate SIP/Lumpsum/Withdrawal investment on a NAV time series.

    Args:
        nav_data: DataFrame with columns [date, nav]
        sip_amount: Monthly SIP amount (₹)
        sip_day: Day of month for SIP (1-28)
        start_date: SIP start date
        end_date: Analysis end date
        lumpsum_events: List of {date: date, amount: float}
                        Positive = lumpsum addition, Negative = withdrawal
        step_up_pct: Annual SIP step-up percentage (e.g., 10 for 10%)

    Returns:
        DataFrame with columns: [date, nav, units_held, total_invested,
                                  total_withdrawn, current_value, net_invested]
    """
    if nav_data.empty:
        return pd.DataFrame()

    if lumpsum_events is None:
        lumpsum_events = []

    # Ensure nav_data is sorted and indexed properly
    nav_df = nav_data.copy().reset_index(drop=True)

    # Filter NAV data to our date range (with small buffer)
    nav_df = nav_df[(nav_df["date"] >= start_date - timedelta(days=7)) &
                     (nav_df["date"] <= end_date + timedelta(days=7))].reset_index(drop=True)

    if nav_df.empty:
        return pd.DataFrame()

    # Generate SIP dates
    sip_dates = _get_sip_dates(sip_day, start_date, end_date)

    # Build event list: SIP dates + lumpsum/withdrawal events
    events = []
    current_sip = sip_amount
    last_step_up_year = start_date.year

    for sd in sip_dates:
        # Apply annual step-up
        if step_up_pct > 0 and sd.year > last_step_up_year:
            years_elapsed = sd.year - start_date.year
            current_sip = sip_amount * ((1 + step_up_pct / 100) ** years_elapsed)
            last_step_up_year = sd.year

        events.append({"date": sd, "amount": current_sip, "type": "sip"})

    for le in lumpsum_events:
        events.append({"date": le["date"], "amount": le["amount"], "type": "lumpsum"})

    # Sort events by date
    events.sort(key=lambda x: x["date"])

    # Simulate day by day
    units_held = 0.0
    total_invested = 0.0
    total_withdrawn = 0.0
    cashflows = []  # For XIRR: (date, amount) — negative = investment, positive = withdrawal

    records = []
    event_idx = 0

    for i, row in nav_df.iterrows():
        current_date = row["date"]
        current_nav = row["nav"]

        # Process any events on or before this date
        while event_idx < len(events):
            event = events[event_idx]
            event_date = event["date"]

            if event_date > current_date:
                break

            # Find the NAV for this event date (use current or next available)
            # We process it at the current nav_df row if event_date <= current_date
            nav_idx = _find_nearest_nav_date(nav_df, event_date, direction="forward")
            if nav_idx is not None and nav_df.loc[nav_idx, "date"] == current_date:
                event_nav = current_nav
                amount = event["amount"]

                if amount > 0:
                    # Buy units
                    units_bought = amount / event_nav
                    units_held += units_bought
                    total_invested += amount
                    cashflows.append((current_date, -amount))
                elif amount < 0:
                    # Sell units (withdrawal)
                    withdraw_amount = abs(amount)
                    units_to_sell = withdraw_amount / event_nav
                    units_held = max(0, units_held - units_to_sell)
                    total_withdrawn += withdraw_amount
                    cashflows.append((current_date, withdraw_amount))

                event_idx += 1
            elif nav_idx is not None and nav_df.loc[nav_idx, "date"] > current_date:
                break  # Wait for the correct NAV date
            else:
                event_idx += 1  # Skip events that can't be matched

        current_value = units_held * current_nav
        net_invested = total_invested - total_withdrawn

        records.append({
            "date": current_date,
            "nav": current_nav,
            "units_held": units_held,
            "total_invested": total_invested,
            "total_withdrawn": total_withdrawn,
            "net_invested": net_invested,
            "current_value": current_value,
        })

    result_df = pd.DataFrame(records)

    # Store cashflows for XIRR calculation
    if not result_df.empty:
        # Add final value as positive cashflow for XIRR
        final_cashflows = cashflows.copy()
        final_date = result_df.iloc[-1]["date"]
        final_value = result_df.iloc[-1]["current_value"]
        final_cashflows.append((final_date, final_value))
        result_df.attrs["cashflows"] = final_cashflows

    return result_df
