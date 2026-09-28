#!/usr/bin/env python3
"""Competitor Watch Desk — snapshot URLs, diff what changed.

System map:
  targets.yml
  → fetch each URL (fixture | Firecrawl)
  → compare to data/snapshots.json
  → out/diff-*.json + stdout table
  → update snapshots

Offline by default. Knobs: VARIABLE_SCHEMA.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
TARGETS_PATH = ROOT / "targets.yml"
SNAPSHOTS_PATH = ROOT / "data" / "snapshots.json"
FIXTURE_DIR = ROOT / "fixtures" / "pages"
NEXT_DIR = ROOT / "fixtures" / "pages-next"
OUT_DIR = ROOT / "out"


def load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_targets() -> list[dict]:
    raw = yaml.safe_load(TARGETS_PATH.read_text()) or {}
    targets = list(raw.get("targets") or [])
    if not targets:
        raise SystemExit("targets.yml has no targets")
    return targets


def load_snapshots() -> dict:
    if not SNAPSHOTS_PATH.exists():
        return {}
    return json.loads(SNAPSHOTS_PATH.read_text())


def save_snapshots(store: dict) -> None:
    SNAPSHOTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_PATH.write_text(json.dumps(store, indent=2, ensure_ascii=False) + "\n")


def fingerprint(extracted: dict) -> str:
    blob = json.dumps(
        {
            "title": extracted.get("title"),
            "headings": extracted.get("headings"),
            "body_excerpt": extracted.get("body_excerpt"),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def extract_from_markdown(url: str, title: str, markdown: str) -> dict:
    headings = re.findall(r"^#{1,3}\s+(.+)$", markdown, flags=re.M)
    excerpt = " ".join(markdown.split())[:280]
    return {
        "url": url,
        "title": title or (headings[0] if headings else ""),
        "headings": headings[:12],
        "body_excerpt": excerpt,
    }


def fetch_target(target: dict, *, live: bool, simulate: bool) -> dict:
    tid = target["id"]
    url = target["url"]

    if not live:
        base = NEXT_DIR if simulate and (NEXT_DIR / f"{tid}.json").exists() else FIXTURE_DIR
        path = base / f"{tid}.json"
        if not path.exists():
            raise SystemExit(f"Missing fixture {path.relative_to(ROOT)}")
        data = json.loads(path.read_text())
        return {
            "id": tid,
            "name": target.get("name") or tid,
            "kind": target.get("kind") or "",
            "url": url,
            "title": data.get("title") or "",
            "headings": list(data.get("headings") or []),
            "body_excerpt": data.get("body_excerpt") or "",
            "source": str(base.relative_to(ROOT)),
        }

    key = os.environ.get("FIRECRAWL_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "Live watch needs FIRECRAWL_API_KEY in .env. "
            "Omit --live to use fixtures/pages/."
        )

    import httpx

    resp = httpx.post(
        "https://api.firecrawl.dev/v2/scrape",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
        timeout=90.0,
    )
    resp.raise_for_status()
    body = resp.json()
    payload = body.get("data") or body
    metadata = payload.get("metadata") or {}
    extracted = extract_from_markdown(
        url,
        metadata.get("title") or metadata.get("ogTitle") or "",
        payload.get("markdown") or "",
    )
    return {
        "id": tid,
        "name": target.get("name") or tid,
        "kind": target.get("kind") or "",
        **extracted,
        "source": "firecrawl",
    }


def diff_headings(old: list, new: list) -> dict:
    old_s, new_s = set(old or []), set(new or [])
    return {
        "added": sorted(new_s - old_s),
        "removed": sorted(old_s - new_s),
    }


def compare(prev: dict | None, current: dict) -> dict:
    fp = fingerprint(current)
    if prev is None:
        return {
            "id": current["id"],
            "name": current["name"],
            "url": current["url"],
            "change": "new",
            "fingerprint": fp,
            "summary": "First snapshot — no prior baseline.",
            "headings_diff": {"added": current.get("headings") or [], "removed": []},
        }

    if prev.get("fingerprint") == fp:
        return {
            "id": current["id"],
            "name": current["name"],
            "url": current["url"],
            "change": "unchanged",
            "fingerprint": fp,
            "summary": "No material change.",
            "headings_diff": {"added": [], "removed": []},
        }

    hdiff = diff_headings(prev.get("headings") or [], current.get("headings") or [])
    bits = []
    if hdiff["added"]:
        bits.append("added: " + ", ".join(hdiff["added"]))
    if hdiff["removed"]:
        bits.append("removed: " + ", ".join(hdiff["removed"]))
    if prev.get("title") != current.get("title"):
        bits.append(f"title → {current.get('title')}")
    if not bits:
        bits.append("body excerpt changed")

    return {
        "id": current["id"],
        "name": current["name"],
        "url": current["url"],
        "change": "changed",
        "fingerprint": fp,
        "summary": "; ".join(bits),
        "headings_diff": hdiff,
        "body_excerpt": current.get("body_excerpt"),
    }


def write_report(results: list[dict], *, simulate: bool) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = OUT_DIR / f"diff-{stamp}.json"
    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "simulate": simulate,
        "results": results,
        "changed_count": sum(1 for r in results if r["change"] == "changed"),
        "new_count": sum(1 for r in results if r["change"] == "new"),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    latest = OUT_DIR / "diff-latest.json"
    latest.write_text(path.read_text())
    return path


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Competitor Watch Desk")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Write current fetches as baseline without treating them as changes",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Offline only: use fixtures/pages-next/ where present (shows a careers change)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Fetch with Firecrawl (needs FIRECRAWL_API_KEY)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete data/snapshots.json before running",
    )
    args = parser.parse_args()

    if args.live and args.simulate:
        raise SystemExit("Use either --live or --simulate, not both.")

    if args.reset and SNAPSHOTS_PATH.exists():
        SNAPSHOTS_PATH.unlink()
        print("Cleared data/snapshots.json")

    targets = load_targets()
    snapshots = {} if args.seed or args.reset else load_snapshots()
    results: list[dict] = []
    next_store: dict = dict(snapshots)

    print("Competitor Watch Desk\n")
    for target in targets:
        current = fetch_target(target, live=args.live, simulate=args.simulate)
        prev = snapshots.get(target["id"])
        row = compare(None if args.seed else prev, current)
        results.append(row)

        next_store[target["id"]] = {
            "id": current["id"],
            "url": current["url"],
            "title": current["title"],
            "headings": current["headings"],
            "body_excerpt": current["body_excerpt"],
            "fingerprint": fingerprint(current),
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "source": current.get("source"),
        }

        mark = {"new": "NEW", "changed": "CHG", "unchanged": "OK "}[row["change"]]
        print(f"  [{mark}] {current['name']}  ({current['kind']})")
        print(f"         {row['summary']}")

    save_snapshots(next_store)
    report = write_report(results, simulate=args.simulate)
    print(f"\nSnapshots → {SNAPSHOTS_PATH.relative_to(ROOT)}")
    print(f"Report    → {report.relative_to(ROOT)}")
    if args.seed:
        print("Seeded baseline. Run again (optionally with --simulate) to see diffs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
