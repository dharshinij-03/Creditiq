# CreditIQ — AI Credit Appraisal Platform

---

## SETUP 

### Step 1: Install Python dependencies
```bash
pip install flask reportlab
```

### Step 2: Run the app
```bash
cd creditiq
gunicorn app:app```

### Step 3: Open in browser
```
http://localhost:5000
```

---

## PROJECT STRUCTURE

```
creditiq/
├── app.py              ← Flask web server (main entry point)
├── scoring.py          ← Five-Cs ML scoring engine (Character, Capacity, Capital, Collateral, Conditions)
├── research.py         ← Research agent (MCA21, eCourts, RBI, news checks)
├── cam_generator.py    ← PDF Credit Appraisal Memo generator (ReportLab)
├── requirements.txt    ← pip dependencies
├── templates/
│   ├── dashboard.html  ← Home screen with active applications
│   └── new_case.html   ← 5-step appraisal workflow
└── README.md
```

---

## WHAT IT DOES

### Dashboard (/)
- View all active loan applications with risk scores
- Click any company to auto-load their data

### New Case (/new-case)
5-step workflow:
1. **Company Details** — enter financial data (revenue, EBITDA, DSCR, debt etc.)
2. **GST Validation** — GSTR-3B vs GSTR-2A cross-check, circular transaction detection
3. **Field Notes** — credit officer site visit observations (adjusts ML score)
4. **AI Analysis** — runs Five-Cs scoring + research agent simultaneously
5. **Results + CAM** — shows scores, risk flags, decision, and downloads PDF CAM

### API Endpoints
| Endpoint | Method | Description |
|---|---|---|
| `/api/gst-check` | POST | Validate GST returns |
| `/api/research` | POST | Run research agent |
| `/api/score` | POST | Compute Five-Cs scores |
| `/api/generate-cam` | POST | Download CAM as PDF |

---

## FIVE-CS SCORING MODEL

| Criterion | Weight | Data Sources |
|---|---|---|
| Character | 25% | Promoter legal history, management quality, share pledge |
| Capacity | 30% | DSCR, EBITDA margin, factory utilisation |
| Capital | 20% | Debt/Equity ratio, net worth, PAT trend |
| Collateral | 15% | Asset cover proxy, LTV ratio |
| Conditions | 10% | GST variance, sector risk, macro |

**Risk Bands:**
- 75–100 → LOW risk → APPROVE (MCLR + 0.75%)
- 60–74  → MEDIUM risk → APPROVE WITH CONDITIONS (MCLR + 1.75%)
- 48–59  → HIGH risk → REVIEW REQUIRED (MCLR + 2.75%)
- Below 48 → VERY HIGH → REJECT

---

## INDIA-SPECIFIC FEATURES
- GSTR-2A vs GSTR-3B reconciliation with variance threshold
- Circular bank transaction detection
- MCA21 director DIN linked company risk check
- eCourts / NCLT litigation lookup
- RBI wilful defaulter check
- Sector-specific risk adjustments (NBFC, Real Estate, Pharma, Agriculture)
- Lakh/Crore number format throughout
- DSCR covenant monitoring in CAM conditions

---

## TO EXTEND IN PRODUCTION
- `research.py` → Replace simulated lookups with real MCA21 / eCourts APIs
- `scoring.py` → Train XGBoost model on historical Indian credit data
- Add database (PostgreSQL) for case persistence
- Add user authentication (bank login)
- Connect to Databricks for bulk PDF parsing pipeline
