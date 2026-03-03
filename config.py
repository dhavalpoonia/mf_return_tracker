"""
Configuration constants for the Mutual Fund Comparison App.
Contains fund categories, benchmark tickers, and app settings.
"""

# ─────────────────────────── App Settings ───────────────────────────
APP_TITLE = "MF Performance Analyzer"
APP_ICON = ""
APP_DESCRIPTION = "Quantitative comparison of mutual fund SIP performance against peers and benchmarks"

# Maximum number of funds/benchmarks visible on chart at once
MAX_CHART_LINES = 5

# Cache TTL in seconds (24 hours)
CACHE_TTL = 86400

# ─────────────────────────── Benchmark Tickers (yfinance) ───────────────────────────
BENCHMARKS = {
    "Nifty 50": "^NSEI",
    "Nifty Next 50": "^NSMIDCP50.NS",
    "Nifty Midcap 150": "NIFTYMIDCAP150.NS",
    "Nifty Smallcap 250": "NIFTYSMLCAP250.NS",
    "Gold (GOLDBEES)": "GOLDBEES.NS",
    "Silver (SILVERBEES)": "SILVERBEES.NS",
}

# ─────────────────────────── Fund Categories & Top Funds ───────────────────────────
# scheme_code: name  (from mfapi.in)
# These are direct-growth plans of popular funds per category

FUND_CATEGORIES = {
    "Small Cap": {
        "funds": {
            "120828": "Quant Small Cap Fund - Direct Plan - Growth",
            "125497": "Nippon India Small Cap Fund - Direct Plan - Growth",
            "125307": "HDFC Small Cap Fund - Direct Plan - Growth",
            "119775": "SBI Small Cap Fund - Direct Plan - Growth",
            "130503": "Axis Small Cap Fund - Direct Plan - Growth",
            "147946": "Tata Small Cap Fund - Direct Plan - Growth",
            "125354": "Kotak Small Cap Fund - Direct Plan - Growth",
        },
        "relevant_benchmarks": ["Nifty Smallcap 250"],
    },
    "Mid Cap": {
        "funds": {
            "119504": "HDFC Mid-Cap Opportunities Fund - Direct Plan - Growth",
            "119246": "Kotak Emerging Equity Fund - Direct Plan - Growth",
            "120505": "Quant Mid Cap Fund - Direct Plan - Growth",
            "119237": "Axis Midcap Fund - Direct Plan - Growth",
            "125468": "Nippon India Growth Fund - Direct Plan - Growth",
            "118989": "DSP Midcap Fund - Direct Plan - Growth",
        },
        "relevant_benchmarks": ["Nifty Midcap 150"],
    },
    "Large Cap": {
        "funds": {
            "120503": "Quant Large Cap Fund - Direct Plan - Growth",
            "120716": "Mirae Asset Large Cap Fund - Direct Plan - Growth",
            "119062": "ICICI Prudential Bluechip Fund - Direct Plan - Growth",
            "119597": "SBI Bluechip Fund - Direct Plan - Growth",
            "119688": "Axis Bluechip Fund - Direct Plan - Growth",
            "125494": "Nippon India Large Cap Fund - Direct Plan - Growth",
        },
        "relevant_benchmarks": ["Nifty 50"],
    },
    "Flexi Cap": {
        "funds": {
            "120587": "Quant Flexi Cap Fund - Direct Plan - Growth",
            "122639": "Parag Parikh Flexi Cap Fund - Direct Plan - Growth",
            "119060": "HDFC Flexi Cap Fund - Direct Plan - Growth",
            "100471": "UTI Flexi Cap Fund - Direct Plan - Growth",
            "119064": "ICICI Prudential Equity & Debt Fund - Direct Plan - Growth",
        },
        "relevant_benchmarks": ["Nifty 50"],
    },
    "ELSS (Tax Saver)": {
        "funds": {
            "120847": "Quant ELSS Tax Saver Fund - Direct Plan - Growth",
            "119775": "SBI Long Term Equity Fund - Direct Plan - Growth",
            "120465": "Mirae Asset Tax Saver Fund - Direct Plan - Growth",
            "119773": "Axis Long Term Equity Fund - Direct Plan - Growth",
            "119245": "Kotak Tax Saver Fund - Direct Plan - Growth",
        },
        "relevant_benchmarks": ["Nifty 50"],
    },
    "Large & Mid Cap": {
        "funds": {
            "119062": "ICICI Prudential Large & Mid Cap Fund - Direct Plan - Growth",
            "125492": "Nippon India Vision Fund - Direct Plan - Growth",
            "120837": "Quant Large and Mid Cap Fund - Direct Plan - Growth",
            "119182": "Kotak Equity Opportunities Fund - Direct Plan - Growth",
            "119598": "SBI Large & Midcap Fund - Direct Plan - Growth",
        },
        "relevant_benchmarks": ["Nifty 50", "Nifty Midcap 150"],
    },
}

# ─────────────────────────── Comparison Table Metrics ───────────────────────────
METRICS_INFO = {
    "Total Invested": {"format": "₹{:,.0f}", "description": "Total amount invested via SIP + lumpsum"},
    "Current Value": {"format": "₹{:,.0f}", "description": "Current portfolio value"},
    "Profit/Loss": {"format": "₹{:,.0f}", "description": "Current Value - Total Invested"},
    "Absolute Return": {"format": "{:.2f}%", "description": "Total return as percentage"},
    "XIRR": {"format": "{:.2f}%", "description": "Annualized return accounting for irregular cashflows"},
    "Max Drawdown": {"format": "{:.2f}%", "description": "Largest peak-to-trough decline"},
}

# LLM Model Priority
GEMINI_MODEL_PRIMARY = "gemini-3-flash-preview"
GEMINI_MODEL_SECONDARY = "gemini-2.5-flash"  
LLM_TEMPERATURE = 0.7

# Rating categories for LLM recommendation
RATINGS = {
    "continue": {"emoji": "", "label": "Continue SIP", "color": "#1b5e20"},
    "pause": {"emoji": "", "label": "Pause & Hold", "color": "#e65100"},
    "switch": {"emoji": "", "label": "Consider Switching", "color": "#b71c1c"},
}
