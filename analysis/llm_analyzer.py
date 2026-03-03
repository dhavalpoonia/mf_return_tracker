"""
LLM-powered analysis using Google Gemini (free tier).
Dual-agent approach: Analyst generates recommendation, Reviewer validates it.
"""

import streamlit as st
import json
from config import GEMINI_MODEL_PRIMARY, GEMINI_MODEL_SECONDARY, LLM_TEMPERATURE


def _get_gemini_client():
    """Get Gemini client using API key from session state (provided by user in UI)."""
    try:
        from google import genai

        # Always respect the user's provided key in session state
        api_key = st.session_state.get("gemini_api_key", "")
            
        if not api_key:
            return None

        client = genai.Client(api_key=api_key)
        return client
    except Exception:
        return None


def _build_analyst_prompt(
    fund_name: str,
    metrics_table: str,
    events_summary: str,
    fund_category: str,
) -> str:
    """Build the analysis prompt for the Analyst agent."""
    return f"""You are an expert mutual fund analyst for the Indian market. Analyze the following mutual fund performance data and provide a clear recommendation.

## Fund Under Analysis
**{fund_name}** (Category: {fund_category})

## Performance Comparison (SIP-based, same investment pattern applied to all)
{metrics_table}

## Significant Market Events Detected
{events_summary}

## Your Task
1. **Performance Assessment**: How is {fund_name} performing compared to its peers and benchmarks? Consider absolute returns, XIRR, and risk metrics.
2. **Category Comparison**: Is it among the top performers in its category, or lagging?
3. **Risk Analysis**: Look at max drawdown — is the fund taking too much risk for the returns it generates?
4. **Event Impact**: Did the fund recover well from market dips? How did it perform during rallies?
5. **Recommendation**: Provide ONE of these ratings:
   - **CONTINUE** — Fund is performing well, continue the SIP
   - **PAUSE** — Fund is average/below average, pause SIP and hold existing units
   - **SWITCH** — Fund is consistently underperforming, consider switching

## Output Format
Provide your analysis in the following JSON format:
```json
{{
    "rating": "CONTINUE" or "PAUSE" or "SWITCH",
    "confidence": "HIGH" or "MEDIUM" or "LOW",
    "summary": "2-3 sentence overall assessment",
    "key_observations": [
        "observation 1",
        "observation 2",
        "observation 3"
    ],
    "peer_comparison": "How the fund ranks among peers",
    "benchmark_comparison": "How the fund compares to benchmarks",
    "risk_assessment": "Assessment of risk-adjusted performance",
    "recommendation_reasoning": "Detailed reasoning for the recommendation"
}}
```

Be objective and data-driven. Do not make assumptions beyond the data provided. If the data is insufficient for a confident recommendation, say so."""


def _build_reviewer_prompt(analyst_output: str, metrics_table: str) -> str:
    """Build the review prompt for the Reviewer agent."""
    return f"""You are a senior financial advisor reviewing an analyst's mutual fund recommendation. Your job is to verify the analyst's claims against the actual data and ensure the recommendation is sound.

## Analyst's Report
{analyst_output}

## Actual Data for Verification
{metrics_table}

## Your Review Tasks
1. **Fact-Check**: Verify that the analyst's claims match the actual numbers in the data.
2. **Bias Check**: Ensure the recommendation is not overly bullish or bearish without justification.
3. **Missing Considerations**: Are there any important factors the analyst missed?
4. **Final Verdict**: Do you agree with the recommendation? If not, what would you change?

## Output Format
Provide your review in JSON format:
```json
{{
    "agrees_with_recommendation": true or false,
    "adjusted_rating": "CONTINUE" or "PAUSE" or "SWITCH" (if different from analyst),
    "review_notes": "Your detailed review",
    "corrections": ["any factual errors found"],
    "final_summary": "Your final 2-3 sentence recommendation for the investor"
}}
```

Be thorough but practical. This is for a retail investor who needs a clear, actionable answer."""


def _format_metrics_as_table(all_metrics: dict[str, dict]) -> str:
    """Format the metrics dict as a markdown table for LLM consumption."""
    if not all_metrics:
        return "No metrics data available."

    # Build header
    names = list(all_metrics.keys())
    header = "| Metric | " + " | ".join(names) + " |"
    separator = "|--------|" + "|".join(["--------" for _ in names]) + "|"

    # Build rows
    metric_keys = ["Total Invested", "Current Value", "Profit/Loss", "Absolute Return", "XIRR", "Max Drawdown"]
    rows = []
    for mk in metric_keys:
        row_values = []
        for name in names:
            val = all_metrics[name].get(mk, "N/A")
            if val is None:
                row_values.append("N/A")
            elif isinstance(val, float):
                if "Return" in mk or "XIRR" in mk or "Drawdown" in mk:
                    row_values.append(f"{val:.2f}%")
                else:
                    row_values.append(f"₹{val:,.0f}")
            else:
                row_values.append(str(val))
        rows.append(f"| {mk} | " + " | ".join(row_values) + " |")

    return "\n".join([header, separator] + rows)


