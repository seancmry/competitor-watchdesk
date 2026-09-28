#!/usr/bin/env python3
"""Screenshot lab HTML pages and print the PDF report (Playwright).

Usage (from the demo root, after experiments.py):
  python scripts/make_lab_pdf.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMAGES = DOCS / "images"
PDF_NAME = {
    "publish-loop": "publish-loop-lab.pdf",
    "competitor-watchdesk": "watchdesk-lab.pdf",
}.get(ROOT.name, f"{ROOT.name}-lab.pdf")


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Install Playwright in this demo venv first:", file=sys.stderr)
        print("  pip install playwright && playwright install chromium", file=sys.stderr)
        return 1

    for needed in ("overview.html", "catalog.html", "results.html", "report.html"):
        if not (DOCS / needed).exists():
            print(f"Missing {needed}. Run python experiments.py first.", file=sys.stderr)
            return 1

    IMAGES.mkdir(parents=True, exist_ok=True)
    shots = [
        ("overview.html", "overview.png", 1100, 420),
        ("catalog.html", "catalog.png", 1100, 900),
        ("results.html", "results.png", 1100, 900),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        for html_name, png_name, w, h in shots:
            page.set_viewport_size({"width": w, "height": h})
            page.goto((DOCS / html_name).as_uri(), wait_until="networkidle")
            page.screenshot(path=str(IMAGES / png_name), full_page=True)
            print(f"wrote images/{png_name}")

        page.set_viewport_size({"width": 1100, "height": 1400})
        page.goto((DOCS / "report.html").as_uri(), wait_until="networkidle")
        out_pdf = DOCS / PDF_NAME
        page.pdf(path=str(out_pdf), format="A4", print_background=True)
        print(f"wrote {out_pdf.relative_to(ROOT)}")
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
