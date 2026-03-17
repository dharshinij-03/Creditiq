"""
CreditIQ — Research Agent
Simulates MCA21, eCourts, RBI defaulter, and news checks.
In production: replace each section with real API calls.
"""

import random
import time


# ── Simulated databases (replace with real API calls in production) ──

_MCA_RISK_COMPANIES = {
    "krishna": {"struck_off": 2, "charges": 3, "director_flags": True},
    "pqr":     {"struck_off": 1, "charges": 1, "director_flags": True},
}

_RBI_DEFAULTERS = ["krishna", "pqr microfinance"]

_NEWS_FLAGS = {
    "krishna":   ["ED probe on promoter (Economic Times, Jan 2026)",
                  "RERA violation notice issued (Hindu BusinessLine, Nov 2025)"],
    "pqr":       ["RBI notice for NBFC compliance breach (Mint, Feb 2026)"],
}

_COURT_CASES = {
    "krishna":   [{"court":"NCLT Mumbai","case":"IBC Petition CP-112/2025","status":"Active"}],
    "pqr":       [{"court":"DRT Mumbai","case":"DRT-445/2024","status":"Pending"}],
}


def run_research_agent(company_name: str, sector: str) -> dict:
    """
    Run automated secondary research on a company.

    In production this would call:
    - MCA21 API  → director DIN lookup, charge filings
    - eCourts API → litigation search
    - RBI portal → wilful defaulter check
    - SerpAPI / Google News → news search
    """
    key = company_name.lower().split()[0]   # simple key lookup

    findings = []
    risk_score_impact = 0

    # ── 1. MCA21 Director DIN Check ──────────────────────
    mca = _MCA_RISK_COMPANIES.get(key, {})
    if mca.get("struck_off", 0) > 0:
        findings.append({
            "source":  "MCA21 Portal",
            "finding": f"Director DIN linked to {mca['struck_off']} struck-off company/companies",
            "level":   "MEDIUM",
            "api_stub": "GET https://www.mca.gov.in/MCA21/din_details/{din}"
        })
        risk_score_impact -= 8
    else:
        findings.append({
            "source":  "MCA21 Portal",
            "finding": "Director DINs checked — no struck-off or NPA-flagged associations found",
            "level":   "LOW",
            "api_stub": "GET https://www.mca.gov.in/MCA21/din_details/{din}"
        })

    if mca.get("charges", 0) > 2:
        findings.append({
            "source":  "MCA21 Charge Registry",
            "finding": f"{mca['charges']} charge filings found — verify satisfaction status",
            "level":   "MEDIUM",
            "api_stub": "GET https://www.mca.gov.in/MCA21/charges/{cin}"
        })
        risk_score_impact -= 5

    # ── 2. eCourts / NCLT Check ──────────────────────────
    cases = _COURT_CASES.get(key, [])
    if cases:
        for c in cases:
            findings.append({
                "source":   f"eCourts — {c['court']}",
                "finding":  f"Active case: {c['case']} ({c['status']})",
                "level":    "HIGH",
                "api_stub": f"GET https://services.ecourts.gov.in/ecourtindia/cases/?company={company_name}"
            })
            risk_score_impact -= 15
    else:
        findings.append({
            "source":  "eCourts / NCLT",
            "finding": "No active litigation or insolvency proceedings found",
            "level":   "LOW",
            "api_stub": f"GET https://services.ecourts.gov.in/ecourtindia/cases/?company={company_name}"
        })

    # ── 3. RBI Wilful Defaulter Check ────────────────────
    is_defaulter = any(d in company_name.lower() for d in _RBI_DEFAULTERS)
    if is_defaulter:
        findings.append({
            "source":  "RBI Wilful Defaulter List",
            "finding": "Company or promoter appears in RBI defaulter list — REJECT immediately",
            "level":   "CRITICAL",
            "api_stub": "GET https://www.rbi.org.in/scripts/Wilfuldefaulters.aspx"
        })
        risk_score_impact -= 30
    else:
        findings.append({
            "source":  "RBI Wilful Defaulter List",
            "finding": "Not found in RBI wilful defaulter or CRILC SMA list",
            "level":   "LOW",
            "api_stub": "GET https://www.rbi.org.in/scripts/Wilfuldefaulters.aspx"
        })

    # ── 4. News Intelligence ──────────────────────────────
    news_items = _NEWS_FLAGS.get(key, [])
    if news_items:
        for item in news_items:
            findings.append({
                "source":  "News Intelligence",
                "finding": item,
                "level":   "HIGH",
                "api_stub": f"SerpAPI: '{company_name} fraud ED SFIO RBI 2025 2026'"
            })
            risk_score_impact -= 10
    else:
        findings.append({
            "source":  "News Intelligence",
            "finding": "No adverse news found for company or promoters in last 24 months",
            "level":   "LOW",
            "api_stub": f"SerpAPI: '{company_name} fraud ED SFIO RBI 2025 2026'"
        })

    # ── 5. Sector Watch ───────────────────────────────────
    sector_alerts = {
        "NBFC":         "RBI tightening NBFC regulations (Jan 2026) — higher provisioning requirements",
        "Real Estate":  "RERA enforcement active in Maharashtra/Karnataka — project delays risk",
        "Agriculture":  "Good monsoon forecast — positive sector outlook for FY2026",
        "Pharma Mfg":   "PLI scheme active — sector getting government support",
    }
    alert = sector_alerts.get(sector, f"No specific sector alerts for {sector}")
    level = "MEDIUM" if sector in ["NBFC", "Real Estate"] else "LOW"
    findings.append({
        "source":  "Sector Intelligence",
        "finding": alert,
        "level":   level,
        "api_stub": f"SerpAPI: '{sector} India RBI regulations NPA 2026'"
    })

    high_count   = sum(1 for f in findings if f["level"] in ("HIGH", "CRITICAL"))
    medium_count = sum(1 for f in findings if f["level"] == "MEDIUM")

    return {
        "company":        company_name,
        "sector":         sector,
        "findings":       findings,
        "high_flags":     high_count,
        "medium_flags":   medium_count,
        "risk_adjustment": risk_score_impact,
        "summary": (
            f"Research complete. Found {high_count} HIGH-risk and "
            f"{medium_count} MEDIUM-risk signals across "
            f"{len(findings)} sources."
        )
    }
