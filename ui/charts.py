"""
Interactive Plotly charts for fund comparison visualization.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
from config import MAX_CHART_LINES


# Color palette for chart lines
# Color palette for chart lines (Navy, Green, Slate, Grey, Orange-Red)
CHART_COLORS = [
    "#3b82f6",  # Blue
    "#10b981",  # Green
    "#64748b",  # Slate
    "#f59e0b",  # Amber
    "#ef4444",  # Red
    "#06b6d4",  # Cyan
    "#8b5cf6",  # Violet (Wait, user said no purple, I'll use Indigo #4f46e5 which is blue-ish or just more blues)
    "#0ea5e9",  # Sky
    "#14b8a6",  # Teal
    "#f43f5e",  # Rose
]

# Better palette: strict minimalist
CHART_COLORS = [
    "#1e40af", # Deep Navy
    "#059669", # Green
    "#475569", # Slate
    "#0891b2", # Cyan
    "#dc2626", # Red
    "#4b5563", # Grey
    "#0369a1", # Sky
    "#0d9488", # Teal
    "#b91c1c", # Maroon
    "#334155", # Dark Slate
]


def _apply_chart_theme(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply consistent dark theme to Plotly figures."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color="#f8fafc")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.5)",
        font=dict(family="Space Grotesk, sans-serif", color="#94a3b8"),
        legend=dict(
            bgcolor="rgba(15,23,42,0.8)",
            bordercolor="rgba(30,58,138,0.3)",
            borderwidth=1,
            font=dict(size=10),
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.06)",
            zerolinecolor="rgba(255,255,255,0.1)",
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.06)",
            zerolinecolor="rgba(255,255,255,0.1)",
        ),
        hovermode="x unified",
        margin=dict(l=60, r=30, t=60, b=40),
    )
    return fig


def render_value_chart(
    simulation_results: dict[str, pd.DataFrame],
    events: list[dict] | None = None,
    event_explanations: dict | None = None,
) -> None:
    """
    Render the main investment value comparison chart.
    Shows current_value over time for each fund/benchmark.
    """
    if not simulation_results:
        st.info("No data to display.")
        return

    # Let user select which lines to show (max 5)
    all_names = list(simulation_results.keys())
    primary_fund = all_names[0] if all_names else None
    
    st.markdown("##### Filter Visibility")
    
    # Ensure selections are valid and include the primary fund
    if "chart_selections" not in st.session_state:
        st.session_state.chart_selections = all_names[:MAX_CHART_LINES]
    
    # Filter out any old selections not in current all_names to prevent StreamlitAPIException
    valid_selections = [s for s in st.session_state.chart_selections if s in all_names]
    
    # Always ensure primary fund is selected
    if primary_fund and primary_fund not in valid_selections:
        valid_selections.insert(0, primary_fund)
    
    # Truncate to max allowed
    valid_selections = valid_selections[:MAX_CHART_LINES]

    selected = st.multiselect(
        "Select up to 5 funds/benchmarks to compare",
        options=all_names,
        default=valid_selections,
        max_selections=MAX_CHART_LINES,
        key="main_chart_multiselect"
    )

    st.session_state.chart_selections = selected

    if not selected:
        st.info("Select at least one fund to display comparison.")
        return

    # Build chart
    fig = go.Figure()

    for i, name in enumerate(selected):
        df = simulation_results[name]
        if df.empty:
            continue

        color = CHART_COLORS[i % len(CHART_COLORS)]
        short_name = name.split(" - ")[0] if " - " in name else name

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["current_value"],
            mode="lines",
            name=short_name[:25],
            line=dict(color=color, width=2.5),
            hovertemplate=f"<b>{short_name[:20]}</b><br>₹%{{y:,.0f}}<extra></extra>",
        ))

    # Add "Amount Invested" line (from the first selected fund — it's same for all)
    first_df = simulation_results[selected[0]]
    if not first_df.empty:
        fig.add_trace(go.Scatter(
            x=first_df["date"],
            y=first_df["net_invested"],
            mode="lines",
            name="Amount Invested",
            line=dict(color="rgba(255,255,255,0.3)", width=1.5, dash="dash"),
            hovertemplate="<b>Invested</b><br>₹%{y:,.0f}<extra></extra>",
        ))

    # Add event markers
    if events and event_explanations:
        for event in events:
            date_str = str(event["date"])
            explanation = ""
            if date_str in event_explanations:
                explanation = event_explanations[date_str].get("summary", "")[:100]

            color_marker = "#dc2626" if event["type"] == "dip" else "#059669"
            symbol = "triangle-down" if event["type"] == "dip" else "triangle-up"

            # Find the y-value for the primary fund at this date
            ref_df = simulation_results.get(primary_fund, pd.DataFrame())
            y_val = None
            if not ref_df.empty:
                mask = ref_df["date"] == event["date"]
                if mask.any():
                    y_val = ref_df[mask]["current_value"].values[0]

            if y_val is not None:
                fig.add_trace(go.Scatter(
                    x=[event["date"]],
                    y=[y_val],
                    mode="markers",
                    marker=dict(color=color_marker, size=12, symbol=symbol, line=dict(width=1, color="white")),
                    name=f"{'Dip' if event['type'] == 'dip' else 'Rise'} {event['magnitude']:.1f}%",
                    hovertemplate=f"<b>{'📉 Dip' if event['type'] == 'dip' else '📈 Rise'}: {event['magnitude']:.1f}%</b><br>{explanation}<extra></extra>",
                    showlegend=False,
                ))

    _apply_chart_theme(fig, "Portfolio Value History")
    fig.update_yaxes(title="Portfolio Value (₹)", tickformat=",")
    fig.update_xaxes(title="Date")

    st.plotly_chart(fig, use_container_width=True, config={
        "displayModeBar": True,
        "modeBarButtonsToAdd": ["toggleFullScreen"],
        "displaylogo": False,
    })


def render_returns_bar_chart(all_metrics: dict[str, dict]) -> None:
    """Render a bar chart comparing absolute returns across all entities."""
    if not all_metrics:
        return

    names = []
    returns_vals = []
    xirr_vals = []
    colors = []

    for i, (name, metrics) in enumerate(all_metrics.items()):
        short_name = name.split(" - ")[0] if " - " in name else name
        names.append(short_name[:25])
        returns_vals.append(metrics.get("Absolute Return", 0))
        xirr_val = metrics.get("XIRR")
        xirr_vals.append(xirr_val if xirr_val is not None else 0)
        colors.append(CHART_COLORS[i % len(CHART_COLORS)])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=names,
        y=returns_vals,
        name="Absolute Return %",
        marker_color=colors,
        text=[f"{v:.1f}%" for v in returns_vals],
        textposition="outside",
        textfont=dict(color="#fafafa"),
    ))

    fig.add_trace(go.Bar(
        x=names,
        y=xirr_vals,
        name="XIRR %",
        marker_color=[
            f"rgba({int(c[1:3], 16)},{int(c[3:5], 16)},{int(c[5:7], 16)},0.5)" if c.startswith("#") else c
            for c in colors
        ],
        text=[f"{v:.1f}%" for v in xirr_vals],
        textposition="outside",
        textfont=dict(color="#fafafa"),
    ))

    _apply_chart_theme(fig, "Comparative Returns Analysis")
    fig.update_layout(barmode="group", xaxis_tickangle=-30)
    fig.update_yaxes(title="Return (%)")

    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})


def render_profit_loss_chart(all_metrics: dict[str, dict]) -> None:
    """Render a horizontal bar chart showing profit/loss for each fund."""
    if not all_metrics:
        return

    names = []
    pnl_vals = []
    colors = []

    for name, metrics in all_metrics.items():
        short_name = name.split(" - ")[0] if " - " in name else name
        names.append(short_name[:25])
        pnl = metrics.get("Profit/Loss", 0)
        pnl_vals.append(pnl)
        colors.append("#00e676" if pnl >= 0 else "#ff1744")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=names,
        x=pnl_vals,
        orientation="h",
        marker_color=colors,
        text=[f"₹{abs(v):,.0f}" for v in pnl_vals],
        textposition="outside",
        textfont=dict(color="#fafafa"),
    ))

    _apply_chart_theme(fig, "Net Profit / Loss Distribution")
    fig.update_xaxes(title="Profit/Loss (₹)", tickformat=",")

    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
