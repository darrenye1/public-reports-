"""
Blend fundamental valuation, technical, quantitative, and FSA into composite investment signal.
"""

from __future__ import annotations

from dataclasses import dataclass

from financial_statement_analysis import FinancialStatementSummary
from market_analytics import BacktestSummary, QuantSummary, TechnicalSummary


WEIGHT_FUNDAMENTAL = 0.45
WEIGHT_FSA = 0.20
WEIGHT_TECHNICAL = 0.20
WEIGHT_QUANT = 0.15


@dataclass
class InvestmentSignal:
    fundamental_rating: str
    technical_signal: str
    quant_signal: str
    fsa_rating: str
    composite_score: float
    confluence_pct: float
    composite_rating: str
    action_note: str


def _fundamental_score(upside_pct: float | None, rating: str) -> float:
    if upside_pct is not None:
        return max(-1.0, min(1.0, upside_pct / 25.0))
    r = rating.upper()
    if "BUY" in r:
        return 0.8
    if "OVERWEIGHT" in r:
        return 0.45
    if "UNDERWEIGHT" in r:
        return -0.45
    if "SELL" in r:
        return -0.8
    return 0.0


def _technical_score(tech: TechnicalSummary) -> float:
    if tech.golden_cross:
        return 0.85
    if tech.death_cross:
        return -0.85
    if tech.signal == "BULLISH":
        return 0.5
    if tech.signal == "BEARISH":
        return -0.5
    return 0.0


def _quant_score(quant: QuantSummary) -> float:
    return max(-1.0, min(1.0, quant.quant_score))


def _fsa_score(fsa: FinancialStatementSummary) -> float:
    return max(-1.0, min(1.0, fsa.health_score))


def _score_to_rating(score: float) -> str:
    if score >= 0.55:
        return "BUY"
    if score >= 0.25:
        return "OVERWEIGHT"
    if score <= -0.55:
        return "SELL"
    if score <= -0.25:
        return "UNDERWEIGHT"
    return "HOLD"


_RATING_RANK = {"BUY": 5, "OVERWEIGHT": 4, "HOLD": 3, "UNDERWEIGHT": 2, "SELL": 1}


def _bearish_cap(rating: str, floor: str) -> str:
    """Cap rating at floor when valuation is materially negative (floor is more bearish)."""
    if _RATING_RANK.get(rating, 3) > _RATING_RANK[floor]:
        return floor
    return rating


def _apply_valuation_anchor(
    comp_rating: str,
    composite: float,
    upside_pct: float | None,
    fund_rating: str,
) -> str:
    """Prevent composite HOLD/BUY when target implies large downside."""
    fr = fund_rating.upper()
    if upside_pct is not None:
        if upside_pct <= -25:
            return "SELL" if composite <= 0.05 else "UNDERWEIGHT"
        if upside_pct <= -15 or fr == "SELL":
            return _bearish_cap(comp_rating, "UNDERWEIGHT")
        if upside_pct <= -10 and fr == "UNDERWEIGHT":
            return _bearish_cap(comp_rating, "HOLD")
        if upside_pct >= 35 and composite >= 0.50:
            return "BUY"
        if upside_pct >= 20 and composite >= 0.30:
            if _RATING_RANK.get(comp_rating, 3) < _RATING_RANK["OVERWEIGHT"]:
                return "OVERWEIGHT"
    elif fr == "SELL":
        return _bearish_cap(comp_rating, "UNDERWEIGHT")
    return comp_rating


def blend_investment_signal(
    fundamental_rating: str,
    upside_pct: float | None,
    technical: TechnicalSummary,
    quant: QuantSummary,
    fsa: FinancialStatementSummary,
    backtest: BacktestSummary | None = None,
) -> InvestmentSignal:
    f_score = _fundamental_score(upside_pct, fundamental_rating)
    t_score = _technical_score(technical)
    q_score = _quant_score(quant)
    s_score = _fsa_score(fsa)

    if backtest and not backtest.strategy_beats_bh:
        t_score *= 0.65

    composite = (
        WEIGHT_FUNDAMENTAL * f_score
        + WEIGHT_FSA * s_score
        + WEIGHT_TECHNICAL * t_score
        + WEIGHT_QUANT * q_score
    )
    composite = max(-1.0, min(1.0, composite))

    signs = [f_score, t_score, q_score, s_score]
    pos = sum(1 for x in signs if x > 0.15)
    neg = sum(1 for x in signs if x < -0.15)
    aligned = max(pos, neg)
    confluence = aligned / 4 * 100

    comp_rating = _score_to_rating(composite)
    anchored = _apply_valuation_anchor(comp_rating, composite, upside_pct, fundamental_rating)
    valuation_overrode = anchored != comp_rating
    comp_rating = anchored

    notes: list[str] = []
    if valuation_overrode and upside_pct is not None and upside_pct <= -10:
        notes.append(f"valuation anchor: {upside_pct:+.0f}% upside vs target")
    elif valuation_overrode and upside_pct is not None and upside_pct >= 20:
        notes.append(f"valuation anchor: {upside_pct:+.0f}% upside vs target")
    if technical.golden_cross:
        notes.append("recent Golden Cross")
    if f_score > 0.2 and t_score > 0.2:
        notes.append("valuation + technical aligned bullish")
    if f_score < -0.2 and t_score > 0.2:
        notes.append("valuation rich but trend improving — wait for confirmation")
    if f_score < -0.2 and t_score < -0.2:
        notes.append("fundamental and technical both bearish")
    if s_score > 0.2:
        notes.append("solid financial statement profile")
    if not notes:
        notes.append("mixed signals across pillars")

    return InvestmentSignal(
        fundamental_rating=fundamental_rating,
        technical_signal=technical.signal,
        quant_signal=quant.signal,
        fsa_rating=fsa.health_rating,
        composite_score=composite,
        confluence_pct=confluence,
        composite_rating=comp_rating,
        action_note="; ".join(notes).capitalize() + ".",
    )
