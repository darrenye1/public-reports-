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
BODY_FONT = "Helvetica"
BODY_FONT_BOLD = "Helvetica-Bold"


def _default_content() -> dict:
    return {
        "title": "Automated Equity Research - Project Guide",
        "subtitle": (
            "Repo: github.com/darrenye1/public-reports- | "
            "Site: public-reports-one.vercel.app | "
            "Educational demo only; not investment advice."
        ),
        "sections": [
            {
                "heading": "1. Project Overview",
                "paragraphs": [
                    "Single-repo pipeline: pull US equity data from Yahoo Finance (yfinance), "
                    "run financial/industry/peer analysis, blend Simon FCFE DCF + comparable "
                    "multiples + analyst targets, publish 2-page PDF reports and a Top 20 summary "
                    "table, sync a static dashboard, and deploy via Vercel."
                ],
                "bullets": [
                    "Data: yfinance (Yahoo Finance)",
                    "Outputs: reports/{TICKER}_research.pdf, Top20_Summary.pdf / .csv",
                    "Website root: public/ (Vercel Output Directory = public)",
                    "Automation: GitHub Actions every Monday + optional manual Run workflow",
                ],
            },
            {
                "heading": "2. Directory Layout",
                "code": (
                    "equity_research.py       Core: data, valuation, PDF, batch CLI (~3700 lines)\n"
                    "dashboard_data.py        Dashboard macro news + index sparklines\n"
                    "sync_website.py          Copy reports/ to public/ + docs/; build JS files\n"
                    "reports/                 Generated PDFs/CSV; .data_state.json (gitignored)\n"
                    "public/                  Deploy root: index.html, *.js, reports/\n"
                    "docs/                    Mirror of public/ for GitHub Pages\n"
                    ".github/workflows/       weekly-update.yml - scheduled refresh"
                ),
            },
            {
                "heading": "3. End-to-End Workflow",
                "subsections": [
                    {
                        "title": "3.1 Fully automatic (recommended)",
                        "bullets": [
                            "Monday 14:00 UTC: GitHub Actions cron triggers",
                            "python equity_research.py --batch-top20 --refresh-stale --replace-old",
                            "python sync_website.py updates public/ and docs/",
                            "Actions bot commits and pushes main; Vercel redeploys in ~1-2 min",
                            "Prerequisite: Actions workflow permissions = Read and write",
                        ],
                    },
                    {
                        "title": "3.2 Local manual",
                        "code": (
                            "python equity_research.py --batch-top20 --force --replace-old\n"
                            "sync_website.bat\n"
                            "GitHub Desktop: Commit + Push origin"
                        ),
                    },
                    {
                        "title": "3.3 Single ticker",
                        "code": (
                            "python equity_research.py AAPL\n"
                            "python equity_research.py SPCX --export-excel"
                        ),
                    },
                ],
            },
            {
                "heading": "4. equity_research.py - Core Logic",
                "subsections": [
                    {
                        "title": "4.1 Single-ticker pipeline",
                        "code": (
                            "fetch_company(ticker)\n"
                            "  -> build_financial_summary()\n"
                            "  -> build_industry_research()\n"
                            "  -> build_competitor_analysis()\n"
                            "  -> build_valuation_summary()\n"
                            "  -> generate_pdf_report()"
                        ),
                    },
                    {
                        "title": "4.2 Data fetch - fetch_company()",
                        "bullets": [
                            "Uses yfinance.Ticker: .info, financials, balance_sheet, cashflow, history, recommendations",
                            "Retries with backoff (YFINANCE_FETCH_RETRIES) for rate limits",
                            "Returns CompanyData dataclass",
                        ],
                    },
                    {
                        "title": "4.3 Valuation - three methods",
                        "paragraphs": [
                            "Simon FCFE DCF (run_dcf): discount projected FCFE at cost of equity Ke; "
                            "Gordon terminal value; mid-year convention; growth capped at 12%. "
                            "Skipped for banks/insurance.",
                            "Comps (run_comps): sector peers from SECTOR_PEERS; median multiples "
                            "(P/E, EV/EBITDA, P/S); implied price sanity 0.25x-3.0x current.",
                            "Analyst: Yahoo targetMeanPrice / recommendations.",
                            "Blend (build_valuation_summary): weights DCF 28% / Comps 44% / Analyst 28% "
                            "on active methods; outlier filter; audit if upside > 30%; target cap 40%.",
                            "Rating: BUY/OVERWEIGHT, HOLD, SELL/UNDERWEIGHT from upside bands.",
                        ],
                    },
                    {
                        "title": "4.4 Top 20 batch - run_batch()",
                        "bullets": [
                            "build_summary_ticker_list: rank MEGA_CAP_UNIVERSE; force SPCX (SUMMARY_INCLUDE_TICKERS)",
                            "build_pdf_ticker_list: top 20 PDFs + EXTRA_PDF_TICKERS (TSLA, BX) = 21 reports",
                            "--refresh-stale: skip if period unchanged and last run < 7 days (.data_state.json)",
                            "--force: regenerate all tickers",
                            "Summary sorted by market_cap -> Top20_Summary.pdf + .csv",
                        ],
                    },
                    {
                        "title": "4.5 Key constants",
                        "table": [
                            ["TOP_US_SUMMARY_COUNT", "20", "Summary table rows"],
                            ["EXTRA_PDF_TICKERS", "TSLA, BX", "Extra PDFs"],
                            ["SUMMARY_INCLUDE_TICKERS", "SPCX", "Always in Top 20"],
                            ["STALE_MAX_AGE_DAYS", "7", "Stale refresh threshold"],
                            ["VALUATION_AUDIT_THRESHOLD_PCT", "30", "Audit trigger upside %"],
                            ["TARGET_SANITY_CAP_PCT", "40", "Max target vs current"],
                        ],
                    },
                    {
                        "title": "4.6 CLI reference",
                        "code": (
                            "python equity_research.py --batch-top20 --refresh-stale\n"
                            "python equity_research.py --batch-top20 --force\n"
                            "python equity_research.py --batch-top20 --weekly\n"
                            "python equity_research.py NVDA"
                        ),
                    },
                ],
            },
            {
                "heading": "5. dashboard_data.py",
                "bullets": [
                    "fetch_macro_news(7): one high-impact headline per US Eastern day (past week, newest first)",
                    "Impact score: macro keywords + premium sources + market-moving terms",
                    "fetch_index_charts: ^GSPC, ^DJI, ^IXIC, ^RUT - 6M normalized sparklines",
                    "Output: window.DASHBOARD_DATA in dashboard-data.js",
                ],
            },
            {
                "heading": "6. sync_website.py",
                "bullets": [
                    "Copy reports PDFs to public/reports and docs/reports; remove stale PDFs",
                    "Top20_Summary.csv -> summary-data.js (window.SUMMARY_ROWS)",
                    "build_dashboard_payload() -> dashboard-data.js",
                    "Do not hand-edit JS data files; change Python and re-run sync",
                ],
            },
            {
                "heading": "7. Frontend - public/index.html",
                "bullets": [
                    "Static single-page site; no build step",
                    "Loads summary-data.js + dashboard-data.js",
                    "renderTable: sortable/searchable Top 20; renderReportButtons: PDF grid",
                    "renderIndices + renderNews: market dashboard widgets",
                    "Sections: #about #project #research #top20 #resume",
                ],
            },
            {
                "heading": "8. GitHub Actions",
                "paragraphs": [
                    "File: .github/workflows/weekly-update.yml. Triggers: cron 0 14 * * 1 (Monday) "
                    "and workflow_dispatch. Steps: checkout, pip install, batch + sync, "
                    "git add reports/ public/ docs/, commit, push. Manual run supports Force full refresh."
                ],
            },
            {
                "heading": "9. Git workflow tips",
                "bullets": [
                    "Commit source code (.py, index.html, workflows); let Actions generate PDFs and JS",
                    "On JS merge conflicts: pick either side, then run sync_website.py",
                    "After Actions pushes, Pull before local edits to avoid divergence",
                ],
            },
            {
                "heading": "10. Common operations",
                "table": [
                    ["Change valuation", "Edit equity_research.py -> force batch -> sync -> push"],
                    ["Add Top 20 ticker", "SUMMARY_INCLUDE_TICKERS + MEGA_CAP_UNIVERSE"],
                    ["Change news logic", "Edit dashboard_data.py -> sync_website.py"],
                    ["Change website UI", "Edit public/index.html -> push"],
                    ["Update site now", "Actions -> Run workflow"],
                ],
            },
            {
                "heading": "11. Dependencies",
                "paragraphs": [
                    "yfinance, pandas, numpy, reportlab, matplotlib, openpyxl - see requirements.txt",
                    "Regenerate this guide: python generate_project_guide_pdf.py",
                ],
            },
        ],
    }


