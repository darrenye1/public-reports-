"""
Technical & quantitative market analytics (MGTA 632 Topics 5–6).

SMA golden/death cross (42/252), momentum, risk metrics, and SMA backtest vs buy-and-hold.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# Topic 5 SMA backtest parameters
SMA_SHORT_WINDOW = 42
SMA_LONG_WINDOW = 252
CROSS_LOOKBACK_DAYS = 20
RSI_PERIOD = 14
RISK_FREE_RATE = 0.04
TRADING_DAYS = 252
BACKTEST_COST_PCT = 0.001  # 0.10% per trade side


@dataclass
class TechnicalSummary:
    sma_short: float | None = None
    sma_long: float | None = None
    rsi_14: float | None = None
    trend: str = "Neutral"
    golden_cross: bool = False
    death_cross: bool = False
    days_since_cross: int | None = None
    cross_type: str | None = None
    signal: str = "NEUTRAL"
    notes: list[str] = field(default_factory=list)


@dataclass
class QuantSummary:
    momentum_12m: float | None = None
    momentum_3m: float | None = None
    volatility_ann: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown: float | None = None
    beta: float | None = None
    rel_strength_vs_spy: float | None = None
    quant_score: float = 0.0
    signal: str = "NEUTRAL"
    notes: list[str] = field(default_factory=list)


@dataclass
class BacktestSummary:
    strategy_ann_return: float | None = None
    buyhold_ann_return: float | None = None
    strategy_sharpe: float | None = None
    num_trades: int = 0
    cost_adjusted_ann_return: float | None = None
    strategy_beats_bh: bool = False
    notes: list[str] = field(default_factory=list)


def _close_series(history: pd.DataFrame | None) -> pd.Series | None:
    if history is None or history.empty or "Close" not in history.columns:
        return None
    s = history["Close"].dropna()
    return s if len(s) >= 30 else None


def _rsi(close: pd.Series, period: int = RSI_PERIOD) -> float | None:
    if len(close) < period + 1:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    val = 100 - (100 / (1 + rs))
    last = val.iloc[-1]
    return float(last) if pd.notna(last) else None


def _detect_crosses(
    close: pd.Series,
    short: int = SMA_SHORT_WINDOW,
    long: int = SMA_LONG_WINDOW,
    lookback: int = CROSS_LOOKBACK_DAYS,
) -> tuple[bool, bool, int | None, str | None]:
    if len(close) < long + 5:
        return False, False, None, None
    sma_s = close.rolling(short).mean()
    sma_l = close.rolling(long).mean()
    spread = sma_s - sma_l
    cross_up = (spread > 0) & (spread.shift(1) <= 0)
    cross_down = (spread < 0) & (spread.shift(1) >= 0)

    recent_gc = bool(cross_up.tail(lookback).any())
    recent_dc = bool(cross_down.tail(lookback).any())

    days_since: int | None = None
    cross_type: str | None = None
    for i in range(len(cross_up) - 1, max(len(cross_up) - lookback - 1, 0), -1):
        if cross_up.iloc[i]:
            days_since = len(cross_up) - 1 - i
            cross_type = "Golden Cross"
            break
        if cross_down.iloc[i]:
            days_since = len(cross_down) - 1 - i
            cross_type = "Death Cross"
            break

    return recent_gc, recent_dc, days_since, cross_type


def build_technical_summary(history: pd.DataFrame | None) -> TechnicalSummary:
    close = _close_series(history)
    if close is None:
        return TechnicalSummary(notes=["Insufficient price history for technical analysis"])

    sma_s = float(close.rolling(SMA_SHORT_WINDOW).mean().iloc[-1]) if len(close) >= SMA_SHORT_WINDOW else None
    sma_l = float(close.rolling(SMA_LONG_WINDOW).mean().iloc[-1]) if len(close) >= SMA_LONG_WINDOW else None
    rsi = _rsi(close)
    recent_gc, recent_dc, days_since, cross_type = _detect_crosses(close)

    last = float(close.iloc[-1])
    if sma_s and sma_l:
        if sma_s > sma_l * 1.01:
            trend = "Bullish"
        elif sma_s < sma_l * 0.99:
            trend = "Bearish"
        else:
            trend = "Neutral"
    else:
        trend = "Neutral"

    notes: list[str] = []
    signal = "NEUTRAL"
    if recent_gc:
        signal = "BULLISH"
        notes.append(f"Golden Cross within last {CROSS_LOOKBACK_DAYS}d (SMA{SMA_SHORT_WINDOW} > SMA{SMA_LONG_WINDOW})")
    elif recent_dc:
        signal = "BEARISH"
        notes.append(f"Death Cross within last {CROSS_LOOKBACK_DAYS}d")
    elif trend == "Bullish":
        signal = "BULLISH"
        notes.append(f"Price above SMA{SMA_SHORT_WINDOW}; SMA{SMA_SHORT_WINDOW} > SMA{SMA_LONG_WINDOW}")
    elif trend == "Bearish":
        signal = "BEARISH"
        notes.append(f"SMA{SMA_SHORT_WINDOW} below SMA{SMA_LONG_WINDOW}")

    if rsi is not None:
        if rsi > 70:
            notes.append(f"RSI {rsi:.0f} — overbought zone")
        elif rsi < 30:
            notes.append(f"RSI {rsi:.0f} — oversold zone")

    if sma_s and last:
        notes.append(f"SMA{SMA_SHORT_WINDOW}=${sma_s:.2f}, SMA{SMA_LONG_WINDOW}=${sma_l:.2f}" if sma_l else f"SMA{SMA_SHORT_WINDOW}=${sma_s:.2f}")

    return TechnicalSummary(
        sma_short=sma_s,
        sma_long=sma_l,
        rsi_14=rsi,
        trend=trend,
        golden_cross=recent_gc,
        death_cross=recent_dc,
        days_since_cross=days_since,
        cross_type=cross_type,
        signal=signal,
        notes=notes,
    )


def _ann_return(daily_rets: pd.Series) -> float | None:
    if daily_rets is None or daily_rets.empty:
        return None
    total = float((1 + daily_rets).prod())
    years = len(daily_rets) / TRADING_DAYS
    if years <= 0 or total <= 0:
        return None
    return total ** (1 / years) - 1


def _max_drawdown(close: pd.Series) -> float | None:
    if close is None or len(close) < 2:
        return None
    roll_max = close.cummax()
    dd = close / roll_max - 1
    return float(dd.min()) * 100


def build_quant_summary(
    history: pd.DataFrame | None,
    beta: float | None = None,
    spy_history: pd.DataFrame | None = None,
) -> QuantSummary:
    close = _close_series(history)
    if close is None:
        return QuantSummary(notes=["Insufficient history for quantitative metrics"])

    rets = close.pct_change().dropna()
    mom_12m = None
    mom_3m = None
    if len(close) >= TRADING_DAYS:
        mom_12m = (float(close.iloc[-1]) / float(close.iloc[-TRADING_DAYS]) - 1) * 100
    if len(close) >= 63:
        mom_3m = (float(close.iloc[-1]) / float(close.iloc[-63]) - 1) * 100

    vol = float(rets.std() * np.sqrt(TRADING_DAYS) * 100) if len(rets) > 20 else None
    ann_ret = _ann_return(rets)
    sharpe = None
    if ann_ret is not None and vol and vol > 0:
        sharpe = (ann_ret - RISK_FREE_RATE) / (vol / 100)

    mdd = _max_drawdown(close)

    rel_spy = None
    if spy_history is not None and not spy_history.empty and "Close" in spy_history.columns:
        spy = spy_history["Close"].reindex(close.index).ffill().dropna()
        aligned = pd.concat([close, spy], axis=1, join="inner").dropna()
        if len(aligned) >= 63:
            c0, s0 = aligned.iloc[0, 0], aligned.iloc[0, 1]
            c1, s1 = aligned.iloc[-1, 0], aligned.iloc[-1, 1]
            if c0 and s0:
                rel_spy = ((c1 / c0) - (s1 / s0)) * 100

    score = 0.0
    notes: list[str] = []
    if mom_12m is not None:
        if mom_12m > 15:
            score += 0.35
            notes.append(f"12m momentum +{mom_12m:.1f}%")
        elif mom_12m > 0:
            score += 0.15
        elif mom_12m < -15:
            score -= 0.35
            notes.append(f"12m momentum {mom_12m:.1f}%")
        else:
            score -= 0.1
    if sharpe is not None:
        if sharpe > 1.0:
            score += 0.25
            notes.append(f"Sharpe {sharpe:.2f}")
        elif sharpe > 0.5:
            score += 0.1
        elif sharpe < 0:
            score -= 0.2
    if rel_spy is not None:
        if rel_spy > 5:
            score += 0.2
            notes.append(f"Outperforming SPY by {rel_spy:.1f}% (period)")
        elif rel_spy < -5:
            score -= 0.2
    if mdd is not None and mdd < -35:
        score -= 0.15
        notes.append(f"Max drawdown {mdd:.1f}%")

    score = max(-1.0, min(1.0, score))
    if score >= 0.25:
        signal = "POSITIVE"
    elif score <= -0.25:
        signal = "NEGATIVE"
    else:
        signal = "NEUTRAL"

    return QuantSummary(
        momentum_12m=mom_12m,
        momentum_3m=mom_3m,
        volatility_ann=vol,
        sharpe_ratio=sharpe,
        max_drawdown=mdd,
        beta=beta,
        rel_strength_vs_spy=rel_spy,
        quant_score=score,
        signal=signal,
        notes=notes,
    )


def run_sma_backtest(history: pd.DataFrame | None) -> BacktestSummary:
    """Topic 5: long when SMA42 > SMA252, else cash."""
    close = _close_series(history)
    if close is None or len(close) < SMA_LONG_WINDOW + 10:
        return BacktestSummary(notes=["Need 252+ trading days for SMA backtest"])

    sma_s = close.rolling(SMA_SHORT_WINDOW).mean()
    sma_l = close.rolling(SMA_LONG_WINDOW).mean()
    position = (sma_s > sma_l).astype(float)
    position = position.shift(1).fillna(0)

    rets = close.pct_change().fillna(0)
    strat_rets = rets * position
    bh_rets = rets

    strat_ann = _ann_return(strat_rets[SMA_LONG_WINDOW:])
    bh_ann = _ann_return(bh_rets[SMA_LONG_WINDOW:])
    strat_vol = float(strat_rets[SMA_LONG_WINDOW:].std() * np.sqrt(TRADING_DAYS))
    strat_sharpe = (
        (strat_ann - RISK_FREE_RATE) / strat_vol if strat_ann is not None and strat_vol > 0 else None
    )

    trades = int((position.diff().abs() > 0).sum())
    years = max(len(strat_rets[SMA_LONG_WINDOW:]) / TRADING_DAYS, 0.1)
    cost_drag = (trades * BACKTEST_COST_PCT) / years
    cost_adj = strat_ann - cost_drag if strat_ann is not None else None

    beats = bool(strat_ann is not None and bh_ann is not None and strat_ann > bh_ann)
    notes = [
        f"SMA{SMA_SHORT_WINDOW}/{SMA_LONG_WINDOW} rule vs buy-and-hold",
        f"Trades: {trades}, est. cost drag {cost_drag * 100:.2f}%/yr",
    ]
    if not beats:
        notes.append("Strategy underperformed B&H historically — use TA as timing overlay only")

    return BacktestSummary(
        strategy_ann_return=strat_ann * 100 if strat_ann is not None else None,
        buyhold_ann_return=bh_ann * 100 if bh_ann is not None else None,
        strategy_sharpe=strat_sharpe,
        num_trades=trades,
        cost_adjusted_ann_return=cost_adj * 100 if cost_adj is not None else None,
        strategy_beats_bh=beats,
        notes=notes,
    )


def build_technical_table(tech: TechnicalSummary) -> list[list[str]]:
    rows = [["Metric", "Value", "Notes"]]
    rows.append(["SMA (42d)", f"${tech.sma_short:.2f}" if tech.sma_short else "N/A", "Short-term trend"])
    rows.append(["SMA (252d)", f"${tech.sma_long:.2f}" if tech.sma_long else "N/A", "Long-term trend"])
    rows.append(["RSI (14d)", f"{tech.rsi_14:.1f}" if tech.rsi_14 else "N/A", "Momentum oscillator"])
    rows.append(["Trend", tech.trend, ""])
    gc = "Yes" if tech.golden_cross else "No"
    dc = "Yes" if tech.death_cross else "No"
    rows.append(["Golden Cross (20d)", gc, tech.cross_type or ""])
    rows.append(["Death Cross (20d)", dc, f"{tech.days_since_cross}d ago" if tech.days_since_cross else ""])
    rows.append(["TA Signal", tech.signal, "; ".join(tech.notes[:2]) if tech.notes else ""])
    return rows


def build_quant_table(quant: QuantSummary, backtest: BacktestSummary) -> list[list[str]]:
    rows = [["Metric", "Value", "Notes"]]
    rows.append(["12m Momentum", f"{quant.momentum_12m:+.1f}%" if quant.momentum_12m is not None else "N/A", ""])
    rows.append(["3m Momentum", f"{quant.momentum_3m:+.1f}%" if quant.momentum_3m is not None else "N/A", ""])
    rows.append(["Ann. Volatility", f"{quant.volatility_ann:.1f}%" if quant.volatility_ann else "N/A", ""])
    rows.append(["Sharpe Ratio", f"{quant.sharpe_ratio:.2f}" if quant.sharpe_ratio is not None else "N/A", "Rf=4%"])
    rows.append(["Max Drawdown", f"{quant.max_drawdown:.1f}%" if quant.max_drawdown is not None else "N/A", ""])
    rows.append(["Rel. Strength vs SPY", f"{quant.rel_strength_vs_spy:+.1f}%" if quant.rel_strength_vs_spy is not None else "N/A", ""])
    rows.append(["Quant Score", f"{quant.quant_score:+.2f}", quant.signal])
    if backtest.strategy_ann_return is not None:
        rows.append([
            "SMA Backtest (ann.)",
            f"{backtest.strategy_ann_return:.1f}%",
            f"B&H {backtest.buyhold_ann_return:.1f}%" if backtest.buyhold_ann_return else "",
        ])
    return rows
