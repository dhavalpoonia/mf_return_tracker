"""
User input form for fund selection, SIP configuration, and transaction log.
"""

import streamlit as st
from datetime import date, timedelta
from data.mf_data import search_funds
from data.fund_categories import (
    detect_category,
    get_peer_funds,
    get_relevant_benchmarks,
    get_all_categories,
    get_funds_by_category,
)
from data.benchmark_data import get_available_benchmarks


def render_input_form() -> dict | None:
    """
    Render the input form in the sidebar.
    Returns a configuration dict when user clicks Analyze, or None.
    """

    st.sidebar.markdown("## Fund Selection")

    # --- Fund Search ---
    search_query = st.sidebar.text_input(
        "Search mutual fund by name",
        placeholder="e.g., Quant Small Cap Fund",
        key="fund_search",
    )

    selected_fund = None
    selected_code = None

    if search_query and len(search_query) >= 3:
        with st.sidebar.status("Searching funds...", expanded=False):
            results = search_funds(search_query)

        if results:
            fund_options = {r["schemeCode"]: r["schemeName"] for r in results[:15]}
            selected_code = st.sidebar.selectbox(
                "Select fund",
                options=list(fund_options.keys()),
                format_func=lambda x: fund_options[x],
                key="fund_select",
            )
            if selected_code:
                selected_fund = fund_options[selected_code]
        else:
            st.sidebar.warning("No funds found. Try a different search term.")

    if not selected_fund:
        st.sidebar.info("Start by searching for your mutual fund above")
        return None

    # Show detected category
    category = detect_category(selected_fund)
    if category:
        st.sidebar.success(f"📁 Category: **{category}**")

    st.sidebar.markdown("---")
    st.sidebar.markdown("## SIP Configuration")

    # --- SIP Details ---
    col1, col2 = st.sidebar.columns(2)
    with col1:
        sip_amount = st.number_input(
            "SIP Amount (₹)",
            min_value=100,
            max_value=10000000,
            value=10000,
            step=500,
            key="sip_amount",
        )
    with col2:
        sip_day = st.number_input(
            "SIP Date (day)",
            min_value=1,
            max_value=28,
            value=3,
            key="sip_day",
            help="Day of month when SIP is deducted (1-28)",
        )

    col3, col4 = st.sidebar.columns(2)
    with col3:
        start_date = st.date_input(
            "SIP Start Date",
            value=date(2023, 4, 2),
            min_value=date(2010, 1, 1),
            max_value=date.today(),
            key="start_date",
        )
    with col4:
        end_date = st.date_input(
            "Analysis End Date",
            value=date.today(),
            min_value=start_date,
            max_value=date.today(),
            key="end_date",
        )

    step_up = st.sidebar.number_input(
        "Annual Step-Up (%)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=5.0,
        key="step_up",
        help="Increase SIP amount annually by this percentage",
    )

    # --- Transaction Log (Lumpsum / Withdrawal) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("## Additional Transactions")
    st.sidebar.caption("Add lumpsum investments (+) or withdrawals (-)")

    if "transactions" not in st.session_state:
        st.session_state.transactions = []

    # Add transaction form
    with st.sidebar.expander("Add Transaction or Withdrawal", expanded=len(st.session_state.transactions) == 0):
        tx_type = st.selectbox(
            "Type",
            ["Lumpsum Investment", "Withdrawal"],
            key="tx_type",
        )
        tx_date = st.date_input(
            "Date",
            value=date.today() - timedelta(days=30),
            min_value=start_date,
            max_value=end_date,
            key="tx_date",
        )
        tx_amount = st.number_input(
            "Amount (₹)",
            min_value=1000,
            max_value=100000000,
            value=100000,
            step=10000,
            key="tx_amount",
        )

        if st.button("Add Transaction", key="add_tx"):
            amount = tx_amount if tx_type == "Lumpsum Investment" else -tx_amount
            st.session_state.transactions.append({
                "date": tx_date,
                "amount": amount,
                "type": tx_type,
            })
            st.rerun()

    if st.session_state.transactions:
        for i, tx in enumerate(st.session_state.transactions):
            type_label = "Lumpsum" if tx["amount"] > 0 else "Withdrawal"
            col_a, col_b = st.sidebar.columns([4, 1])
            with col_a:
                st.caption(f"{emoji} {tx['type']}: ₹{abs(tx['amount']):,.0f} on {tx['date']}")
            with col_b:
                if st.button("❌", key=f"del_tx_{i}"):
                    st.session_state.transactions.pop(i)
                    st.rerun()

    # --- Comparison Funds ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("## Peer Comparison")

    # Auto-suggest peer funds
    peer_funds = get_peer_funds(str(selected_code), selected_fund)
    selected_peers = {}

    if peer_funds:
        st.sidebar.caption(f"Suggested peers ({category or 'same category'}):")
        for code, name in list(peer_funds.items())[:6]:
            short_name = name.split(" - ")[0] if " - " in name else name
            if st.sidebar.checkbox(short_name, value=True, key=f"peer_{code}"):
                selected_peers[code] = name

    # Manual fund search for additional comparison
    with st.sidebar.expander("Search & add more funds"):
        extra_search = st.text_input("Search fund", key="extra_fund_search")
        if extra_search and len(extra_search) >= 3:
            extra_results = search_funds(extra_search)
            if extra_results:
                extra_options = {r["schemeCode"]: r["schemeName"] for r in extra_results[:10]}
                for code, name in extra_options.items():
                    short = name.split(" - ")[0] if " - " in name else name
                    if st.checkbox(short, key=f"extra_{code}"):
                        selected_peers[code] = name

    # --- Benchmarks ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("## Benchmarks")

    all_benchmarks = get_available_benchmarks()
    relevant = get_relevant_benchmarks(selected_fund) if selected_fund else []
    selected_benchmarks = []

    for bm_name in all_benchmarks:
        default_on = bm_name in relevant
        if st.sidebar.checkbox(bm_name, value=default_on, key=f"bm_{bm_name}"):
            selected_benchmarks.append(bm_name)

    # --- Gemini API Key ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("## AI Analysis")
    api_key = st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        key="gemini_key_input",
        help="Get a free key from https://aistudio.google.com/apikey",
        placeholder="Paste your Gemini API key",
    )
    if api_key:
        st.session_state.gemini_api_key = api_key

    # --- Analyze Button ---
    st.sidebar.markdown("---")
    analyze = st.sidebar.button(
        "Analyze Fund Performance",
        type="primary",
        use_container_width=True,
        key="analyze_btn",
    )

    if analyze:
        return {
            "fund_code": str(selected_code),
            "fund_name": selected_fund,
            "fund_category": category or "Unknown",
            "sip_amount": sip_amount,
            "sip_day": sip_day,
            "start_date": start_date,
            "end_date": end_date,
            "step_up_pct": step_up,
            "transactions": [
                {"date": tx["date"], "amount": tx["amount"]}
                for tx in st.session_state.transactions
            ],
            "peer_funds": selected_peers,
            "benchmarks": selected_benchmarks,
        }

    return None
