# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

An eval harness for the quality of dbt column descriptions as context for agents. `rubric.md` defines four parts every documented column is scored on (business meaning, allowed values, interpretation guidance, default filter, plus a "not applicable" carve-out). The target standard is the `account_status` example from LangChain's post "How LangChain Built an Agent-First Data Stack" (July 27, 2026): name the source system, define each value, give a default filter.

The scorecard is `score_context.py` at the repo root. It writes one report per scored commit to `results/`. The eval harness (frozen questions, weak docs against strong docs) does not exist yet.

## Layout

- `rubric.md`: the scoring rubric. The `<!-- YOU WRITE: ... -->` placeholders are the user's to author. Do not fill them in unless asked.
- `jaffle-shop/`: a vendored copy of `dbt-labs/jaffle_shop_duckdb` (upstream history dropped), used as the test-subject dbt project. It is tracked in this repo so description rewrites show up as ordinary diffs. Its own `.gitignore` keeps `target/`, `logs/`, `.user.yml` and the DuckDB file out.
- `.venv/`: root-level virtualenv (Python 3.12) with `dbt-core` 1.11 and `dbt-duckdb`. The jaffle-shop README asks for Python 3.13+, but this venv works.

The column descriptions under evaluation live in `jaffle-shop/models/schema.yml` (marts: `customers`, `orders`) and `jaffle-shop/models/staging/schema.yml`. Some descriptions are `{{ doc("...") }}` references resolved from `jaffle-shop/models/docs.md`. The compiled, resolved descriptions are in `jaffle-shop/target/manifest.json` after `dbt parse`.

## Commands

Run dbt from inside `jaffle-shop/`, because `profiles.yml` sits there and points at a relative `jaffle_shop.duckdb` path.

```shell
cd jaffle-shop
../.venv/bin/dbt build                 # seeds, models, tests
../.venv/bin/dbt build -s stg_orders   # one model plus its tests
../.venv/bin/dbt test -s customers     # tests for one model
../.venv/bin/dbt parse                 # refresh target/manifest.json
../.venv/bin/dbt docs generate
```

`*.duckdb` and `.env` are gitignored at the root.

Python dependencies are declared in the root `pyproject.toml` (a uv project with `package = false`). `uv sync --all-extras` installs dbt 1.11, pytest and the optional `anthropic` extra into `.venv` (worked on 2026-10-07 without the fallback in tasks.md T004).

```shell
uv sync --all-extras
.venv/bin/python score_context.py                   # scorecard: prints and writes results/<sha>.md
.venv/bin/python score_context.py --llm             # model grades to results/<sha>-llm.md, needs ANTHROPIC_API_KEY
.venv/bin/python -m pytest                          # all tests
.venv/bin/python -m pytest tests/test_columns.py -k pii   # one test
ruff check score_context.py tests/ && ruff format score_context.py tests/
```
