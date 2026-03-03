"""
News search agent using DuckDuckGo (free, no API key).
Searches for explanations of significant market events.
"""

import streamlit as st
from datetime import date, timedelta


@st.cache_data(ttl=86400, show_spinner=False)
def search_event_news(event_date: date, event_type: str, fund_name: str = "") -> list[dict]:
    """
    Search for news articles explaining a market event around a given date.

    Args:
        event_date: Date of the event
        event_type: 'dip' or 'rise'
        fund_name: Optional fund name for more specific search

    Returns:
        List of {title, url, snippet}
    """
    try:
        from duckduckgo_search import DDGS

        # Build search query
        date_str = event_date.strftime("%B %Y")  # e.g., "March 2024"
        event_word = "crash" if event_type == "dip" else "rally"

        queries = [
            f"Indian stock market {event_word} {date_str}",
            f"Nifty {event_word} reason {date_str}",
        ]

        if fund_name:
            queries.insert(0, f"{fund_name} {event_word} {date_str}")

        results = []
        seen_titles = set()

        with DDGS() as ddgs:
            for query in queries:
                try:
                    search_results = list(ddgs.text(query, max_results=3))
                    for r in search_results:
                        title = r.get("title", "")
                        if title not in seen_titles:
                            seen_titles.add(title)
                            results.append({
                                "title": title,
                                "url": r.get("href", ""),
                                "snippet": r.get("body", ""),
                            })
                except Exception:
                    continue

                if len(results) >= 5:
                    break

        return results[:5]

    except ImportError:
        return [{"title": "DuckDuckGo search not available", "url": "", "snippet": "Install duckduckgo-search package"}]
    except Exception as e:
        return [{"title": f"Search error: {str(e)}", "url": "", "snippet": ""}]


@st.cache_data(ttl=86400, show_spinner=False)
def get_event_explanations(events: list[dict], fund_name: str = "") -> dict:
    """
    For a list of detected events, search for news and return explanations.

    Args:
        events: List of event dicts from event_detector
        fund_name: Fund name for context

    Returns:
        Dict mapping event date string → {news: [...], summary: str}
    """
    # Convert events list to a tuple of tuples for caching
    explanations = {}

    for event in events[:5]:  # Limit to 5 events to avoid rate limiting
        event_date = event["date"]
        event_type = event["type"]

        news = search_event_news(event_date, event_type, fund_name)

        # Build a brief summary from snippets
        snippets = [n["snippet"] for n in news if n["snippet"]]
        summary = " | ".join(snippets[:3]) if snippets else "No specific news found for this event."

        explanations[str(event_date)] = {
            "news": news,
            "summary": summary,
            "event": event,
        }

    return explanations
