"""
Comparison metrics table with color-coded performance indicators.
"""

import pandas as pd
import streamlit as st


def render_comparison_table(all_metrics: dict[str, dict], primary_fund: str) -> None:
    """
    Render a structured comparison table with funds as rows and metrics as columns.
    """
    if not all_metrics:
        st.info("No comparison data available.")
        return

    st.markdown("### Comparative Performance Matrix")

    # Build structured data
    rows = []
    for fund_name, metrics in all_metrics.items():
        short_name = fund_name.split(" - ")[0] if " - " in fund_name else fund_name
        
        row = {
            "Entity": short_name,
            "Total Invested": metrics.get("Total Invested", 0),
            "Current Value": metrics.get("Current Value", 0),
            "P&L": metrics.get("Profit/Loss", 0),
            "Absolute %": metrics.get("Absolute Return", 0),
            "XIRR %": metrics.get("XIRR", 0) or 0,
            "Max DD %": metrics.get("Max Drawdown", 0),
            "CAGR %": metrics.get("CAGR", 0),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    
    # Sort by XIRR descending
    df = df.sort_values(by="XIRR %", ascending=False)
    
    # Format for display
    def _format_values(df_to_format):
        fmt_df = df_to_format.copy()
        
        # Currency formatting
        currency_cols = ["Total Invested", "Current Value", "P&L"]
        for col in currency_cols:
            if col in fmt_df.columns:
                fmt_df[col] = fmt_df[col].apply(lambda x: f"₹{x:,.0f}" if pd.notnull(x) else "N/A")
        
        # Percentage formatting
        pct_cols = ["Absolute %", "XIRR %", "Max DD %", "CAGR %"]
        for col in pct_cols:
            if col in fmt_df.columns:
                fmt_df[col] = fmt_df[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
        
        return fmt_df

    display_df = _format_values(df)

    # Brutalist styling for the table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )

    st.caption("All simulations apply the user-specified transaction schedule to historical data.")

