# Variable schema — Competitor Watch Desk

**System map:** `targets.yml` → fetch (fixture | Firecrawl) → compare to `data/snapshots.json` → `out/diff-*.json` + updated snapshots.

## Headline card

| Knob | Plain English |
|------|----------------|
| **`targets.yml`** | Who to watch (careers / pricing / changelog URLs). |
| **`fixtures/pages/`** | Fake page extracts for offline demos. |
| **`fixtures/pages-next/`** | “What changed overnight” set — used with `--simulate`. |
| **`data/snapshots.json`** | Last known good snapshot per target (the memory). |
| **`--seed`** | Take a baseline without calling it a change. |
| **`--simulate`** | Offline demo of a careers page that added “GTM Engineer” (n8n fixture). |
| **`FIRECRAWL_API_KEY`** | Live crawls. Stays in `.env`. |

## Knobs

| Name | Type | Required? | Job | If wrong / missing |
|------|------|-----------|-----|--------------------|
| `targets.yml` | file | yes | List of `{id, name, url, kind}` | Script exits |
| `--seed` | flag | no | Write baseline, mark rows as `new` | First real run after seed diffs against it |
| `--simulate` | flag | no | Read `fixtures/pages-next/` when present | No simulated change |
| `--live` | flag | no | Firecrawl each URL | Needs API key |
| `--reset` | flag | no | Delete snapshots before run | — |
| `FIRECRAWL_API_KEY` | text | only with `--live` | Auth for scrape | Live mode exits |
| `fixtures/pages/<id>.json` | file | offline | Extracted title / headings / excerpt | Missing id → exit |
| `data/snapshots.json` | file | created | Prior fingerprints | Treated as all-new |
| `out/diff-*.json` | file | written | Full run report | — |

## Snapshot / diff fields

| Name | Type | Job |
|------|------|-----|
| `fingerprint` | short hash | Cheap “did anything material change?” |
| `change` | `new` \| `changed` \| `unchanged` | Row status for the Loom table |
| `headings_diff.added` / `.removed` | list | What roles / sections appeared or vanished |
| `summary` | text | One-line brief (also feed for a later ElevenLabs clip) |

## MCP experiments (next)

| MCP | Demo move |
|-----|-----------|
| **Firecrawl** | `--live` against real competitor URLs |
| **Supabase** | Store snapshot history instead of a local JSON file |
| **Sheets** | Weekly “what changed” tab |
| **n8n** | Cron → `python watch.py --json`-style → Slack if `changed_count > 0` |
| **ElevenLabs** | Speak `out/diff-latest.json` summaries (pattern from elevenlabs-sandbox) |
