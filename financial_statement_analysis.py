"""
Financial statement analysis & projection (MGTA 632 Topics 7–8).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class FinancialStatementSummary:
    health_score: float = 0.0
    health_rating: str = "Neutral"
    revenue_cagr_3y: float | None = None
    ni_cagr_3y: float | None = None
    gross_margin_trend: str = "Stable"
    operating_margin_trend: str = "Stable"
    current_ratio: float | None = None
    debt_to_equity: float | None = None
    roe: float | None = None
    fcf_to_ni: float | None = None
    projected_revenue_y1: float | None = None
    projected_revenue_y3: float | None = None
    projected_ni_y1: float | None = None
    projected_ni_y3: float | None = None
    projection_growth_assumption: float | None = None
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _safe_series_value(df: pd.DataFrame | None, row_label: str, col_index: int = 0) -> float | None:
    if df is None or df.empty:
        return None
    if row_label not in df.index:
        matches = [idx for idx in df.index if row_label.lower() in str(idx).lower()]
        if not matches:
            return None
        row_label = matches[0]
    try:
        val = df.loc[row_label].iloc[col_index]
        if pd.isna(val):
            return None
        return float(val)
    except (IndexError, KeyError, TypeError, ValueError):
        return None


def _fmt_large(value: float | None) -> str:
    if value is None:
        return "N/A"
    av = abs(value)
    if av >= 1e12:
        return f"${value / 1e12:.2f}T"
    if av >= 1e9:
        return f"${value / 1e9:.2f}B"
    if av >= 1e6:
        return f"${value / 1e6:.2f}M"
    return f"${value:,.0f}"


def _cagr(start: float, end: float, years: int) -> float | None:
    if start <= 0 or end <= 0 or years <= 0:
        return None
    return ((end / start) ** (1 / years) - 1) * 100


def _series_values(df: pd.DataFrame | None, label: str, n: int) -> list[float]:
    if df is None or df.empty:
        return []
    out: list[float] = []
    for i in range(min(n, df.shape[1])):
        v = _safe_series_value(df, label, i)
        if v is not None:
            out.append(v)
    return out


def _margin_trend(values: list[float]) -> str:
    if len(values) < 2:
        return "Stable"
    diff = values[0] - values[-1]
    if diff > 2:
        return "Improving"
    if diff < -2:
        return "Deteriorating"
    return "Stable"


def build_financial_statement_summary(
    financials: pd.DataFrame | None,
    balance_sheet: pd.DataFrame | None,
    revenue: float | None,
    revenue_growth: float | None,
    operating_margin: float | None,
    debt_to_equity: float | None,
    roe: float | None,
    free_cash_flow: float | None,
) -> FinancialStatementSummary:
    rev_hist = list(reversed(_series_values(financials, "Total Revenue", 4)))
    ni_hist = list(reversed(_series_values(financials, "Net Income", 4)))

    rev_cagr = _cagr(rev_hist[0], rev_hist[-1], len(rev_hist) - 1) if len(rev_hist) >= 2 else None
    ni_cagr = _cagr(ni_hist[0], ni_hist[-1], len(ni_hist) - 1) if len(ni_hist) >= 2 else None

    gross_margins: list[float] = []
    op_margins: list[float] = []
    ncols = financials.shape[1] if financials is not None and not financials.empty else 0
    for i in range(min(3, ncols)):
        rev = _safe_series_value(financials, "Total Revenue", i)
        gp = _safe_series_value(financials, "Gross Profit", i)
        oi = _safe_series_value(financials, "Operating Income", i)
        if rev and rev > 0:
            if gp is not None:
                gross_margins.append(gp / rev * 100)
            if oi is not None:
                op_margins.append(oi / rev * 100)

    gross_trend = _margin_trend(list(reversed(gross_margins)))
    op_trend = _margin_trend(list(reversed(op_margins)))

    current_assets = _safe_series_value(balance_sheet, "Current Assets", 0)
    current_liab = _safe_series_value(balance_sheet, "Current Liabilities", 0)
    current_ratio = (
        current_assets / current_liab
        if current_assets and current_liab and current_liab > 0
        else None
    )

    ni_ttm = ni_hist[-1] if ni_hist else _safe_series_value(financials, "Net Income", 0)
    fcf_ni = (free_cash_flow / ni_ttm) if free_cash_flow and ni_ttm and ni_ttm > 0 else None

    base_rev = revenue or (rev_hist[-1] if rev_hist else None)
    growth = rev_cagr if rev_cagr is not None else (revenue_growth or 5.0)
    if revenue_growth is not None:
        growth = (growth + revenue_growth) / 2
    growth = max(-5.0, min(25.0, growth))
    g = growth / 100

    proj_rev_y1 = base_rev * (1 + g) if base_rev else None
    proj_rev_y3 = base_rev * ((1 + g) ** 3) if base_rev else None

    op_margin = (operating_margin or 15.0) / 100
    tax_rate = 0.21
    proj_ni_y1 = proj_rev_y1 * op_margin * (1 - tax_rate) if proj_rev_y1 else None
    proj_ni_y3 = proj_rev_y3 * op_margin * (1 - tax_rate) if proj_rev_y3 else None

    score = 0.0
    strengths: list[str] = []
    weaknesses: list[str] = []

    if rev_cagr is not None and rev_cagr > 8:
        score += 0.2
        strengths.append(f"Revenue CAGR {rev_cagr:.1f}% (3Y)")
    elif rev_cagr is not None and rev_cagr < 0:
        score -= 0.2
        weaknesses.append(f"Revenue declining ({rev_cagr:.1f}% CAGR)")

    if op_trend == "Improving":
        score += 0.15
        strengths.append("Operating margin improving")
    elif op_trend == "Deteriorating":
        score -= 0.15
        weaknesses.append("Operating margin deteriorating")

    if current_ratio is not None:
        if current_ratio >= 1.5:
            score += 0.1
            strengths.append(f"Current ratio {current_ratio:.2f}x")
        elif current_ratio < 1.0:
            score -= 0.15
            weaknesses.append(f"Current ratio {current_ratio:.2f}x — liquidity pressure")

    if debt_to_equity is not None:
        if debt_to_equity > 150:
            score -= 0.15
            weaknesses.append(f"Elevated leverage (D/E {debt_to_equity:.0f}%)")
        elif debt_to_equity < 60:
            score += 0.1
            strengths.append("Conservative balance sheet")

    if roe is not None:
        if roe > 18:
            score += 0.15
            strengths.append(f"Strong ROE {roe:.1f}%")
        elif roe < 8:
            score -= 0.1
            weaknesses.append(f"Weak ROE {roe:.1f}%")

    if fcf_ni is not None:
        if fcf_ni > 0.8:
            score += 0.1
            strengths.append("FCF supports reported earnings")
        elif fcf_ni < 0.3:
            score -= 0.1
            weaknesses.append("Low FCF vs net income")

    score = max(-1.0, min(1.0, score))
    rating = "Strong" if score >= 0.25 else ("Weak" if score <= -0.25 else "Stable")

    return FinancialStatementSummary(
        health_score=score,
        health_rating=rating,
        revenue_cagr_3y=rev_cagr,
        ni_cagr_3y=ni_cagr,
        gross_margin_trend=gross_trend,
        operating_margin_trend=op_trend,
        current_ratio=current_ratio,
        debt_to_equity=debt_to_equity,
        roe=roe,
        fcf_to_ni=fcf_ni,
        projected_revenue_y1=proj_rev_y1,
        projected_revenue_y3=proj_rev_y3,
        projected_ni_y1=proj_ni_y1,
        projected_ni_y3=proj_ni_y3,
        projection_growth_assumption=growth,
        strengths=strengths,
        weaknesses=weaknesses,
        notes=[
            f"Projection: {growth:.1f}% revenue growth (hist. CAGR + TTM blend)",
            "Sales forecast → NI via operating margin & tax",
        ],
    )


def build_fsa_table(fsa: FinancialStatementSummary) -> list[list[str]]:
    rows = [["Metric", "Value", "Assessment"]]
    rows.append(["FSA Health Score", f"{fsa.health_score:+.2f}", fsa.health_rating])
    rows.append(["Revenue CAGR (3Y)", f"{fsa.revenue_cagr_3y:.1f}%" if fsa.revenue_cagr_3y is not None else "N/A", ""])
    rows.append(["Net Income CAGR (3Y)", f"{fsa.ni_cagr_3y:.1f}%" if fsa.ni_cagr_3y is not None else "N/A", ""])
    rows.append(["Gross Margin Trend", fsa.gross_margin_trend, ""])
    rows.append(["Operating Margin Trend", fsa.operating_margin_trend, ""])
    rows.append(["Current Ratio", f"{fsa.current_ratio:.2f}x" if fsa.current_ratio else "N/A", "Liquidity"])
    rows.append(["Debt / Equity", f"{fsa.debt_to_equity:.0f}%" if fsa.debt_to_equity else "N/A", "Leverage"])
    rows.append(["ROE", f"{fsa.roe:.1f}%" if fsa.roe else "N/A", "Profitability"])
    rows.append(["FCF / Net Income", f"{fsa.fcf_to_ni:.2f}x" if fsa.fcf_to_ni else "N/A", "Earnings quality"])
    rows.append([
        "Proj. Revenue (Y1 / Y3)",
        f"{_fmt_large(fsa.projected_revenue_y1)} / {_fmt_large(fsa.projected_revenue_y3)}",
        f"@{fsa.projection_growth_assumption:.1f}%" if fsa.projection_growth_assumption else "",
    ])
    rows.append([
        "Proj. Net Income (Y1 / Y3)",
        f"{_fmt_large(fsa.projected_ni_y1)} / {_fmt_large(fsa.projected_ni_y3)}",
        "Margin × (1−tax)",
    ])
    return rows


def build_fsa_narrative(fsa: FinancialStatementSummary) -> str:
    parts = [f"Financial statement profile: {fsa.health_rating} (score {fsa.health_score:+.2f})."]
    if fsa.strengths:
        parts.append("Strengths: " + "; ".join(fsa.strengths[:3]) + ".")
    if fsa.weaknesses:
        parts.append("Risks: " + "; ".join(fsa.weaknesses[:3]) + ".")
    if fsa.projection_growth_assumption is not None:
        parts.append(
            f"3Y projection: ~{fsa.projection_growth_assumption:.1f}% revenue growth; "
            f"Y3 revenue {_fmt_large(fsa.projected_revenue_y3)}."
        )
    return " ".join(parts)
