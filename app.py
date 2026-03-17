"""
CreditIQ — AI Credit Appraisal Platform
Main Flask Application
Run: python app.py
Visit: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, send_file
import json, io
from scoring import compute_scores
from research import run_research_agent
from cam_generator import generate_cam_pdf

app = Flask(__name__)

# ── Routes ─────────────────────────────────────────────

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/new-case")
def new_case():
    return render_template("new_case.html")

@app.route("/api/gst-check", methods=["POST"])
def gst_check():
    """Validate GST returns — GSTR-3B vs GSTR-2A cross check"""
    data = request.json
    gst3b = float(data.get("gst3b", 0))
    gst2a = float(data.get("gst2a", 0))
    circular = int(data.get("circular", 0))

    flags = []
    if gst3b > 0:
        variance_amt = round(gst3b - gst2a, 2)
        variance_pct = round((variance_amt / gst3b) * 100, 1)
        if variance_pct > 15:
            level = "HIGH"
        elif variance_pct > 8:
            level = "MEDIUM"
        else:
            level = "LOW"
        flags.append({
            "issue": f"GSTR-3B vs 2A Variance",
            "amount": f"₹{abs(variance_amt)} Cr ({abs(variance_pct)}%)",
            "level": level
        })

    if circular == 1:
        flags.append({"issue": "Circular transactions detected", "amount": "1–2 instances", "level": "MEDIUM"})
    elif circular >= 2:
        flags.append({"issue": "Circular transactions detected", "amount": "3+ instances", "level": "HIGH"})

    return jsonify({"flags": flags, "variance_pct": variance_pct if gst3b > 0 else 0})

@app.route("/api/research", methods=["POST"])
def research():
    """Run automated secondary research agent"""
    data = request.json
    company = data.get("company_name", "")
    sector  = data.get("sector", "")
    results = run_research_agent(company, sector)
    return jsonify(results)

@app.route("/api/score", methods=["POST"])
def score():
    """Run Five-Cs ML scoring engine"""
    data = request.json
    result = compute_scores(data)
    return jsonify(result)

@app.route("/api/generate-cam", methods=["POST"])
def generate_cam():
    """Generate Credit Appraisal Memo as PDF"""
    data = request.json
    pdf_bytes = generate_cam_pdf(data)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"CAM_{data.get('company_name','report').replace(' ','_')}.pdf"
    )

if __name__ == "__main__":
    print("\n  CreditIQ starting on http://localhost:5000\n")
    app.run(debug=True, port=5000)