def _format_events_summary(events: list[dict], explanations: dict) -> str:
    """Format events and their explanations for the LLM with chronological context."""
    if not events:
        return "No significant market events detected in the analysis period."

    lines = ["Chronological list of significant NAV fluctuations:"]
    for event in events:
        date_str = str(event["date"])
        direction = "DIP" if event["type"] == "dip" else "RISE"
        magnitude = event["magnitude"]

        explanation = ""
        if date_str in explanations:
            # Join multiple news titles if present
            news = explanations[date_str].get("news", [])
            if news:
                explanation = "Related News: " + " | ".join([n['title'] for n in news[:2]])
            else:
                explanation = explanations[date_str].get("summary", "")

        lines.append(f"- {date_str}: {direction} of {magnitude:.1f}% | {explanation}")

    return "\n".join(lines)


def analyze_fund(
    fund_name: str,
    fund_category: str,
    all_metrics: dict[str, dict],
    events: list[dict],
    event_explanations: dict,
) -> dict | None:
    """
    Run dual-agent LLM analysis on the fund comparison data.

    Returns:
        Dict with analyst_report, reviewer_report, and final_recommendation.
        Returns None if LLM is not configured.
    """
    client = _get_gemini_client()
    if not client:
        return None

    metrics_table = _format_metrics_as_table(all_metrics)
    events_summary = _format_events_summary(events, event_explanations)

    result = {"analyst_report": None, "reviewer_report": None, "final_recommendation": None}

    try:
        # === Agent 1: Analyst ===
        analyst_prompt = _build_analyst_prompt(fund_name, metrics_table, events_summary, fund_category)

        # Attempt with Primary Model
        try:
            analyst_response = client.models.generate_content(
                model=GEMINI_MODEL_PRIMARY,
                contents=analyst_prompt,
                config={
                    "temperature": LLM_TEMPERATURE,
                    "response_mime_type": "application/json",
                },
            )
        except Exception as primary_err:
            st.warning(f"Primary model ({GEMINI_MODEL_PRIMARY}) failed. Trying fallback...")
            analyst_response = client.models.generate_content(
                model=GEMINI_MODEL_SECONDARY,
                contents=analyst_prompt,
                config={
                    "temperature": LLM_TEMPERATURE,
                    "response_mime_type": "application/json",
                },
            )

        analyst_text = analyst_response.text.strip()
        try:
            analyst_report = json.loads(analyst_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', analyst_text, re.DOTALL)
            if json_match:
                analyst_report = json.loads(json_match.group(1))
            else:
                analyst_report = {"summary": analyst_text, "rating": "PAUSE", "confidence": "LOW"}

        result["analyst_report"] = analyst_report

        # === Agent 2: Reviewer ===
        reviewer_prompt = _build_reviewer_prompt(analyst_text, metrics_table)

        # Attempt with Primary Model (Re-use same logic for reviewer if needed, but usually if analyst worked, reviewer will too)
        try:
            reviewer_response = client.models.generate_content(
                model=GEMINI_MODEL_PRIMARY,
                contents=reviewer_prompt,
                config={
                    "temperature": LLM_TEMPERATURE,
                    "response_mime_type": "application/json",
                },
            )
        except Exception:
            reviewer_response = client.models.generate_content(
                model=GEMINI_MODEL_SECONDARY,
                contents=reviewer_prompt,
                config={
                    "temperature": LLM_TEMPERATURE,
                    "response_mime_type": "application/json",
                },
            )

        reviewer_text = reviewer_response.text.strip()
        try:
            reviewer_report = json.loads(reviewer_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', reviewer_text, re.DOTALL)
            if json_match:
                reviewer_report = json.loads(json_match.group(1))
            else:
                reviewer_report = {"final_summary": reviewer_text, "agrees_with_recommendation": True}

        result["reviewer_report"] = reviewer_report

        # === Build Final Recommendation ===
        if reviewer_report.get("agrees_with_recommendation", True):
            final_rating = analyst_report.get("rating", "PAUSE")
        else:
            final_rating = reviewer_report.get("adjusted_rating", analyst_report.get("rating", "PAUSE"))

        result["final_recommendation"] = {
            "rating": str(final_rating).upper(),
            "analyst_summary": analyst_report.get("summary", ""),
            "reviewer_summary": reviewer_report.get("final_summary", ""),
            "key_observations": analyst_report.get("key_observations", []),
            "confidence": analyst_report.get("confidence", "MEDIUM"),
            "recommendation_reasoning": analyst_report.get("recommendation_reasoning", ""),
            "peer_comparison": analyst_report.get("peer_comparison", ""),
            "benchmark_comparison": analyst_report.get("benchmark_comparison", ""),
            "risk_assessment": analyst_report.get("risk_assessment", ""),
            "reviewer_agrees": reviewer_report.get("agrees_with_recommendation", True),
            "reviewer_corrections": reviewer_report.get("corrections", []),
        }

        return result

    except Exception as e:
        st.error(f"Analysis Engine Error: {str(e)}")
        if "404" in str(e):
            st.warning("The configured Gemini model ID might be invalid or unsupported in your region.")
        return None
