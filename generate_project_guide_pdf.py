#!/usr/bin/env python3
"""Generate PROJECT_GUIDE.pdf (English). Run: python generate_project_guide_pdf.py"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "PROJECT_GUIDE.pdf"
OUT_NAMED = ROOT / "Equity Research PROJECT_GUIDE.pdf"
BODY_FONT = "Helvetica"
BODY_FONT_BOLD = "Helvetica-Bold"
NAVY = colors.HexColor("#1a365d")
ACCENT = colors.HexColor("#2b6cb0")
LIGHT = colors.HexColor("#f7fafc")


def _default_content() -> dict:
    return {
        "title": "Automated Equity Research — Project Guide",
        "subtitle": (
            "Repo: github.com/darrenye1/public-reports- &nbsp;|&nbsp; "
            "Site: public-reports-one.vercel.app &nbsp;|&nbsp; "
            "Educational demo only; not investment advice."
        ),
        "sections": [
            {
                "heading": "1. Project Overview",
                "paragraphs": [
                    "This repository is an end-to-end equity research pipeline. It pulls US mega-cap "
                    "data from Yahoo Finance (yfinance), runs a five-pillar analysis (valuation, "
                    "financial-statement analysis, technicals, quantitative metrics, and a composite "
                    "signal), writes institutional-style 2-page PDF reports plus a Top 20 summary, "
                    "syncs a static dashboard, and deploys on Vercel.",
                    "There is no application server and no React build. Python generates PDFs and "
                    "JavaScript data files locally or on GitHub Actions; Vercel only hosts the "
                    "static folder public/.",
                ],
                "bullets": [
                    "Data source: Yahoo Finance via yfinance (delayed; no paid terminal)",
                    "Outputs: reports/{TICKER}_research.pdf, Top20_Summary.pdf / .csv",
                    "Website root: public/ (Vercel Output Directory = public)",
                    "Automation: GitHub Actions every Monday 14:00 UTC, plus manual Run workflow",
                    "State: reports/.data_state.json tracks last run and latest financial period",
                ],
            },
            {
                "heading": "2. Directory Layout",
                "code": (
                    "equity_research.py              Orchestration, valuation, PDF, batch CLI\n"
                    "market_analytics.py             SMA 42/252, RSI, momentum, Sharpe, SMA backtest\n"
                    "financial_statement_analysis.py FSA health score, margin trends, 1Y/3Y projections\n"
                    "signal_blend.py                 Composite rating + confluence\n"
                    "dashboard_data.py               Macro headlines + 6M index sparklines\n"
                    "sync_website.py                 Copy reports/ into public/ and docs/; write JS\n"
                    "reports/                        Generated PDFs/CSV and .data_state.json\n"
                    "public/                         Deploy root: index.html, *.js, reports/\n"
                    "docs/                           Mirror of public/ (GitHub Pages fallback)\n"
                    ".github/workflows/              weekly-update.yml scheduled refresh"
                ),
            },
            {
                "heading": "3. End-to-End Workflow",
                "paragraphs": [
                    "Trigger (local CLI or GitHub Actions) → rank MEGA_CAP_UNIVERSE by live market "
                    "cap → select Top 20 + extra PDF names → fetch Yahoo data → five-pillar analysis "
                    "→ write PDFs → write Top20_Summary.csv → sync_website.py → git push → Vercel "
                    "redeploy. Pushing code alone does not regenerate PDFs.",
                ],
                "subsections": [
                    {
                        "title": "3.1 Fully automatic (recommended)",
                        "bullets": [
                            "Monday 14:00 UTC: GitHub Actions cron fires",
                            "python equity_research.py --batch-top20 --refresh-stale --replace-old",
                            "python sync_website.py updates public/ and docs/",
                            "Actions bot commits and pushes main; Vercel redeploys in ~1–2 minutes",
                            "Prerequisite: Settings → Actions → workflow permissions = Read and write",
                        ],
                    },
                    {
                        "title": "3.2 Local full refresh",
                        "code": (
                            "python equity_research.py --batch-top20 --force --replace-old\n"
                            "python sync_website.py\n"
                            "GitHub Desktop: Commit + Push origin"
                        ),
                    },
                    {
                        "title": "3.3 Single ticker",
                        "code": (
                            "python equity_research.py NVDA\n"
                            "python equity_research.py SPCX --export-excel"
                        ),
                    },
                    {
                        "title": "3.4 Smart refresh (--refresh-stale)",
                        "paragraphs": [
                            "After fetch_company(), confirm_ticker_refresh() reads .data_state.json. "
                            "A ticker is regenerated if: (a) --force, (b) no prior run, (c) the latest "
                            "financial-statement period changed, or (d) last run is older than "
                            "STALE_MAX_AGE_DAYS (default 7). Otherwise the cached summary row is reused "
                            "and the PDF is left unchanged.",
                        ],
                    },
                ],
            },
            {
                "heading": "4. How Python Runs One Ticker",
                "paragraphs": [
                    "All analysis funnels through build_full_analysis() in equity_research.py. "
                    "process_ticker_report() then calls generate_pdf_report(). "
                    "process_ticker_summary_only() builds the same analysis without writing a PDF.",
                ],
                "code": (
                    "fetch_company(ticker)                 # yfinance → CompanyData\n"
                    "build_financial_summary()             # price, margins, FCF, analyst target\n"
                    "build_industry_research()             # sector text, trends, risks\n"
                    "build_competitor_analysis()           # industry peers + median multiples\n"
                    "build_valuation_summary()             # DCF + comps + analyst blend\n"
                    "build_technical_summary()             # SMA / RSI / golden-cross\n"
                    "build_quant_summary()                 # momentum, Sharpe, vs SPY\n"
                    "run_sma_backtest()                    # SMA strategy vs buy-and-hold\n"
                    "build_financial_statement_summary()   # FSA health score\n"
                    "blend_investment_signal()             # composite + confluence\n"
                    "generate_pdf_report()                 # 2-page Letter PDF"
                ),
                "subsections": [
                    {
                        "title": "4.1 Data fetch — fetch_company()",
                        "bullets": [
                            "yf.Ticker: .info, financials, balance_sheet, cashflow, 5Y history, recommendations",
                            "Up to 6 retries with backoff on rate limits / HTTP 429 / timeouts",
                            "Batch mode sleeps ~2s between tickers to reduce Yahoo throttling",
                            "Returns a CompanyData dataclass consumed by every later step",
                        ],
                    },
                    {
                        "title": "4.2 Universe and batch selection — run_batch()",
                        "bullets": [
                            "MEGA_CAP_UNIVERSE (~90 names) ranked by live US market cap",
                            "build_summary_ticker_list: Top 20 rows; SUMMARY_INCLUDE_TICKERS (SPCX) always included",
                            "build_pdf_ticker_list: Top 20 PDFs plus EXTRA_PDF_TICKERS (TSLA, BX) = 21 reports",
                            "Summary CSV/PDF sorted by market cap",
                        ],
                    },
                ],
            },
            {
                "heading": "5. Five-Pillar Methodology",
                "paragraphs": [
                    "The dashboard Composite rating is not the same as the Valuation rating. "
                    "Valuation produces the target price (45% of the composite). FSA, technicals, "
                    "and quant supply the remaining 55%. Confluence measures how many pillars "
                    "point the same way — it is not a statistical confidence interval.",
                ],
                "table": [
                    ["Pillar", "Module", "Composite weight", "What it measures"],
                    ["Valuation", "equity_research.py", "45%", "Blended target vs price (DCF / comps / analyst)"],
                    ["FSA", "financial_statement_analysis.py", "20%", "Statement quality: growth, margins, leverage, FCF"],
                    ["Technical", "market_analytics.py", "20%", "SMA 42/252 trend, RSI, golden/death cross"],
                    ["Quantitative", "market_analytics.py", "15%", "Momentum, Sharpe, drawdown, excess vs SPY"],
                ],
                "table_header": ["Pillar", "Module", "Weight", "What it measures"],
                "subsections": [
                    {
                        "title": "5.1 Valuation (45%) — target price engine",
                        "paragraphs": [
                            "build_valuation_summary() (1) picks an industry valuation profile, "
                            "(2) computes three implied prices, (3) drops unreliable methods, "
                            "(4) renormalizes profile weights, (5) audits extreme upside, "
                            "(6) maps upside % to BUY / OVERWEIGHT / HOLD / UNDERWEIGHT / SELL.",
                        ],
                    },
                    {
                        "title": "5.1.1 Industry profiles — resolve_valuation_profile()",
                        "paragraphs": [
                            "Yahoo industry/sector (and revenue growth) map to a profile that "
                            "decides whether DCF is used and which comps multiples are allowed. "
                            "High-growth semiconductors often exclude DCF because FCFE is distorted "
                            "by heavy capex — that is why a DCF print far below the market can "
                            "carry 0% weight while comps set the target.",
                        ],
                    },
                ],
            },
            {
                "heading": "",
                "table": [
                    ["Profile", "Typical names", "DCF", "Comps", "Default weights"],
                    ["default", "Operating companies", "FCFE", "P/E, EV/EBITDA, P/S", "DCF 32 / Comps 53 / Analyst 15"],
                    ["high_growth_tech", "Semis / software, high growth", "Off", "P/S, EV/EBITDA", "Comps 85 / Analyst 15"],
                    ["financial_bank", "Banks", "Off", "P/B", "Comps 75 / Analyst 25"],
                    ["financial_insurance", "Insurance / AM", "Off", "P/B", "Comps 70 / Analyst 30"],
                    ["financial_conglomerate", "BRK-B holdings", "Off", "Book ~1.0x", "Comps 55 / Analyst 45"],
                    ["payment_network", "V, MA", "FCFE", "P/E, EV/EBITDA", "DCF 40 / Comps 45 / Analyst 15"],
                ],
                "table_header": ["Profile", "Typical names", "DCF", "Comps", "Default weights"],
                "subsections": [
                    {
                        "title": "5.1.2 FCFE DCF — run_dcf()",
                        "paragraphs": [
                            "Equity-side DCF (not WACC/FCFF). Financials skip DCF entirely.",
                            "Cost of equity Ke from CAPM (Yahoo beta). Base FCFE is a robust average "
                            "of historical FCFE (OCF − capex ± net borrowing); if that series is "
                            "depressed versus standard FCF, the code falls back to standard FCF.",
                            "Five explicit years: FCFE_t = FCFE_{t-1} × (1+g), with g capped "
                            "(typically 12%, up to 20% for high growth). Mid-year discounting: "
                            "PV = FCFE_t / (1+Ke)^(t−0.5). Terminal value is Gordon: "
                            "TV = FCFE_5 × (1+g_term) / (Ke − g_term), then discounted. "
                            "Implied price = equity value / shares outstanding.",
                            "Hard screens: DCF dropped if implied price &lt; 35% of market, "
                            "&gt; 2.5× market, or more than ~55% below comps.",
                        ],
                    },
                    {
                        "title": "5.1.3 Comparables — run_comps()",
                        "paragraphs": [
                            "Peers: INDUSTRY_PEERS first (e.g. Semiconductors → AMD, INTC, QCOM, AVGO), "
                            "then keyword rules, then broad SECTOR_PEERS. Subject ticker is excluded.",
                            "Implied prices: peer-median P/E × EPS; EV/EBITDA × EBITDA − net debt; "
                            "P/S × revenue; P/B × book (banks/holdcos). Mega-caps may add a 52-week "
                            "range tri-mean as an uplift anchor. Each print is sanity-checked to "
                            "0.25×–3.0× current price, then blended into one comps fair value.",
                        ],
                    },
                    {
                        "title": "5.1.4 Analyst consensus",
                        "paragraphs": [
                            "Yahoo targetMeanPrice. Dropped or down-weighted if upside vs price "
                            "&gt; 50% or divergence vs comps &gt; 35% (stale consensus). "
                            "Analyst weight in the blend is capped near 20%.",
                        ],
                    },
                    {
                        "title": "5.1.5 Blend, audit, and valuation rating",
                        "paragraphs": [
                            "Active methods keep their profile weights, renormalized to 100%. "
                            "If |target/price − 1| ≥ 30%, _apply_valuation_audit() may switch to a "
                            "cross-method median, a 30% price cluster, or a ±40% sanity cap when "
                            "methods disagree. A single coherent anchor is not blindly capped.",
                            "Upside mapping (also requires confirming methods for BUY): "
                            "&gt;20% BUY (if ≥2 methods confirm), &gt;10% OVERWEIGHT, "
                            "about −5% to +5% HOLD, below −12% UNDERWEIGHT/SELL. "
                            "This is the dashboard 'Val …' subtext — not the Composite badge.",
                        ],
                    },
                    {
                        "title": "5.2 Financial statement analysis (20%)",
                        "paragraphs": [
                            "build_financial_statement_summary() scores statement quality on "
                            "[−1, +1]: 3Y revenue/NI CAGR, gross and operating-margin trend, "
                            "current ratio, debt/equity, ROE, FCF/net income. Simple projections: "
                            "revenue grows at a blend of historical CAGR and TTM growth (clipped "
                            "−5% to +25%); NI = revenue × operating margin × (1 − 21% tax).",
                            "Rating: score ≥ +0.25 Strong, ≤ −0.25 Weak, else Stable. "
                            "Strong is not a bullish price signal — a stock can be FSA Strong "
                            "and Quant −0.70 at the same time.",
                        ],
                    },
                    {
                        "title": "5.3 Technical analysis (20%)",
                        "paragraphs": [
                            "SMA 42 vs SMA 252 on daily closes. Golden/death cross scanned over "
                            "the last 20 sessions. RSI(14) flags overbought (&gt;70) / oversold (&lt;30). "
                            "Signal is BULLISH if a recent golden cross or short SMA sits &gt;1% above "
                            "long SMA; BEARISH on the inverse.",
                            "run_sma_backtest() compares an SMA crossover strategy with buy-and-hold "
                            "(0.10% cost per side). If the strategy loses, the technical score is "
                            "scaled by 0.65 in the composite so weak TA does not dominate.",
                        ],
                    },
                    {
                        "title": "5.4 Quantitative (15%)",
                        "paragraphs": [
                            "12-month and 3-month momentum, annualized volatility, Sharpe (Rf = 4%), "
                            "max drawdown, excess return vs SPY. These collapse into quant_score on "
                            "[−1, +1] and a POSITIVE / NEUTRAL / NEGATIVE label — the dashboard Quant column.",
                        ],
                    },
                    {
                        "title": "5.5 Composite rating and confluence — signal_blend.py",
                        "paragraphs": [
                            "Each pillar is mapped to [−1, +1]. Valuation score ≈ upside% / 25 "
                            "(so +25% upside → +1). Technical: golden cross +0.85, BULLISH +0.5, "
                            "BEARISH −0.5, death cross −0.85. FSA and quant use their native scores.",
                            "composite = 0.45×Val + 0.20×FSA + 0.20×TA + 0.15×Quant. "
                            "Mapped to BUY (≥0.55), OVERWEIGHT (≥0.25), HOLD, UNDERWEIGHT (≤−0.25), "
                            "SELL (≤−0.55).",
                            "Valuation anchor: large negative upside (≤ −15% / −25%) cannot stay "
                            "HOLD/BUY; large positive upside can lift HOLD to OVERWEIGHT/BUY.",
                            "Confluence: count pillars with score &gt; +0.15 (bullish) vs &lt; −0.15 "
                            "(bearish); confluence = max(bull, bear) / 4 × 100%. Example: three "
                            "bullish pillars → 75%; two vs two → 50% (typical HOLD).",
                        ],
                    },
                ],
            },
            {
                "heading": "6. PDF Report Layout",
                "paragraphs": [
                    "generate_pdf_report() uses ReportLab (Letter). Matplotlib draws the price/SMA "
                    "chart at 160 DPI so the embed is sharp. Current layout is two pages.",
                ],
                "subsections": [
                    {
                        "title": "Page 1 — company deep dive",
                        "bullets": [
                            "Header: name, sector, date, latest financial period",
                            "Rating card: composite rating, valuation rating, target, upside, last price",
                            "Investment Highlights (three bullets) and multi-pillar snapshot table",
                            "Investment thesis / executive summary",
                            "Key data grid (market cap, multiples, margins, FCF, ROE, yield)",
                            "Price trend chart with SMA 42 and SMA 252",
                        ],
                    },
                    {
                        "title": "Page 2 — financials, valuation, peers",
                        "bullets": [
                            "Financial &amp; valuation summary (2 historical years A + 3 forecast years E)",
                            "Technical and quantitative tables side by side",
                            "Valuation cross-check (DCF, blended comps, analyst, blended target) full width",
                            "DCF (FCFE) one-row summary: Ke, terminal g, FCFE growth, equity value, implied, vs current",
                            "Peer comparison plus a one-line industry context note",
                        ],
                    },
                ],
            },
            {
                "heading": "7. Website and Vercel Dashboard",
                "paragraphs": [
                    "The live site is a static single-page app. Python never runs on Vercel. "
                    "GitHub Actions (or a local machine) produces artifacts, commits them into "
                    "public/, and Vercel serves that folder on every push to main.",
                ],
                "subsections": [
                    {
                        "title": "7.1 sync_website.py",
                        "bullets": [
                            "Copy *_research.pdf, Top20_Summary.pdf and .csv into public/reports and docs/reports; delete stale PDFs",
                            "Top20_Summary.csv → public/summary-data.js (window.SUMMARY_ROWS + DATA_AS_OF)",
                            "dashboard_data.build_dashboard_payload() → dashboard-data.js",
                            "Copy index.html and social assets into docs/",
                            "Do not hand-edit the JS data files — change Python and re-run sync",
                        ],
                    },
                    {
                        "title": "7.2 dashboard_data.py",
                        "bullets": [
                            "News: Yahoo stories on SPY, indices, VIX, dollar, gold, sector ETFs",
                            "Impact score = macro keywords × 3 + premium source points + high-impact terms",
                            "One headline per US Eastern calendar day for the past 7 days",
                            "Index charts: ^GSPC, ^DJI, ^IXIC, ^RUT — 6M closes normalized to 100",
                        ],
                    },
                    {
                        "title": "7.3 public/index.html",
                        "bullets": [
                            "No npm / bundler. Loads summary-data.js and dashboard-data.js",
                            "Sortable Top 20 table: Composite, TA, FSA, Quant, Target/Upside, PDF link",
                            "KPI strip, methodology cards, 6M sparkline canvases, macro news list",
                            "Portfolio sections: #about #project #research #markets #top20 #resume",
                            "Vercel Web Analytics script (/_vercel/insights/script.js) — enable in the Vercel UI",
                        ],
                    },
                    {
                        "title": "7.4 Vercel setup",
                        "bullets": [
                            "Connect GitHub repo; Framework = Other / static",
                            "Output Directory = public (root of the repo, not a build folder)",
                            "Each push to main publishes HTML, JS, and PDFs on the CDN",
                            "Visitor stats: Vercel → Analytics → enable Web Analytics (see ANALYTICS.md)",
                        ],
                    },
                ],
            },
            {
                "heading": "8. GitHub Actions",
                "paragraphs": [
                    "File: .github/workflows/weekly-update.yml. Triggers: cron 0 14 * * 1 (Monday) "
                    "and workflow_dispatch. Job: checkout → Python 3.12 → pip install → "
                    "stale batch (or force-full if the dispatch checkbox is on) → sync_website.py → "
                    "git add reports/ public/ docs/ → commit → push. Vercel then redeploys.",
                ],
            },
            {
                "heading": "9. Git Workflow Tips",
                "bullets": [
                    "Commit source (.py, index.html, workflows). Prefer regenerating PDFs/JS via Actions or local batch + sync",
                    "PDFs are binary: never merge them in VS Code. Keep one side, then re-run the batch",
                    "On summary-data.js / dashboard-data.js conflicts: pick either side, then sync_website.py",
                    "After Actions pushes, Pull before local edits so branches do not diverge",
                    "resolve_merge.bat / resolve_merge.sh keep --ours on generated PDFs and JS during a merge",
                ],
            },
            {
                "heading": "10. Common Operations",
                "table": [
                    ["Change valuation or PDF layout", "Edit equity_research.py → force batch → sync → push"],
                    ["Change TA / quant / FSA / composite", "Edit the matching .py → force batch → sync → push"],
                    ["Add a forced Top 20 ticker", "SUMMARY_INCLUDE_TICKERS and MEGA_CAP_UNIVERSE"],
                    ["Add an extra PDF", "EXTRA_PDF_TICKERS"],
                    ["Change news / index widgets", "Edit dashboard_data.py → python sync_website.py"],
                    ["Change website UI", "Edit public/index.html → push (sync copies it to docs/)"],
                    ["Refresh the live site now", "GitHub → Actions → Weekly research update → Run workflow"],
                    ["Single-name PDF only", "python equity_research.py TICKER"],
                ],
                "table_header": ["Scenario", "Steps"],
            },
            {
                "heading": "11. Key Constants",
                "table": [
                    ["TOP_US_SUMMARY_COUNT", "20", "Summary table rows"],
                    ["EXTRA_PDF_TICKERS", "TSLA, BX", "Extra PDFs beyond Top 20"],
                    ["SUMMARY_INCLUDE_TICKERS", "SPCX", "Always in the Top 20 table"],
                    ["STALE_MAX_AGE_DAYS", "7", "Smart-refresh age threshold"],
                    ["VALUATION_AUDIT_THRESHOLD_PCT", "30", "Audit trigger |upside| %"],
                    ["TARGET_SANITY_CAP_PCT", "40", "Hard cap vs current when methods disagree"],
                    ["WEIGHT_FUNDAMENTAL / FSA / TA / Q", "45 / 20 / 20 / 15", "Composite blend"],
                    ["SMA_SHORT / SMA_LONG", "42 / 252", "Technical moving averages"],
                    ["ANALYST_MAX_BLEND_WEIGHT", "20%", "Cap on analyst in valuation blend"],
                ],
                "table_header": ["Constant", "Value", "Meaning"],
            },
            {
                "heading": "12. CLI Reference",
                "code": (
                    "python equity_research.py NVDA\n"
                    "python equity_research.py --batch-top20 --refresh-stale\n"
                    "python equity_research.py --batch-top20 --force --replace-old\n"
                    "python equity_research.py --batch-top20 --weekly\n"
                    "python sync_website.py\n"
                    "python generate_project_guide_pdf.py"
                ),
            },
            {
                "heading": "13. Dependencies and Disclaimer",
                "paragraphs": [
                    "Python packages: yfinance, pandas, numpy, reportlab, matplotlib, openpyxl "
                    "(see requirements.txt).",
                    "Regenerate this guide: python generate_project_guide_pdf.py "
                    "(writes PROJECT_GUIDE.pdf and Equity Research PROJECT_GUIDE.pdf).",
                    "Educational / research demo only. Not investment advice. Yahoo Finance data "
                    "can be delayed, incomplete, or restated; model outputs are mechanical and "
                    "can be wrong for individual names.",
                ],
            },
        ],
    }


def _style(name: str) -> ParagraphStyle:
    base = getSampleStyleSheet()["Normal"]
    font = BODY_FONT
    cfg = {
        "title": dict(fontName=BODY_FONT_BOLD, fontSize=16, leading=20,
                      textColor=NAVY, spaceAfter=8),
        "sub": dict(fontSize=8.5, leading=11, textColor=colors.grey, spaceAfter=12),
        "h1": dict(fontName=BODY_FONT_BOLD, fontSize=12, leading=16,
                   textColor=NAVY, spaceBefore=10, spaceAfter=5),
        "h2": dict(fontName=BODY_FONT_BOLD, fontSize=10, leading=13,
                   textColor=ACCENT, spaceBefore=6, spaceAfter=3),
        "body": dict(fontSize=8.5, leading=12, spaceAfter=4),
        "code": dict(fontName="Courier", fontSize=7.5, leading=10, leftIndent=8, spaceAfter=6,
                     backColor=LIGHT),
        "bullet": dict(fontSize=8.5, leading=12, leftIndent=14, bulletIndent=6, spaceAfter=2),
        "cell": dict(fontSize=7.5, leading=10),
        "th": dict(fontName=BODY_FONT_BOLD, fontSize=7.5, leading=10, textColor=colors.white),
    }
    kw = dict(cfg[name])
    font = kw.pop("fontName", font)
    return ParagraphStyle(name, parent=base, fontName=font, **kw)


def _p(text: str, kind: str = "body") -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), _style(kind))


def _add_table(story: list, rows: list, header: list | None = None) -> None:
    if header is None:
        header = list(rows[0])
        body = rows[1:]
    else:
        body = rows
        if body and list(body[0]) == list(header):
            body = body[1:]
    cell = _style("cell")
    th = _style("th")
    data = [[Paragraph(str(c), th) for c in header]]
    for row in body:
        data.append([Paragraph(str(c), cell) for c in row])
    ncol = len(header)
    usable = 16.5 * cm
    if ncol == 2:
        widths = [usable * 0.32, usable * 0.68]
    elif ncol == 3:
        widths = [usable * 0.38, usable * 0.22, usable * 0.40]
    elif ncol == 4:
        widths = [usable * 0.18, usable * 0.28, usable * 0.14, usable * 0.40]
    elif ncol == 5:
        widths = [usable * 0.20, usable * 0.22, usable * 0.10, usable * 0.22, usable * 0.26]
    else:
        widths = [usable / ncol] * ncol
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), BODY_FONT),
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))


def _add(story: list, sec: dict) -> None:
    if sec.get("heading"):
        story.append(_p(sec["heading"], "h1"))
    for p in sec.get("paragraphs", []):
        story.append(_p(p))
    for b in sec.get("bullets", []):
        story.append(Paragraph(b, _style("bullet"), bulletText="\u2022"))
    if sec.get("code"):
        story.append(_p(sec["code"], "code"))
    if sec.get("table"):
        _add_table(story, sec["table"], header=sec.get("table_header"))
    for sub in sec.get("subsections", []):
        if sub.get("title"):
            story.append(_p(sub["title"], "h2"))
        for p in sub.get("paragraphs", []):
            story.append(_p(p))
        for b in sub.get("bullets", []):
            story.append(Paragraph(b, _style("bullet"), bulletText="\u2022"))
        if sub.get("code"):
            story.append(_p(sub["code"], "code"))
        if sub.get("table"):
            _add_table(story, sub["table"], header=sub.get("table_header", ["Constant", "Value", "Meaning"]))


def build_pdf() -> list[str]:
    data = _default_content()
    written: list[str] = []
    for path in (OUT, OUT_NAMED):
        doc = SimpleDocTemplate(
            str(path), pagesize=A4,
            leftMargin=1.7 * cm, rightMargin=1.7 * cm,
            topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        )
        story: list = [_p(data["title"], "title"), _p(data["subtitle"], "sub")]
        for sec in data["sections"]:
            _add(story, sec)

        def footer(canvas, _doc):
            canvas.saveState()
            canvas.setFont(BODY_FONT, 8)
            canvas.setFillColor(colors.grey)
            canvas.drawString(1.7 * cm, 0.9 * cm, "Automated Equity Research  |  Project Guide  |  Educational demo")
            canvas.drawRightString(A4[0] - 1.7 * cm, 0.9 * cm, f"Page {canvas.getPageNumber()}")
            canvas.restoreState()

        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        written.append(str(path))
    return written


if __name__ == "__main__":
    paths = build_pdf()
    for p in paths:
        print("Wrote", Path(p).name)
