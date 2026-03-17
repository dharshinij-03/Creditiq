"""
CreditIQ — Five-Cs Scoring Engine
Computes Character, Capacity, Capital, Collateral, Conditions
with full explainability (evidence trace for every score).
"""


def compute_scores(data: dict) -> dict:
    """
    Input: dict with all financial + qualitative fields
    Output: dict with scores, weighted total, decision, rationale
    """

    # ── Extract inputs ─────────────────────────────────
    rev      = float(data.get("revenue", 0))
    ebitda   = float(data.get("ebitda", 0))
    pat      = float(data.get("pat", 0))
    debt     = float(data.get("total_debt", 0))
    nw       = float(data.get("net_worth", 0))
    dscr     = float(data.get("dscr", 1.0))
    gst3b    = float(data.get("gst3b", rev))
    gst2a    = float(data.get("gst2a", rev))
    circular = int(data.get("circular", 0))
    loan_ask = float(data.get("loan_ask", 10))
    tenor    = int(data.get("tenor", 60))
    sector   = data.get("sector", "General")

    # Qualitative inputs (0–3 scale from credit officer)
    q_capacity = int(data.get("q_capacity", 1))   # factory utilisation
    q_mgmt     = int(data.get("q_mgmt", 1))        # management quality
    q_pledge   = int(data.get("q_pledge", 1))      # promoter pledge level
    q_legal    = int(data.get("q_legal", 1))        # legal / regulatory issues

    # ── Derived ratios ──────────────────────────────────
    de_ratio       = round(debt / nw, 2)   if nw   > 0 else 99.0
    ebitda_margin  = round(ebitda / rev * 100, 1) if rev > 0 else 0.0
    gst_variance   = round(abs(gst3b - gst2a) / gst3b * 100, 1) if gst3b > 0 else 0.0
    gst_gap_cr     = round(gst3b - gst2a, 2)

    evidence = []   # full explainability trace

    # ══════════════════════════════════════════════════════
    # C1 — CHARACTER (weight 25%)
    # Promoter history, legal issues, management quality,
    # shareholding pledge
    # ══════════════════════════════════════════════════════
    char_score = 50
    char_trace = []

    if q_legal == 2:
        char_score += 24; char_trace.append("+24 pts — No legal/ED/NCLT issues found")
    elif q_legal == 1:
        char_score += 10; char_trace.append("+10 pts — Minor/old legal cases only")
    else:
        char_score -= 15; char_trace.append("-15 pts — Active ED/NCLT proceedings on promoter")

    if q_mgmt == 2:
        char_score += 15; char_trace.append("+15 pts — Management very cooperative during due diligence")
    elif q_mgmt == 1:
        char_score +=  7; char_trace.append("+7 pts — Management cooperative")
    else:
        char_score -= 10; char_trace.append("-10 pts — Management evasive/uncooperative (RED FLAG)")

    if q_pledge == 2:
        char_score += 10; char_trace.append("+10 pts — Low promoter pledge (<30%)")
    elif q_pledge == 1:
        char_score +=  3; char_trace.append("+3 pts — Moderate promoter pledge (30–60%)")
    else:
        char_score -= 10; char_trace.append("-10 pts — High promoter pledge >60% (risk flag)")

    char_score = max(10, min(100, char_score))
    evidence.append({"criterion": "Character", "score": char_score,
                     "weight": 0.25, "trace": char_trace})

    # ══════════════════════════════════════════════════════
    # C2 — CAPACITY (weight 30%)
    # Ability to repay: DSCR, EBITDA margin, revenue trend
    # ══════════════════════════════════════════════════════
    cap_score = 40
    cap_trace = []

    # DSCR scoring
    if dscr >= 2.0:
        cap_score += 35; cap_trace.append(f"+35 pts — Excellent DSCR {dscr}x (≥2.0x)")
    elif dscr >= 1.5:
        cap_score += 25; cap_trace.append(f"+25 pts — Strong DSCR {dscr}x (≥1.5x)")
    elif dscr >= 1.25:
        cap_score += 15; cap_trace.append(f"+15 pts — Adequate DSCR {dscr}x (≥1.25x)")
    elif dscr >= 1.0:
        cap_score +=  5; cap_trace.append(f"+5 pts — Weak DSCR {dscr}x (≥1.0x, minimal cushion)")
    else:
        cap_score -=  5; cap_trace.append(f"-5 pts — Insufficient DSCR {dscr}x (<1.0x, cannot service debt)")

    # EBITDA margin
    if ebitda_margin >= 20:
        cap_score += 18; cap_trace.append(f"+18 pts — High EBITDA margin {ebitda_margin}% (≥20%)")
    elif ebitda_margin >= 15:
        cap_score += 12; cap_trace.append(f"+12 pts — Good EBITDA margin {ebitda_margin}%")
    elif ebitda_margin >= 10:
        cap_score +=  6; cap_trace.append(f"+6 pts — Moderate EBITDA margin {ebitda_margin}%")
    else:
        cap_score +=  1; cap_trace.append(f"+1 pt — Low EBITDA margin {ebitda_margin}% (<10%)")

    # Factory capacity (qualitative)
    cap_bonus = [0, 3, 6, 10][min(q_capacity, 3)]
    cap_score += cap_bonus
    labels = ["Very low (<40%)", "Low (40–60%)", "Moderate (60–90%)", "Full (90%+)"]
    cap_trace.append(f"+{cap_bonus} pts — Factory utilisation: {labels[min(q_capacity,3)]}")

    cap_score = max(10, min(100, cap_score))
    evidence.append({"criterion": "Capacity", "score": cap_score,
                     "weight": 0.30, "trace": cap_trace})

    # ══════════════════════════════════════════════════════
    # C3 — CAPITAL (weight 20%)
    # Financial strength: D/E ratio, net worth, PAT
    # ══════════════════════════════════════════════════════
    capital_score = 75
    capital_trace = []

    if de_ratio > 3.0:
        capital_score -= 35; capital_trace.append(f"-35 pts — Very high D/E {de_ratio}x (>3.0x)")
    elif de_ratio > 2.0:
        capital_score -= 20; capital_trace.append(f"-20 pts — High D/E {de_ratio}x (>2.0x)")
    elif de_ratio > 1.5:
        capital_score -= 10; capital_trace.append(f"-10 pts — Moderate D/E {de_ratio}x (>1.5x)")
    else:
        capital_score +=  5; capital_trace.append(f"+5 pts — Low D/E {de_ratio}x (≤1.5x, conservative leverage)")

    if nw >= 20:
        capital_score +=  8; capital_trace.append(f"+8 pts — Strong net worth ₹{nw} Cr")
    elif nw >= 10:
        capital_score +=  3; capital_trace.append(f"+3 pts — Adequate net worth ₹{nw} Cr")
    elif nw < 5:
        capital_score -= 12; capital_trace.append(f"-12 pts — Low net worth ₹{nw} Cr (<₹5 Cr)")

    if pat > 0:
        capital_trace.append(f"PAT ₹{pat} Cr — positive earnings support capital base")
    else:
        capital_score -= 10; capital_trace.append("-10 pts — Negative PAT signals financial stress")

    capital_score = max(10, min(100, capital_score))
    evidence.append({"criterion": "Capital", "score": capital_score,
                     "weight": 0.20, "trace": capital_trace})

    # ══════════════════════════════════════════════════════
    # C4 — COLLATERAL (weight 15%)
    # Security quality: asset cover proxy via D/E & NW
    # ══════════════════════════════════════════════════════
    coll_score = 70
    coll_trace = []

    if de_ratio < 0.8:
        coll_score = 92; coll_trace.append(f"+22 pts — Very low debt vs assets, strong security coverage")
    elif de_ratio < 1.2:
        coll_score = 82; coll_trace.append(f"+12 pts — Good asset coverage ratio")
    elif de_ratio < 1.8:
        coll_score = 70; coll_trace.append("Adequate asset coverage for requested security")
    elif de_ratio < 2.5:
        coll_score = 55; coll_trace.append(f"-15 pts — High leverage reduces effective collateral quality")
    else:
        coll_score = 38; coll_trace.append(f"-32 pts — Very high D/E {de_ratio}x — collateral coverage weak")

    if q_pledge == 0:
        coll_score -= 12; coll_trace.append("-12 pts — >60% promoter shares pledged reduces collateral value")

    coll_score = max(10, min(100, coll_score))
    evidence.append({"criterion": "Collateral", "score": coll_score,
                     "weight": 0.15, "trace": coll_trace})

    # ══════════════════════════════════════════════════════
    # C5 — CONDITIONS (weight 10%)
    # External: GST health, sector risk, macro
    # ══════════════════════════════════════════════════════
    cond_score = 70
    cond_trace = []

    # GST validation
    if gst_variance > 15:
        cond_score -= 28
        cond_trace.append(f"-28 pts — HIGH GST mismatch {gst_variance}% (₹{gst_gap_cr} Cr) signals revenue inflation risk")
    elif gst_variance > 8:
        cond_score -= 14
        cond_trace.append(f"-14 pts — MEDIUM GST variance {gst_variance}% requires explanation")
    elif gst_variance > 0:
        cond_trace.append(f"Minor GST variance {gst_variance}% — within acceptable range")
    else:
        cond_trace.append("GST returns consistent — no mismatch detected")

    # Circular transactions
    if circular == 1:
        cond_score -= 10; cond_trace.append("-10 pts — Circular transactions 1–2 instances detected")
    elif circular >= 2:
        cond_score -= 22; cond_trace.append("-22 pts — Multiple circular transactions — revenue inflation suspected")

    # Sector risk adjustment
    sector_adj = {
        "Real Estate":     -15,
        "NBFC":            -10,
        "Infrastructure":   -5,
        "Pharma Mfg":       +5,
        "Agriculture":      +3,
        "IT Services":      +5,
    }
    adj = sector_adj.get(sector, 0)
    cond_score += adj
    if adj != 0:
        sign = "+" if adj > 0 else ""
        cond_trace.append(f"{sign}{adj} pts — Sector adjustment: {sector}")

    cond_score = max(10, min(100, cond_score))
    evidence.append({"criterion": "Conditions", "score": cond_score,
                     "weight": 0.10, "trace": cond_trace})

    # ══════════════════════════════════════════════════════
    # Weighted composite score
    # ══════════════════════════════════════════════════════
    weighted = (
        char_score    * 0.25 +
        cap_score     * 0.30 +
        capital_score * 0.20 +
        coll_score    * 0.15 +
        cond_score    * 0.10
    )
    w_score = round(weighted, 1)

    # ── Risk band & decision ────────────────────────────
    if w_score >= 75:
        risk = "LOW"; decision = "APPROVE"; rate_add = 0.75; limit_mult = 0.95
    elif w_score >= 60:
        risk = "MEDIUM"; decision = "APPROVE WITH CONDITIONS"; rate_add = 1.75; limit_mult = 0.85
    elif w_score >= 48:
        risk = "HIGH"; decision = "REVIEW REQUIRED"; rate_add = 2.75; limit_mult = 0.70
    else:
        risk = "VERY HIGH"; decision = "REJECT"; rate_add = 0; limit_mult = 0.0

    rec_limit = round(loan_ask * limit_mult, 1)

    # ── Natural-language rationale ───────────────────────
    positives, negatives = [], []
    if dscr >= 1.5:      positives.append(f"Strong DSCR {dscr}x")
    if ebitda_margin >= 15: positives.append(f"Good EBITDA margin {ebitda_margin}%")
    if nw >= 12:         positives.append(f"Solid net worth ₹{nw} Cr")
    if q_legal == 2:     positives.append("No litigation/regulatory issues found")
    if gst_variance < 5: positives.append("Clean GST filing record")
    if de_ratio < 1.5:   positives.append(f"Conservative leverage D/E {de_ratio}x")

    if q_legal == 0:     negatives.append("Active ED/NCLT legal proceedings")
    if gst_variance > 10: negatives.append(f"GST mismatch ₹{gst_gap_cr} Cr ({gst_variance}%)")
    if de_ratio > 2.5:   negatives.append(f"High leverage D/E {de_ratio}x")
    if dscr < 1.25:      negatives.append(f"Weak DSCR {dscr}x")
    if circular >= 2:    negatives.append("Multiple circular bank transactions")
    if q_mgmt == 0:      negatives.append("Management uncooperative during due diligence")

    rationale = ""
    if positives:
        rationale += f"Supporting: {'; '.join(positives)}. "
    if negatives:
        rationale += f"Risk factors: {'; '.join(negatives)}. "
    if rec_limit > 0:
        pct = round(rec_limit / loan_ask * 100)
        rationale += f"Recommended limit ₹{rec_limit} Cr ({pct}% of ask) at MCLR + {rate_add}%."
    else:
        rationale += "Does not meet minimum criteria for sanction."

    return {
        "scores": {
            "character":  char_score,
            "capacity":   cap_score,
            "capital":    capital_score,
            "collateral": coll_score,
            "conditions": cond_score,
        },
        "weighted_score":   w_score,
        "risk_band":        risk,
        "decision":         decision,
        "recommended_limit": rec_limit,
        "interest_rate":    f"MCLR + {rate_add}%",
        "tenor_months":     tenor,
        "rationale":        rationale,
        "evidence":         evidence,
        "derived": {
            "de_ratio":       de_ratio,
            "ebitda_margin":  ebitda_margin,
            "gst_variance":   gst_variance,
            "gst_gap_cr":     gst_gap_cr,
        }
    }
