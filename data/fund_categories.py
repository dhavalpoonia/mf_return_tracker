"""
Fund category detection and peer fund suggestion.
Maps funds to categories and suggests comparison peers.
"""

import streamlit as st
from config import FUND_CATEGORIES


def detect_category(scheme_name: str) -> str | None:
    """
    Detect fund category from scheme name using keyword matching.
    Returns category name or None if not detected.
    """
    name_upper = scheme_name.upper()

    # Order matters — check more specific categories first
    category_keywords = {
        "Small Cap": ["SMALL CAP", "SMALLCAP", "SMALL-CAP"],
        "ELSS (Tax Saver)": ["ELSS", "TAX SAVER", "TAX SAVING", "LONG TERM EQUITY"],
        "Large & Mid Cap": ["LARGE & MID", "LARGE AND MID", "LARGE&MID"],
        "Mid Cap": ["MID CAP", "MIDCAP", "MID-CAP"],
        "Large Cap": ["LARGE CAP", "LARGECAP", "LARGE-CAP", "BLUECHIP", "BLUE CHIP"],
        "Flexi Cap": ["FLEXI CAP", "FLEXICAP", "FLEXI-CAP", "MULTI CAP", "MULTICAP"],
    }

    for category, keywords in category_keywords.items():
        for kw in keywords:
            if kw in name_upper:
                return category
    return None


def get_peer_funds(scheme_code: str, scheme_name: str) -> dict[str, str]:
    """
    Get peer funds for comparison based on the fund's category.
    Returns {scheme_code: scheme_name} excluding the input fund.
    """
    category = detect_category(scheme_name)
    if not category or category not in FUND_CATEGORIES:
        return {}

    peers = FUND_CATEGORIES[category]["funds"].copy()

    # Remove the input fund from peers
    if scheme_code in peers:
        del peers[scheme_code]

    return peers


def get_relevant_benchmarks(scheme_name: str) -> list[str]:
    """
    Get the most relevant benchmark names for comparison based on fund category.
    Always includes Nifty 50 and Gold as universal benchmarks.
    """
    category = detect_category(scheme_name)
    relevant = set()

    if category and category in FUND_CATEGORIES:
        for bm in FUND_CATEGORIES[category].get("relevant_benchmarks", []):
            relevant.add(bm)

    # Always include these for complete comparison
    relevant.add("Nifty 50")
    relevant.add("Gold (GOLDBEES)")

    return sorted(relevant)


def get_all_categories() -> list[str]:
    """Return list of all available fund categories."""
    return list(FUND_CATEGORIES.keys())


def get_funds_by_category(category: str) -> dict[str, str]:
    """Return {scheme_code: scheme_name} for a given category."""
    if category in FUND_CATEGORIES:
        return FUND_CATEGORIES[category]["funds"].copy()
    return {}