def _style(name: str) -> ParagraphStyle:
    base = getSampleStyleSheet()["Normal"]
    font = BODY_FONT
    cfg = {
        "title": dict(fontName=BODY_FONT_BOLD, fontSize=18, leading=24,
                      textColor=colors.HexColor("#1a365d"), spaceAfter=10),
        "sub": dict(fontSize=9, leading=12, textColor=colors.grey, spaceAfter=14),
        "h1": dict(fontName=BODY_FONT_BOLD, fontSize=14, leading=18,
                   textColor=colors.HexColor("#1a365d"), spaceBefore=12, spaceAfter=6),
        "h2": dict(fontName=BODY_FONT_BOLD, fontSize=11, leading=15,
                   textColor=colors.HexColor("#2b6cb0"), spaceBefore=8, spaceAfter=4),
        "body": dict(fontSize=9, leading=13, spaceAfter=5),
        "code": dict(fontName="Courier", fontSize=8, leading=10, leftIndent=10, spaceAfter=6,
                     backColor=colors.HexColor("#f7fafc")),
        "bullet": dict(fontSize=9, leading=13, leftIndent=14, bulletIndent=6, spaceAfter=3),
    }
    kw = dict(cfg[name])
    font = kw.pop("fontName", font)
    return ParagraphStyle(name, parent=base, fontName=font, **kw)


def _p(text: str, kind: str = "body") -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), _style(kind))


def _add_table(story: list, rows: list, header: list) -> None:
    data = [header] + rows
    ncol = len(header)
    width = 15.5 * cm / ncol
    t = Table(data, colWidths=[width] * ncol)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), BODY_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), BODY_FONT_BOLD),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b6cb0")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
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
            _add_table(story, sub["table"], header=["Constant", "Value", "Meaning"])
    if sec.get("table"):
        _add_table(story, sec["table"], header=["Scenario", "Steps"])


def build_pdf() -> str:
    data = _default_content()
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
    )
    story: list = [_p(data["title"], "title"), _p(data["subtitle"], "sub")]
    for sec in data["sections"]:
        _add(story, sec)

    def footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont(BODY_FONT, 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, 1.2 * cm, f"Project Guide  |  Page {canvas.getPageNumber()}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return str(OUT)


if __name__ == "__main__":
    build_pdf()
    print("Wrote PROJECT_GUIDE.pdf")
