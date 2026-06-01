#!/usr/bin/env python3
"""Copy reports to public/reports and build summary-data.js for the website."""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "reports"
DST = ROOT / "public" / "reports"
PDF_TICKERS = ["NVDA", "GOOGL", "AAPL", "MSFT", "AMZN", "TSLA", "BX"]


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    for name in ("Top20_Summary.csv", "Top20_Summary.pdf"):
        src = SRC / name
        if src.is_file():
            shutil.copy2(src, DST / name)

    for ticker in PDF_TICKERS:
        src = SRC / f"{ticker}_research.pdf"
        if src.is_file():
            shutil.copy2(src, DST / src.name)

    csv_path = DST / "Top20_Summary.csv"
    if not csv_path.is_file():
        csv_path = SRC / "Top20_Summary.csv"
    rows: list[dict[str, str]] = []
    if csv_path.is_file():
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

    js_path = ROOT / "public" / "summary-data.js"
    js_path.write_text(
        "window.SUMMARY_ROWS = " + json.dumps(rows, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    print("Synced reports to public/reports")
    print(f"Wrote {len(rows)} rows to public/summary-data.js")


if __name__ == "__main__":
    main()
