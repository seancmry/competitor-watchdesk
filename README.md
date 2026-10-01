# Watch Desk

## The problem

Competitor careers, pricing, and changelog pages matter — but opening the same tabs every Monday does not scale. You either miss a change, or you waste time when nothing moved.

**What this program does:** it watches the pages you pick, saves a snapshot, looks again later, and writes a short report in plain language. Quiet when nothing changed; clear when something did. A saved sample stands in for the live web, so you can try it with no account.

![Spot competitor page changes without a tab graveyard](docs/images/overview.png)

## Who it helps

- GTM / sales / product people who track a few competitor pages  
- Ops folks tired of “tab graveyards” and manual Monday checks  
- Engineers wiring a lightweight watch job before building a bigger system  

## How to run

**Offline lab** (recommended first):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python experiments.py
```

It seeds a baseline, checks again (unchanged), then runs a simulated careers change.

![Who we watch after the baseline](docs/images/catalog.png)

![After the simulated change](docs/images/results.png)

Lab PDF: [docs/watchdesk-lab.pdf](docs/watchdesk-lab.pdf).

**Day-to-day offline:**

```bash
python watch.py --reset --seed
python watch.py
python watch.py --simulate
```

### Optional: live crawl

Edit `targets.yml`, put `FIRECRAWL_API_KEY` in `.env`, then:

```bash
python watch.py --reset --seed --live
python watch.py --live
```

Default sample targets: n8n Careers, Linear Changelog, Personio Careers.

### Rebuild lab screenshots / PDF

```bash
pip install playwright
playwright install chromium
python scripts/make_lab_pdf.py
```

---

## What the words mean

| Word | What it means |
| --- | --- |
| **Target** | One page you care about (careers, pricing, changelog). |
| **Snapshot** | Last title, headings, and short excerpt we saved. |
| **Changed** | Something material moved since the last look. |
| **Unchanged** | No material change — leave it alone. |
| **Simulated change** | Offline demo that pretends a careers page added a role. |

Full field list: `VARIABLE_SCHEMA.md`.
