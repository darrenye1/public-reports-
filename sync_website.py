#!/usr/bin/env python3
"""Copy reports to public/ and docs/; build summary-data.js for the website."""
from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "reports"
PUBLIC = ROOT / "public"
DOCS = ROOT / "docs"
def _copy_reports(src_dir: Path, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in ("Top20_Summary.csv", "Top20_Summary.pdf"):
        s = src_dir / name
        if s.is_file():
            shutil.copy2(s, dst_dir / name)
    src_pdfs = {p.name for p in src_dir.glob("*_research.pdf")}
    for pdf in sorted(src_dir.glob("*_research.pdf")):
        shutil.copy2(pdf, dst_dir / pdf.name)
    for stale in dst_dir.glob("*_research.pdf"):
        if stale.name not in src_pdfs:
            stale.unlink()


def main() -> None:
    csv_path = SRC / "Top20_Summary.csv"
    rows: list[dict[str, str]] = []
    if csv_path.is_file():
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

    as_of = datetime.now().strftime("%Y-%m-%d")
    js = (
        f'window.DATA_AS_OF = "{as_of}";\n'
        + "window.SUMMARY_ROWS = "
        + json.dumps(rows, ensure_ascii=False, indent=2)
        + ";\n"
    )

    for web_root in (PUBLIC, DOCS):
        web_root.mkdir(parents=True, exist_ok=True)
        _copy_reports(SRC, web_root / "reports")
        (web_root / "summary-data.js").write_text(js, encoding="utf-8")
        index_src = PUBLIC / "index.html"
        if index_src.is_file() and web_root != PUBLIC:
            shutil.copy2(index_src, web_root / "index.html")
        for name in ("og-preview.png", "social-card.jpg", "robots.txt"):
            src = PUBLIC / name
            if src.is_file() and web_root != PUBLIC:
                try:
                    shutil.copy2(src, web_root / name)
                except OSError:
                    pass

    print("Synced to public/ and docs/")
    print(f"Wrote {len(rows)} rows, DATA_AS_OF={as_of}")


if __name__ == "__main__":
    main()
