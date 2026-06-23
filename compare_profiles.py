#!/usr/bin/env python3
"""Compare valuation profiles for JPM, BRK-B, NVDA (Phase 1)."""
from __future__ import annotations

from equity_research import VALUATION_PROFILES, _analyze_ticker, resolve_valuation_profile

LEGACY_NOTES = {
    "JPM": "Before: DCF N/A, Comps N/A (no P/E for banks) -> Analyst-only target",
    "BRK-B": "Before: DCF N/A, Comps N/A (insurance) -> Analyst-only target",
    "NVDA": "Before: DCF ~59 excluded; Comps ~290; blend 28/44/28",
}


def report(ticker: str) -> None:
    result = _analyze_ticker(ticker)
    if not result:
        print(f"{ticker}: analysis failed")
        return
    _data, summary, _ind, comp, val = result
    pk = resolve_valuation_profile(summary)
    prof = VALUATION_PROFILES[pk]
    c = val.comps

    print("=" * 64)
    print(f"{ticker} | {summary.industry}")
    print(f"Legacy: {LEGACY_NOTES.get(ticker, 'n/a')}")
    print(f"Profile: {pk} - {prof['label']}")
    print(f"  comps multiples: {prof['comps']}")
    print(f"  profile weights: {prof['weights']}")
    print(f"Price: ${summary.current_price:.2f}")
    dcf_s = f"${val.dcf_target:.2f}" if val.dcf_target else "N/A"
    print(f"DCF: {dcf_s} (reliable={val.dcf_reliable})")
    pb_s = f"${c.implied_price_pb:.2f}" if c.implied_price_pb else "N/A"
    print(f"Comps P/B: {pb_s} (peer median P/B={c.peer_median_pb})")
    comps_s = f"${val.comps_target:.2f}" if val.comps_target else "N/A"
    print(f"Comps blended: {comps_s} (reliable={val.comps_reliable})")
    if c.implied_price_ps:
        print(f"  P/S implied: ${c.implied_price_ps:.2f}")
    if c.implied_price_ev_ebitda:
        print(f"  EV/EBITDA implied: ${c.implied_price_ev_ebitda:.2f}")
    an_s = f"${val.analyst_target:.2f}" if val.analyst_target else "N/A"
    print(f"Analyst: {an_s}")
    tgt = f"${val.target_price:.2f}" if val.target_price else "N/A"
    if summary.current_price and val.target_price:
        up = (val.target_price / summary.current_price - 1) * 100
        print(f"Target: {tgt} ({up:+.1f}% vs price) | {val.recommendation}")
    else:
        print(f"Target: {tgt} | {val.recommendation}")
    w = ", ".join(f"{k} {v:.0%}" for k, v in val.blend_weights.items())
    print(f"Active blend: {w or 'median fallback'}")
    if val.excluded_methods:
        print("Excluded:", "; ".join(f"{k}: {v}" for k, v in val.excluded_methods.items()))
    print(f"Peers: {[p.ticker for p in comp.peers]}")


def main() -> None:
    for t in ("JPM", "BRK-B", "NVDA"):
        report(t)


if __name__ == "__main__":
    main()
