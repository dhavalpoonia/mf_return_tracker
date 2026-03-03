"""
MF SIP Analyzer — Main Streamlit application.
Compare your mutual fund SIP performance against peers, benchmarks & commodities.
"""

import streamlit as st
import pandas as pd
from datetime import date

from config import APP_TITLE, APP_ICON, APP_DESCRIPTION, RATINGS
from ui.input_form import render_input_form
from ui.charts import render_value_chart, render_returns_bar_chart, render_profit_loss_chart
from ui.comparison_table import render_comparison_table
from data.mf_data import get_nav_history
from data.benchmark_data import get_all_benchmark_data
from engine.sip_simulator import simulate_investment
from engine.metrics import calculate_all_metrics
from analysis.event_detector import detect_events
from analysis.news_search import get_event_explanations
from analysis.llm_analyzer import analyze_fund


# ─────────────────────────── Page Config ───────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────── Custom CSS ───────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Space Grotesk', sans-serif; }

    /* Root Colors and Background */
    :root {
        --bg-primary: #0a1120;
        --sidebar-bg: #0d1629;
        --accent-navy: #1e3a8a;
        --accent-green: #059669;
        --text-muted: #94a3b8;
        --card-bg: #111a2e;
        --border-color: #1e293b;
    }

    /* Brutilist Header */
    .main-header {
        background-color: var(--card-bg);
        border: 2px solid var(--accent-navy);
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: left;
    }
    .main-header h1 {
        color: #f8fafc;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: var(--text-muted);
        font-size: 0.95rem;
        margin-top: 0.5rem;
        max-width: 800px;
    }

    /* Strict Metric cards */
    .metric-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        padding: 1.5rem;
        text-align: left;
    }
    .metric-card .label {
        color: var(--text-muted);
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    .metric-card .value {
        font-size: 1.5rem;
        font-weight: 600;
    }
    .metric-card .value.positive { color: var(--accent-green); }
    .metric-card .value.negative { color: #dc2626; }
    .metric-card .value.neutral { color: #f1f5f9; }

    /* Recommendation card - Minimalist */
    .rec-card {
        border-left: 5px solid;
        background: #0f172a;
        padding: 1.5rem;
        margin: 1.5rem 0;
    }
    .rec-continue { border-color: var(--accent-green); }
    .rec-pause { border-color: #d97706; }
    .rec-switch { border-color: #dc2626; }

    /* Section divider as simple line */
    .section-divider {
        border-top: 1px solid var(--border-color);
        margin: 2.5rem 0;
    }

    /* Event structured component */
    .event-container {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    .event-item {
        background: #0f172a;
        border: 1px solid var(--border-color);
        padding: 1rem;
    }
    .event-dip { border-top: 3px solid #dc2626; }
    .event-rise { border-top: 3px solid var(--accent-green); }

    /* Sidebar width and spacing */
    [data-testid="stSidebar"] {
        min-width: 350px !important;
        max-width: 450px !important;
    }
    [data-testid="stSidebar"] .css-1d391kg {
        padding: 2rem 1rem;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 1px solid var(--border-color);
    }
    .stTabs [data-baseweb="tab"] {
        color: var(--text-muted);
        padding-bottom: 0.5rem;
    }
    .stTabs [aria-selected="true"] {
        color: #f8fafc !important;
        border-bottom: 2px solid var(--accent-navy) !important;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Override all Streamlit Violet/Purple defaults */
    .stButton > button {
        background-color: var(--accent-navy) !important;
        color: white !important;
        border: none !important;
        border-radius: 0px !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    .stButton > button:hover {
        background-color: #1e40af !important;
        border: none !important;
    }
    
    /* Multiselect chips */
    div[data-baseweb="tag"] {
        background-color: var(--accent-navy) !important;
    }
    
    /* Tabs indicator */
    div[data-baseweb="tab-highlight"] {
        background-color: var(--accent-navy) !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: var(--accent-navy) !important;
    }

    /* Checkbox color */
    .stCheckbox > label > div[role="checkbox"][aria-checked="true"] {
        background-color: var(--accent-navy) !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────── Header ───────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1>{APP_TITLE}</h1>
    <p>{APP_DESCRIPTION}</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────── Sidebar Input ───────────────────────────
config = render_input_form()

# ─────────────────────────── Main Analysis ───────────────────────────
if config is None:
    # Show welcome screen
    st.markdown("""
    <div style="padding: 2rem 0;">
        <h2 style="color: #f8fafc; font-weight: 500;">Overview</h2>
        <p style="color: var(--text-muted); font-size: 1rem; max-width: 800px; margin-bottom: 2rem;">
            A quantitative dashboard to analyze and compare mutual fund SIP performance. 
            Simulate exact investment patterns across peer funds and relevant benchmarks to evaluate risk-adjusted returns.
        </p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem;">
            <div class="metric-card">
                <div class="label">Step 1</div>
                <div class="value neutral" style="font-size: 1.1rem;">Search Fund</div>
            </div>
            <div class="metric-card">
                <div class="label">Step 2</div>
                <div class="value neutral" style="font-size: 1.1rem;">Input SIP Parameters</div>
            </div>
            <div class="metric-card">
                <div class="label">Step 3</div>
                <div class="value neutral" style="font-size: 1.1rem;">Generate Comparison</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ═══════════════════════════ RUN ANALYSIS ═══════════════════════════

progress = st.progress(0, text="Starting analysis...")
simulation_results = {}
all_metrics = {}

# --- Step 1: Fetch primary fund NAV ---
progress.progress(5, text=f"Fetching NAV data for {config['fund_name'][:40]}...")

primary_nav = get_nav_history(config["fund_code"])
if primary_nav.empty:
    st.error("❌ Could not fetch NAV data for the selected fund. Please try again.")
    st.stop()

# --- Step 2: Simulate primary fund ---
progress.progress(15, text="Simulating your SIP investment...")

primary_sim = simulate_investment(
    nav_data=primary_nav,
    sip_amount=config["sip_amount"],
    sip_day=config["sip_day"],
    start_date=config["start_date"],
    end_date=config["end_date"],
    lumpsum_events=config["transactions"],
    step_up_pct=config["step_up_pct"],
)

if primary_sim.empty:
    st.error("❌ Simulation returned no data. Check your date range.")
    st.stop()

simulation_results[config["fund_name"]] = primary_sim
all_metrics[config["fund_name"]] = calculate_all_metrics(primary_sim)

# --- Step 3: Simulate peer funds ---
peer_funds = config["peer_funds"]
total_peers = len(peer_funds) + len(config["benchmarks"])
step_counter = 0

for code, name in peer_funds.items():
    step_counter += 1
    pct = 20 + int(40 * step_counter / max(total_peers, 1))
    progress.progress(pct, text=f"Fetching {name[:40]}...")

    nav = get_nav_history(code)
    if not nav.empty:
        sim = simulate_investment(
            nav_data=nav,
            sip_amount=config["sip_amount"],
            sip_day=config["sip_day"],
            start_date=config["start_date"],
            end_date=config["end_date"],
            lumpsum_events=config["transactions"],
            step_up_pct=config["step_up_pct"],
        )
        if not sim.empty:
            simulation_results[name] = sim
            all_metrics[name] = calculate_all_metrics(sim)

# --- Step 4: Simulate benchmarks ---
if config["benchmarks"]:
    progress.progress(65, text="Fetching benchmark data...")

    benchmark_data = get_all_benchmark_data(
        config["benchmarks"],
        config["start_date"],
        config["end_date"],
    )

    for bm_name, bm_nav in benchmark_data.items():
        step_counter += 1
        pct = 65 + int(15 * step_counter / max(total_peers, 1))
        progress.progress(min(pct, 80), text=f"Simulating {bm_name}...")

        sim = simulate_investment(
            nav_data=bm_nav,
            sip_amount=config["sip_amount"],
            sip_day=config["sip_day"],
            start_date=config["start_date"],
            end_date=config["end_date"],
            lumpsum_events=config["transactions"],
            step_up_pct=config["step_up_pct"],
        )
        if not sim.empty:
            simulation_results[bm_name] = sim
            all_metrics[bm_name] = calculate_all_metrics(sim)

# --- Step 5: Detect events ---
progress.progress(82, text="Detecting significant market events...")

events = detect_events(primary_nav)
event_explanations = {}

if events:
    progress.progress(85, text="Searching for event explanations...")
    try:
        short_name = config["fund_name"].split(" - ")[0] if " - " in config["fund_name"] else config["fund_name"]
        event_explanations = get_event_explanations(events, short_name)
    except Exception:
        event_explanations = {}

progress.progress(90, text="Rendering results...")

# ═══════════════════════════ DISPLAY RESULTS ═══════════════════════════

# --- Summary Metrics Cards ---
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown("## Fund Performance Summary")

primary_metrics = all_metrics[config["fund_name"]]
cols = st.columns(5)

metric_cards = [
    ("Total Invested", primary_metrics.get("Total Invested", 0), "neutral", "₹{:,.0f}"),
    ("Current Value", primary_metrics.get("Current Value", 0), "positive" if primary_metrics.get("Current Value", 0) > primary_metrics.get("Total Invested", 0) else "negative", "₹{:,.0f}"),
    ("Profit / Loss", primary_metrics.get("Profit/Loss", 0), "positive" if primary_metrics.get("Profit/Loss", 0) >= 0 else "negative", "₹{:,.0f}"),
    ("Absolute Return", primary_metrics.get("Absolute Return", 0), "positive" if primary_metrics.get("Absolute Return", 0) >= 0 else "negative", "{:.2f}%"),
    ("XIRR", primary_metrics.get("XIRR", 0) or 0, "positive" if (primary_metrics.get("XIRR") or 0) >= 0 else "negative", "{:.2f}%"),
]

for i, (label, value, cls, fmt) in enumerate(metric_cards):
    with cols[i]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value {cls}">{fmt.format(value)}</div>
        </div>
        """, unsafe_allow_html=True)

# --- Charts ---
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Performance History", "Returns Analysis", "P&L Distribution"])

with tab1:
    render_value_chart(simulation_results, events, event_explanations)

with tab2:
    render_returns_bar_chart(all_metrics)

with tab3:
    render_profit_loss_chart(all_metrics)

# --- Comparison Table ---
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
render_comparison_table(all_metrics, config["fund_name"])

# --- Market Events and AI Analysis ---
if events:
    with st.expander("Market Events Detected", expanded=False):
        st.caption(f"Significant NAV fluctuation events for {config['fund_name'].split(' - ')[0]}")
        st.markdown('<div class="event-container">', unsafe_allow_html=True)

        for event in events:
            date_str = str(event["date"])
            evt_class = "event-dip" if event["type"] == "dip" else "event-rise"
            explanation = ""

            if date_str in event_explanations:
                news = event_explanations[date_str].get("news", [])
                if news:
                    explanation = "<br>".join([
                        f"• <a href='{n['url']}' target='_blank'>{n['title']}</a>"
                        for n in news[:3] if n.get("title")
                    ])

            st.markdown(f"""
            <div class="event-item {evt_class}">
                <strong>{event['date'].strftime('%d %b %Y')}</strong>
                <br><span style="font-size: 1.1rem; font-weight: 500;">{'-' if event['type'] == 'dip' else '+'}{event['magnitude']:.1f}% Change</span>
                {f'<div style="margin-top: 0.5rem; font-size: 0.8rem; color: var(--text-muted);">{explanation}</div>' if explanation else ''}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- AI Analysis ---
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

if st.session_state.get("gemini_api_key"):
    st.markdown("## Quantitative Analysis Report")

    progress.progress(92, text="Running AI analysis (Analyst Agent)...")

    analysis = analyze_fund(
        fund_name=config["fund_name"],
        fund_category=config["fund_category"],
        all_metrics=all_metrics,
        events=events,
        event_explanations=event_explanations,
    )

    if analysis and analysis.get("final_recommendation"):
        rec = analysis["final_recommendation"]
        rating = rec.get("rating", "PAUSE").lower()

        # Get rating config
        rating_info = RATINGS.get(rating, RATINGS["pause"])

        st.markdown(f"""
        <div class="rec-card rec-{rating}">
            <h3 style="margin-top: 0;">Recommendation: {rating_info['label']}</h3>
            <p style="color: #cbd5e1; font-size: 1rem;">{rec.get('analyst_summary', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Key observations
        observations = rec.get("key_observations", [])
        if observations:
            st.markdown("#### Observations")
            for obs in observations:
                st.markdown(f"- {obs}")

        # Detailed sections in expanders
        with st.expander("Peer Comparison", expanded=False):
            st.markdown(rec.get("peer_comparison", "N/A"))

        with st.expander("Benchmark Context", expanded=False):
            st.markdown(rec.get("benchmark_comparison", "N/A"))

        with st.expander("Risk Factors", expanded=False):
            st.markdown(rec.get("risk_assessment", "N/A"))

        with st.expander("Strategic Reasoning", expanded=True):
            st.markdown(rec.get("recommendation_reasoning", "N/A"))

        # Reviewer's notes
        if not rec.get("reviewer_agrees", True):
            st.warning("⚠️ **Reviewer Disagreement**: The reviewing agent disagreed with some aspects:")
            for correction in rec.get("reviewer_corrections", []):
                st.markdown(f"- {correction}")

        reviewer_summary = rec.get("reviewer_summary", "")
        if reviewer_summary:
            with st.expander("Internal Audit Notes", expanded=False):
                st.markdown(reviewer_summary)

        # Confidence badge
        confidence = rec.get("confidence", "MEDIUM")
        conf_colors = {"HIGH": "#00e676", "MEDIUM": "#ff9100", "LOW": "#ff1744"}
        st.markdown(f"""
        <div style="text-align: right; margin-top: 1rem;">
            <span style="background: {conf_colors.get(confidence, '#ff9100')}22;
                         color: {conf_colors.get(confidence, '#ff9100')};
                         padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;
                         border: 1px solid {conf_colors.get(confidence, '#ff9100')}44;">
                Confidence: {confidence}
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("AI analysis could not generate a recommendation. This might be due to API limits.")
else:
    st.markdown("""
    <div class="metric-card" style="text-align: left; padding: 2rem; border-left: 3px solid var(--accent-navy);">
        <div class="label">AI Insight</div>
        <div class="value neutral" style="font-size: 1rem;">
            Key missing for analysis. Enter Gemini API key in sidebar.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Complete
progress.progress(100, text="Analysis complete!")

# --- Disclaimer ---
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #555; font-size: 0.75rem;">
    ⚠️ <b>Disclaimer:</b> This tool is for educational and informational purposes only.
    It does not constitute financial advice. Past performance does not guarantee future returns.
    Always consult a qualified financial advisor before making investment decisions.
    <br>Data sourced from <a href="https://mfapi.in" target="_blank">mfapi.in</a> (AMFI) and
    <a href="https://finance.yahoo.com" target="_blank">Yahoo Finance</a>.
</div>
""", unsafe_allow_html=True)
