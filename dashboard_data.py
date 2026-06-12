#!/usr/bin/env python3
"""Fetch market news and index series for the website dashboard."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from zoneinfo import ZoneInfo

import yfinance as yf

ET = ZoneInfo("America/New_York")
NEWS_TICKERS = (
    "SPY", "^GSPC", "QQQ", "^VIX", "DX-Y.NYB", "GC=F",
    "DIA", "IWM", "TLT", "HYG", "XLF", "XLE", "GLD",
)
INDEX_CHARTS = (
    ("^GSPC", "S&P 500"),
    ("^DJI", "Dow Jones"),
    ("^IXIC", "Nasdaq Composite"),
    ("^RUT", "Russell 2000"),
)

MACRO_KEYWORDS = (
    "fed", "federal reserve", "fomc", "inflation", "cpi", "ppi", "gdp", "jobs",
    "unemployment", "nonfarm", "treasury", "yield", "rate cut", "rate hike",
    "interest rate", "s&p", "market", "stocks", "nasdaq", "dow", "rally", "selloff",
    "tariff", "trade war", "recession", "geopolit", "oil", "crude", "opec",
    "earnings season", "volatility", "vix", "bond", "dollar", "china", "war",
    "semiconductor", "ai ", "chip", "debt ceiling", "shutdown", "payroll",
)

PREMIUM_SOURCES: tuple[tuple[str, int], ...] = (
    ("wall street journal", 4),
    ("barrons.com", 4),
    ("barrons", 4),
    ("reuters", 4),
    ("bloomberg", 4),
    ("financial times", 3),
    ("cnbc", 2),
    ("marketwatch", 2),
    ("investor's business daily", 2),
    ("associated press", 2),
    ("ap news", 2),
)

HIGH_IMPACT_TERMS = (
    "fed", "fomc", "cpi", "ppi", "jobs report", "nonfarm", "payroll", "tariff",
    "selloff", "rally", "surge", "plunge", "crash", "rate cut", "rate hike",
    "recession", "inflation", "treasury", "vix", "geopolit", "war", "ipo",
    "earnings", "gdp", "shutdown", "debt ceiling",
)


def _parse_news_date(raw: str | int | float | None) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(float(raw), tz=timezone.utc)
        except (OSError, ValueError, OverflowError):
            return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def _news_item_fields(item: dict[str, Any]) -> dict[str, str] | None:
    content = item.get("content") if isinstance(item.get("content"), dict) else item
    if not isinstance(content, dict):
        return None
    title = (content.get("title") or "").strip()
    if not title:
        return None
    pub = _parse_news_date(content.get("pubDate") or content.get("displayTime"))
    url = ""
    for key in ("clickThroughUrl", "canonicalUrl"):
        block = content.get(key)
        if isinstance(block, dict) and block.get("url"):
            url = str(block["url"])
            break
    provider = content.get("provider") or {}
    source = provider.get("displayName", "Yahoo Finance") if isinstance(provider, dict) else "Yahoo Finance"
    summary = (content.get("summary") or content.get("description") or "")[:280]
    return {
        "title": title,
        "url": url,
        "source": str(source),
        "summary": summary,
        "published": pub.isoformat() if pub else "",
        "published_display": pub.strftime("%b %d, %Y") if pub else "",
    }


def _macro_score(title: str, summary: str) -> int:
    text = f"{title} {summary}".lower()
    return sum(1 for kw in MACRO_KEYWORDS if kw in text)


def _impact_score(title: str, summary: str, source: str) -> int:
    """Rank headlines by macro relevance + source quality + market-moving terms."""
    text = f"{title} {summary}".lower()
    score = _macro_score(title, summary) * 3
    src = source.lower()
    for name, pts in PREMIUM_SOURCES:
        if name in src:
            score += pts
            break
    score += sum(2 for term in HIGH_IMPACT_TERMS if term in text)
    if any(k in text for k in ("s&p 500", "s&p", "dow jones", "dow", "nasdaq", "russell")):
        score += 2
    return score


def _collect_news_candidates(max_age_days: int = 7) -> list[tuple[int, datetime, dict[str, str]]]:
    """Gather deduplicated Yahoo Finance stories within the lookback window."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    seen_titles: set[str] = set()
    candidates: list[tuple[int, datetime, dict[str, str]]] = []

    for ticker in NEWS_TICKERS:
        try:
            items = yf.Ticker(ticker).news or []
        except Exception:
            continue
        for raw in items:
            parsed = _news_item_fields(raw)
            if not parsed:
                continue
            norm = re.sub(r"\s+", " ", parsed["title"].lower())
            if norm in seen_titles:
                continue
            pub = _parse_news_date(parsed["published"])
            if not pub or pub < cutoff:
                continue
            seen_titles.add(norm)
            impact = _impact_score(parsed["title"], parsed["summary"], parsed["source"])
            candidates.append((impact, pub, parsed))

    return candidates


def _day_key_et(dt: datetime) -> str:
    return dt.astimezone(ET).strftime("%Y-%m-%d")


def fetch_macro_news(days: int = 7) -> list[dict[str, str]]:
    """One high-impact macro/market headline per calendar day (past week, newest first)."""
    now_et = datetime.now(ET)
    candidates = _collect_news_candidates(max_age_days=days + 1)

    by_day: dict[str, list[tuple[int, datetime, dict[str, str]]]] = {}
    for item in candidates:
        _, pub, _ = item
        by_day.setdefault(_day_key_et(pub), []).append(item)

    picked: list[dict[str, str]] = []
    used_titles: set[str] = set()
    for offset in range(days):
        day_key = (now_et - timedelta(days=offset)).strftime("%Y-%m-%d")
        pool = [
            row for row in by_day.get(day_key, [])
            if re.sub(r"\s+", " ", row[2]["title"].lower()) not in used_titles
        ]
        if not pool:
            continue
        _, _, story = max(pool, key=lambda row: (row[0], row[1].timestamp()))
        used_titles.add(re.sub(r"\s+", " ", story["title"].lower()))
        story = dict(story)
        story["day"] = day_key
        picked.append(story)

    return picked


def fetch_index_charts(period: str = "6mo") -> list[dict[str, Any]]:
    """Normalized index price series for dashboard sparkline charts."""
    charts: list[dict[str, Any]] = []
    for symbol, label in INDEX_CHARTS:
        try:
            hist = yf.Ticker(symbol).history(period=period, auto_adjust=True)
        except Exception:
            continue
        if hist is None or hist.empty:
            continue
        closes = [float(x) for x in hist["Close"].tolist() if x == x]
        if len(closes) < 2:
            continue
        start, end = closes[0], closes[-1]
        pct = (end / start - 1) * 100 if start else 0
        base = closes[0] or 1
        normalized = [round(c / base * 100, 2) for c in closes]
        dates = [d.strftime("%Y-%m-%d") for d in hist.index]
        charts.append({
            "symbol": symbol,
            "label": label,
            "last": round(end, 2),
            "change_pct": round(pct, 2),
            "dates": dates[-60:],
            "series": normalized[-60:],
        })
    return charts


def build_dashboard_payload() -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_as_of": datetime.now().strftime("%Y-%m-%d"),
        "news": fetch_macro_news(days=7),
        "indices": fetch_index_charts(),
    }


def write_dashboard_js(path: str) -> dict[str, Any]:
    payload = build_dashboard_payload()
    js = "window.DASHBOARD_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(js)
    return payload


if __name__ == "__main__":
    payload = write_dashboard_js("public/dashboard-data.js")
    print(f"News: {len(payload['news'])} | Indices: {len(payload['indices'])}")
