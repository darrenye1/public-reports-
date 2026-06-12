#!/usr/bin/env python3
"""Fetch market news and index series for the website dashboard."""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import yfinance as yf

NEWS_TICKERS = ("SPY", "^GSPC", "QQQ", "^VIX", "DX-Y.NYB", "GC=F")
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


def fetch_macro_news(limit: int = 5, max_age_days: int = 7) -> list[dict[str, str]]:
    """Top macro/market headlines from the past week (Yahoo Finance)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    seen_titles: set[str] = set()
    scored: list[tuple[int, datetime, dict[str, str]]] = []

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
            if pub and pub < cutoff:
                continue
            score = _macro_score(parsed["title"], parsed["summary"])
            if score < 1:
                continue
            seen_titles.add(norm)
            scored.append((score, pub or datetime.min.replace(tzinfo=timezone.utc), parsed))

    scored.sort(key=lambda x: (-x[1].timestamp(), -x[0]))
    if len(scored) < limit:
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
                if pub and pub < cutoff:
                    continue
                seen_titles.add(norm)
                scored.append((0, pub or datetime.min.replace(tzinfo=timezone.utc), parsed))
                if len(scored) >= limit * 3:
                    break

    scored.sort(key=lambda x: (-x[1].timestamp(), -x[0]))
    return [row[2] for row in scored[:limit]]


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
        "news": fetch_macro_news(limit=5),
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
