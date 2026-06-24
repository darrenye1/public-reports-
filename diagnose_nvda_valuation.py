#!/usr/bin/env python3
"""Step-by-step NVDA valuation trace for blend-weight audit."""
from __future__ import annotations

from equity_research import (
    VALUATION_PROFILES,
    _analyze_ticker,
    _assess_dcf_reliability,
    _cap_target_sanity,
    _filter_valuation_methods,
    _needs_valuation_audit,
    resolve_valuation_profile,
)


def main() -> None:
    result = _analyze_ticker("NVDA")
    if not result:
        print("NVDA analysis failed")
        return
    _data, summary, _ind, _comp, val = result
    price = summary.current_price or 0
    pk = resolve_valuation_profile(summary)
    prof = VALUATION_PROFILES[pk]

    print("NVDA VALUATION TRACE")
    print("=" * 60)
    print(f"Price: ${price:.2f}")
    print(f"Profile: {pk} ({prof['label']})")
    print(f"Template weights: {prof['weights']}")
    print()
    print("Step 1 - Raw method prices:")
    print(f"  DCF:     ${val.dcf_target:.2f}" if val.dcf_target else "  DCF:     N/A")
    print(f"  Comps:   ${val.comps_target:.2f}" if val.comps_target else "  Comps:   N/A")
    print(f"  Analyst: ${val.analyst_target:.2f}" if val.analyst_target else "  Analyst: N/A")
    print(f"  Comps detail P/E ${val.comps.implied_price_pe:.2f}, EV/EBITDA ${val.comps.implied_price_ev_ebitda:.2f}, P/S ${val.comps.implied_price_ps:.2f}")

    methods = {}
    if val.dcf_target:
        methods["DCF"] = val.dcf_target
    if val.comps_target:
        methods["Comps"] = val.comps_target
    if val.analyst_target:
        methods["Analyst"] = val.analyst_target

    active, excluded = _filter_valuation_methods(methods, price)
    print()
    print("Step 2 - Outlier filter (active methods):")
    print(f"  Active: {active}")
    print(f"  Excluded: {excluded}")

    if val.dcf_target:
        ok, reason = _assess_dcf_reliability(val.dcf_target, price, val.comps_target)
        print(f"  DCF reliability: {ok} ({reason})")

    tpl = prof["weights"]
    w = {k: tpl[k] for k in active if k in tpl}
    total = sum(w.values())
    w_norm = {k: v / total for k, v in w.items()} if total else {}
    pre = sum(active[k] * w_norm[k] for k in active) if w_norm else None

    print()
    print("Step 3 - Profile-weighted blend (active methods only):")
    for k, wt in w_norm.items():
        print(f"  {k}: {wt:.1%} x ${active[k]:.2f} = ${active[k] * wt:.2f}")
    if pre:
        print(f"  => Pre-audit target: ${pre:.2f} ({(pre / price - 1) * 100:+.1f}% vs price)")

    print()
    print("Step 4 - Stored pre-audit vs final:")
    print(f"  pre_audit_target: ${val.pre_audit_target:.2f}" if val.pre_audit_target else "  pre_audit_target: N/A")
    print(f"  pre_audit_weights: {val.pre_audit_weights}")
    print(f"  final target:      ${val.target_price:.2f}" if val.target_price else "  final target: N/A")
    print(f"  final blend_weights: {val.blend_weights or '(cleared by audit)'}")

    if pre and price:
        audit = _needs_valuation_audit(pre, price, methods)
        capped, was = _cap_target_sanity(pre, price)
        print()
        print("Step 5 - Audit:")
        print(f"  Audit triggered (>=30% move): {audit}")
        print(f"  40% sanity cap applied: {was}")
        if capped:
            print(f"  Capped target: ${capped:.2f} ({(capped / price - 1) * 100:+.1f}%)")

    print()
    print("Step 6 - Default profile comparison (28/44/28 on Comps+Analyst):")
    old_w = {"Comps": 0.44, "Analyst": 0.28}
    old_total = sum(old_w[k] for k in active if k in old_w)
    old_norm = {k: old_w[k] / old_total for k in active if k in old_w}
    old_pre = sum(active[k] * old_norm[k] for k in old_norm)
    old_capped, _ = _cap_target_sanity(old_pre, price)
    print(f"  Old-style weighted: ${old_pre:.2f} -> capped ${old_capped:.2f}" if old_capped else "")


if __name__ == "__main__":
    main()
