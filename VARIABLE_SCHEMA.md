# Inputs

`targets.yml` lists the pages. Each run fetches them, compares the result to `data/snapshots.json`, and writes `out/diff-*.json`.

## Knobs

| Name | Required | What it does |
| --- | --- | --- |
| `targets.yml` | yes | One entry per page: `id`, `name`, `url`, `kind`. The script exits if it is missing. |
| `--seed` | no | Write a baseline. Those rows are `new`, not a change. |
| `--simulate` | no | Read `fixtures/pages-next/` when that file exists for a target. |
| `--live` | no | Fetch each URL with Firecrawl. |
| `--reset` | no | Delete snapshots before the run. |
| `FIRECRAWL_API_KEY` | only with `--live` | Stays in `.env`. Live mode exits without it. |
| `fixtures/pages/<id>.json` | for the offline run | Title, headings, and excerpt. A missing id stops the run. |
| `data/snapshots.json` | created on first run | Prior snapshot. Empty means every page is new. |
| `out/diff-*.json` | written | The report for that run. |

## A row in the report

| Field | Meaning |
| --- | --- |
| `fingerprint` | Short hash of the title, headings, and excerpt. |
| `change` | `new`, `changed`, or `unchanged`. |
| `headings_diff.added` / `.removed` | Headings that appeared or vanished. |
| `summary` | One line on what moved. |
