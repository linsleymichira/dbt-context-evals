# CLI Contract: `score_context.py`

## Invocation

```shell
.venv/bin/python score_context.py          # rule grades only
.venv/bin/python score_context.py --llm    # adds model grades for the 2 judgment parts
```

Run from the repo root. No other flags in v1.

## Steps, in order

1. Check `rubric.md` for unwritten sections.
2. Refresh: `dbt build`, then `dbt docs generate`, against `jaffle-shop/`.
3. With `--llm`: check that `anthropic` is importable and `ANTHROPIC_API_KEY` is set.
4. Grade, render, print to stdout, write `results/<short-sha>[-dirty].md`.

## Exit codes

|Code|Meaning|Report written|
|---|---|---|
|0|Success|Yes|
|2|`rubric.md` still has a `<!-- YOU WRITE` section, each one named on stderr|No|
|3|`dbt build` or `dbt docs generate` failed, dbt's output passed through|No|
|4|`--llm` set but the package or key is missing, the missing one named on stderr|No|

## Report layout (Markdown, stdout and file identical)

1. Title with the commit, plus a `-dirty` warning line when relevant
2. Heuristic notice
3. Rubric table: part, the user's sentence, rule summary, heuristic yes/no
4. Pass rate by part
5. Pass rate by model
6. Drift: undocumented columns, then stale columns
7. Per-column table: model, column, PII, 4 outcomes, fail reasons (plus model grade and reason columns with `--llm`)
8. Examples: 3 to 5 graded columns for the README

No timestamps or machine-specific paths anywhere in the output.
