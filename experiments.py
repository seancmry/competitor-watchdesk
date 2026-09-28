#!/usr/bin/env python3
"""Fake lab run for Watch Desk — offline fixtures only, no Firecrawl.

Runs a seed baseline, an unchanged pass, then a simulated change.
Writes docs HTML + experiment-results.json. Then: python scripts/make_lab_pdf.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
OUT_JSON = DOCS / "experiment-results.json"
DIFF_LATEST = ROOT / "out" / "diff-latest.json"
PY = ROOT / ".venv" / "bin" / "python"


def run_watch(args: list[str]) -> None:
    cmd = [str(PY if PY.exists() else sys.executable), str(ROOT / "watch.py"), *args]
    subprocess.check_call(cmd, cwd=ROOT)


def load_diff() -> dict:
    return json.loads(DIFF_LATEST.read_text())


def plain_change(change: str) -> str:
    return {
        "new": "First look — we saved a baseline.",
        "unchanged": "No material change since the last look.",
        "changed": "Something on the page changed.",
    }.get(change, change)


def write_html(baseline: dict, after: dict, simulated: dict) -> None:
    def cell(value: object) -> str:
        text = "—" if value is None else str(value)
        return text.replace("&", "&amp;").replace("<", "&lt;")

    def rows(report: dict) -> str:
        bits = []
        for item in report.get("results") or []:
            cls = {
                "changed": "changed",
                "new": "new",
                "unchanged": "ok",
            }.get(item["change"], "ok")
            label = {
                "changed": "Changed",
                "new": "New",
                "unchanged": "Unchanged",
            }.get(item["change"], item["change"])
            bits.append(
                "<tr>"
                f"<td>{cell(item['name'])}</td>"
                f"<td>{cell(item.get('url', '').replace('https://', ''))}</td>"
                f"<td class='{cls}'>{cell(label)}</td>"
                f"<td>{cell(item.get('summary'))}</td>"
                "</tr>"
            )
        return "".join(bits)

    changed = sum(1 for r in simulated.get("results") or [] if r["change"] == "changed")
    unchanged = sum(1 for r in simulated.get("results") or [] if r["change"] == "unchanged")
    style = """
    @font-face { font-family: Geist; src: url("fonts/Geist-Regular.woff2") format("woff2"); font-weight: 400; }
    @font-face { font-family: Geist; src: url("fonts/Geist-SemiBold.woff2") format("woff2"); font-weight: 600; }
    body { font-family: Geist, sans-serif; margin: 28px auto; max-width: 980px; color: #111; background: #fff; }
    h1 { font-weight: 600; font-size: 28px; margin-bottom: 4px; color: #111; }
    h2 { font-weight: 600; font-size: 20px; margin-top: 28px; color: #0a5f8a; }
    p { line-height: 1.45; }
    table { width: 100%; border-collapse: collapse; background: #fff; }
    th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid #e6e6e6; font-size: 14px; }
    th { background: #0a5f8a; color: white; font-weight: 600; }
    .changed { color: #b85a00; font-weight: 600; }
    .new { color: #0a5f8a; font-weight: 600; }
    .ok { color: #067a3a; font-weight: 600; }
    .tiles { display: flex; gap: 16px; margin: 16px 0 8px; }
    .tile { background: #f0f7fb; padding: 16px 20px; min-width: 140px; border-top: 4px solid #0a5f8a; }
    .tile b { display: block; font-size: 28px; }
"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Watch Desk lab</title>
  <style>{style}</style>
</head>
<body>
  <h1>What changed overnight?</h1>
  <p>We watched three public pages with saved sample content. Nothing here calls the live web. First we saved a baseline. Then we ran again with a simulated careers change.</p>
  <div class="tiles">
    <div class="tile"><b>{changed}</b>changed</div>
    <div class="tile"><b>{unchanged}</b>unchanged</div>
    <div class="tile"><b>{len(simulated.get('results') or [])}</b>watched</div>
  </div>
  <h2 id="catalog">Who we watch</h2>
  <table>
    <thead><tr><th>Name</th><th>Address</th><th>After baseline</th><th>Note</th></tr></thead>
    <tbody>
      {rows(after)}
    </tbody>
  </table>
  <h2 id="results">After the simulated change</h2>
  <table>
    <thead><tr><th>Name</th><th>Address</th><th>Decision</th><th>What we saw</th></tr></thead>
    <tbody>
      {rows(simulated)}
    </tbody>
  </table>
</body>
</html>
"""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "lab.html").write_text(html)
    head = html.split("<body>")[0] + "<body>\n"
    catalog_html = html.split('<h2 id="results">')[0] + "</body></html>\n"
    results_html = head + '<h2 id="results">' + html.split('<h2 id="results">')[1]
    (DOCS / "catalog.html").write_text(catalog_html)
    (DOCS / "results.html").write_text(results_html)

    (DOCS / "overview.html").write_text(
        """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Overview</title>
  <style>
    @font-face { font-family: Geist; src: url("fonts/Geist-Regular.woff2") format("woff2"); font-weight: 400; }
    @font-face { font-family: Geist; src: url("fonts/Geist-SemiBold.woff2") format("woff2"); font-weight: 600; }
    body { font-family: Geist, sans-serif; margin: 24px; background: #fff; color: #111; }
    h1 { font-size: 18px; font-weight: 600; margin: 0 0 16px; }
    .row { display: flex; align-items: stretch; gap: 12px; }
    .card { flex: 1; background: #f0f7fb; border-top: 4px solid #0a5f8a; padding: 14px 16px; }
    .card b { display: block; color: #0a5f8a; font-size: 13px; margin-bottom: 6px; }
    .card p { margin: 0; font-size: 15px; line-height: 1.35; }
    .plus, .arrow { align-self: center; color: #0a5f8a; font-weight: 600; font-size: 22px; }
    .go { flex: 0.9; background: #fff6e9; border-top: 4px solid #b85a00; }
    .go b { color: #b85a00; }
  </style>
</head>
<body>
  <h1>Spot competitor page changes without a tab graveyard</h1>
  <div class="row">
    <div class="card"><b>Pick pages</b><p>Careers, pricing, or changelog links you care about.</p></div>
    <div class="plus">+</div>
    <div class="card"><b>Save a snapshot</b><p>Remember the title, headings, and a short excerpt.</p></div>
    <div class="plus">+</div>
    <div class="card"><b>Look again later</b><p>Compare to yesterday’s copy.</p></div>
    <div class="arrow">→</div>
    <div class="card go"><b>See what changed</b><p>A short list you can act on — or ignore.</p></div>
  </div>
</body>
</html>
"""
    )

    (DOCS / "report.html").write_text(
        f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Watch Desk — a short note</title>
  <style>
    @font-face {{ font-family: Geist; src: url("fonts/Geist-Regular.woff2") format("woff2"); font-weight: 400; }}
    @font-face {{ font-family: Geist; src: url("fonts/Geist-SemiBold.woff2") format("woff2"); font-weight: 600; }}
    @page {{ margin: 14mm 14mm 16mm; }}
    body {{ font-family: Geist, sans-serif; margin: 0 auto; max-width: 860px; color: #111; }}
    h1 {{ font-weight: 600; color: #111; margin: 0 0 8px; font-size: 28px; }}
    h2 {{ font-weight: 600; color: #0a5f8a; margin: 0 0 8px; font-size: 20px; }}
    p, li {{ line-height: 1.45; }}
    code {{ font-family: ui-monospace, monospace; font-size: 0.92em; }}
    .keep {{ break-inside: avoid; page-break-inside: avoid; }}
    .results {{ break-before: page; page-break-before: always; }}
    .notes {{ break-before: page; page-break-before: always; }}
    img {{ width: 100%; border: 1px solid #e6e6e6; }}
  </style>
</head>
<body>
  <h1>What changed overnight?</h1>
  <p>We watched three pages with saved sample content. Nothing here calls the live web. First we saved a baseline. A second look found no change. Then we simulated a careers update so the desk could show a real “changed” row.</p>
  <p>In this run, <b>{changed}</b> page changed and <b>{unchanged}</b> stayed the same. The desk writes a short report you can open, share, or feed to a weekday morning check.</p>
  <section class="keep">
    <img src="images/overview.png" alt="How Watch Desk works">
  </section>
  <section class="keep">
    <img src="images/catalog.png" alt="Who we watch after the baseline">
  </section>
  <section class="keep results">
    <img src="images/results.png" alt="After the simulated change">
  </section>
  <section class="notes">
    <h2>What this is worth</h2>
    <ul>
      <li>You stop opening the same careers and changelog tabs every Monday hoping to notice a difference.</li>
      <li>A change is named in plain language — for example a new role heading — not a wall of HTML.</li>
      <li>Quiet pages stay quiet. Only the ones that moved need your attention.</li>
      <li>The same report can later wake Slack, a sheet, or a spoken brief. The judgment stays here.</li>
    </ul>
    <p>Run the lab again with <code>python experiments.py</code>. For live pages later, put real links in <code>targets.yml</code> and use <code>python watch.py --live</code>.</p>
  </section>
</body>
</html>
"""
    )


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    print("1) Seed baseline…")
    run_watch(["--reset", "--seed"])
    baseline = load_diff()

    print("2) Unchanged pass…")
    run_watch([])
    after = load_diff()

    print("3) Simulated change…")
    run_watch(["--simulate"])
    simulated = load_diff()

    payload = {
        "baseline": baseline,
        "after_baseline": after,
        "after_simulate": simulated,
        "plain": [
            {
                "name": r["name"],
                "change": r["change"],
                "why": plain_change(r["change"]),
                "summary": r.get("summary"),
            }
            for r in simulated.get("results") or []
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    write_html(baseline, after, simulated)

    for item in simulated.get("results") or []:
        print(f"{item['change']:9}  {item['name']}  — {item.get('summary')}")


if __name__ == "__main__":
    main()
