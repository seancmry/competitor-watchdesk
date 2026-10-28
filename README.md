# Watch desk

It watches the pages listed in `targets.yml`, saves a snapshot, and compares the next look to that snapshot. The snapshot is the title, the headings, and a short excerpt. An unchanged page stays quiet. A material change is written into a short report: what was added, what was removed, and one line on what moved.

A saved sample stands in for the live web, so you can run it with no account. The sample targets are n8n Careers, Linear Changelog, and Personio Careers.

Someone who tracks a few competitor careers, pricing, or changelog pages uses this instead of opening the same tabs every week.

![Spot competitor page changes without opening the same tabs](docs/images/overview.png)

## Run it

**Offline lab:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python experiments.py
```

It takes a baseline, checks again (nothing changed), then runs a simulated careers change.

![Who we watch after the baseline](docs/images/catalog.png)

![After the simulated change](docs/images/results.png)

Lab PDF: [docs/watchdesk-lab.pdf](docs/watchdesk-lab.pdf).

**The same three steps on their own:**

```bash
python watch.py --reset --seed
python watch.py
python watch.py --simulate
```

`--seed` writes the baseline and does not call it a change. `--simulate` pretends the n8n careers page added a role.

### Live crawl

Edit `targets.yml`, put `FIRECRAWL_API_KEY` in `.env`, then:

```bash
python watch.py --reset --seed --live
python watch.py --live
```

### Rebuild the lab screenshots and PDF

```bash
pip install playwright
playwright install chromium
python scripts/make_lab_pdf.py
```

## Inputs

| Input | What the watch does with it |
| --- | --- |
| `targets.yml` | The pages: id, name, url, and kind (careers, pricing, changelog). |
| `fixtures/pages/` | Saved extracts for the offline run. |
| `fixtures/pages-next/` | The "next morning" extracts used by `--simulate`. |
| `data/snapshots.json` | Last snapshot per target. The first run treats every page as new. |
| `--live` | Fetch with Firecrawl. Needs `FIRECRAWL_API_KEY`. |
| `out/diff-*.json` | The report for that run. |

Each row is `new`, `changed`, or `unchanged`. Details are in `VARIABLE_SCHEMA.md`.
