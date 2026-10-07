---

description: "Task list for the Context Coverage Scorecard"
---

# Tasks: Context Coverage Scorecard

**Input**: Design documents from `/specs/001-context-scorecard/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli.md, quickstart.md

**Tests**: included. The user's standing rule requires TDD (`~/.claude/reference/rules/testing.md`), so every implementation task is preceded by a test task that must fail first. Tests encode why a behavior matters, not only what it does.

**Organization**: tasks are grouped by user story. All code lives in one root script, `score_context.py` (plan.md, Structure Decision), so parallel work happens across test files, not across source files.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **[Story]**: US1, US2 or US3 from spec.md
- **USER GATE**: a task only the user can do. Implementation stops there until it is done.

---

## Phase 1: Setup

**Purpose**: dependencies and folders, so every later step is one command from a fresh clone.

- [ ] T001 Create `pyproject.toml` at the repo root per research.md R9: runtime deps `dbt-core>=1.11,<1.12` and `dbt-duckdb`, dev dep `pytest`, optional extra `llm = ["anthropic"]`, Python `>=3.12`
- [ ] T002 [P] Create `.env.example` with the single line `ANTHROPIC_API_KEY=` and confirm `.env` is already ignored in `.gitignore`
- [ ] T003 [P] Create `results/.gitkeep` so the committed reports folder exists
- [ ] T004 Run `uv sync --all-extras` at the repo root, then confirm `.venv/bin/python -m pytest --version` and `.venv/bin/dbt --version` both print, and that dbt is still 1.11.x. If `uv sync` fails while resolving or downloading dbt (the certificate error from setup), fall back to `uv pip install --python .venv/bin/python -e ".[llm]" pytest` into the existing `.venv`, and record which path worked in `CLAUDE.md`

---

## Phase 2: Foundational (blocks every user story)

**Purpose**: rubric loading, the dbt refresh, column loading and the commit label. Every story reads these.

- [ ] T005 [P] Write `tests/conftest.py` with builders for a minimal fixture manifest dict (2 models, test nodes for `unique`, `not_null`, `relationships`, `accepted_values`), a matching catalog dict, and a `rubric.md` text with all 5 sections filled
- [ ] T006 [P] Write failing tests in `tests/test_rubric.py`: a rubric with any `<!-- YOU WRITE` marker raises the "unwritten" error naming every such section (FR-010), and a filled rubric returns the 4 part sentences plus the Not applicable sentence keyed by part
- [ ] T007 Implement `load_rubric(path)` in `score_context.py` to pass T006
- [ ] T008 [P] Write failing tests in `tests/test_refresh.py` with `subprocess.run` patched: `dbt build` runs before `dbt docs generate`, both with `--project-dir jaffle-shop --profiles-dir jaffle-shop`, and a nonzero exit from either raises the refresh error carrying dbt's output (research.md R1)
- [ ] T009 Implement `refresh_dbt()` in `score_context.py` to pass T008
- [ ] T010 [P] Write failing tests in `tests/test_columns.py`: catalog-only column → `undocumented`, manifest-only → `stale`, whitespace description → `undocumented`, names compared lowercased, `PII.` stripped from text with `pii=True`, facts `primary_key`, `foreign_key`, `accepted_values_test` and data type derived from test nodes and catalog (data-model.md, Column)
- [ ] T011 Implement `load_columns(manifest, catalog)` in `score_context.py` to pass T010, limited to models in the `jaffle_shop` package
- [ ] T012 [P] Write failing tests in `tests/test_commit.py` with git patched: a clean tree gives the short SHA, any uncommitted change to a tracked file outside `results/` gives `<sha>-dirty`, and a change only under `results/` does not (research.md R7)
- [ ] T013 Implement `commit_label()` in `score_context.py` to pass T012

**Checkpoint**: `pytest` passes, and `load_columns` on the real baseline artifacts returns 27 built columns and 1 stale column.

---

## Phase 3: User Story 1 - Score every column against the rubric (P1) 🎯 MVP

**Goal**: one command grades every built column on 4 parts and writes a deterministic report to `results/`.

**Independent Test**: on a clean tree, `.venv/bin/python score_context.py` exits 0, prints the report, writes `results/<sha>.md`, and a second run produces a byte-identical file (quickstart.md scenarios 1, 2, 4).

- [ ] T014 [US1] **USER GATE**: the user writes all 5 sections of `rubric.md` (plan step 2). Claude does not draft them (constitution Principle I)
- [ ] T015 [US1] **USER GATE**: Claude proposes one rule per part plus the Not applicable rule in chat, each as a plain-language summary quoting the user's sentence (research.md R5 candidates are a starting point, not a default). The user approves or edits each. Record the approved summaries as constants in `score_context.py`
- [ ] T016 [P] [US1] Write failing tests in `tests/test_rules.py` from the approved rules only: for each part, at least one description that must pass and one that must fail, with a test name stating the business reason (for example `test_restating_the_column_name_is_not_business_meaning`), plus N/A cases from the approved Not applicable rule (FR-004)
- [ ] T017 [US1] Implement the 4 rule functions and the N/A check in `score_context.py` to pass T016. Each returns outcome plus a one-line reason, and the two judgment parts are flagged heuristic (FR-009)
- [ ] T018 [P] [US1] Write failing tests in `tests/test_report.py`: pass rate by part excludes `n/a` from the denominator, pass rate by model uses applicable grades, every `fail` has a reason, a column whose description carried `PII.` shows the PII flag in the per-column table, the heuristic notice and the rubric table (sentence beside rule summary) are present, rows sort by model then column, the output contains no timestamp or absolute path, and rendering twice gives identical strings (FR-003, FR-005, FR-007, FR-011, SC-004)
- [ ] T019 [P] [US1] Add failing tests to `tests/test_report.py` for example selection: 3 to 5 columns, at least one pass and one fail, same picks on every run (FR-008)
- [ ] T020 [US1] Implement `grade_all()`, `select_examples()` and `render_report()` in `score_context.py` to pass T018 and T019, following the section order in `contracts/cli.md`
- [ ] T021 [US1] Implement `main()` in `score_context.py`: rubric check (exit 2), refresh (exit 3), load, grade, print, write `results/<label>.md`, exit 0, with errors on stderr and no file written on any failure (`contracts/cli.md`)
- [ ] T022 [US1] Run quickstart.md scenarios 1, 2 and 4 against the real project and record the results in chat, then commit `results/<sha>.md`

**Checkpoint**: stop point 1 is reachable. The scorecard alone is a shippable deliverable.

---

## Phase 4: User Story 2 - Surface documentation drift (P2)

**Goal**: the report lists undocumented and stale columns, and undocumented columns count against coverage.

**Independent Test**: on the baseline, the drift section lists 7 undocumented columns (including `customers.customer_lifetime_value`) and 1 stale column (`customers.total_order_amount`), as in quickstart.md scenario 3.

- [ ] T023 [P] [US2] Write failing tests in `tests/test_drift.py`: an undocumented column fails every applicable part with reason "no description", a stale column appears in the stale list and in no pass rate, and the two lists render as separate report sections in that order (FR-006, spec User Story 2)
- [ ] T024 [US2] Extend `grade_all()` and `render_report()` in `score_context.py` to pass T023
- [ ] T025 [US2] Run quickstart.md scenario 3 and confirm the 7 and 1 counts against the real baseline

---

## Phase 5: User Story 3 - Optional model grader (P3)

**Goal**: `--llm` adds a model grade and reason beside the rule grade for the two judgment parts, and never changes a published number.

**Independent Test**: with the key unset, `--llm` exits 4 and writes nothing. With the key set, 3 columns show model grades and the rule grades are unchanged (quickstart.md scenario 6).

- [ ] T026 [P] [US3] Write failing tests in `tests/test_llm.py` with the client patched: no `--llm` means the `anthropic` package is never imported, a missing package or key exits 4 naming which, model grades appear only for `business_meaning` and `interpretation_guidance`, rule grades and pass rates are identical with and without `--llm`, and the model id comes from `SCORECARD_MODEL` with default `claude-sonnet-5-5` (research.md R8)
- [ ] T027 [US3] Implement the `--llm` flag, lazy import, `.env` reading and `grade_with_model()` in `score_context.py` to pass T026, with the prompt carrying the user's rubric sentence and the resolved description
- [ ] T028 [US3] **USER GATE**: with a real key in `.env`, run `--llm` once and read 3 model reasons aloud against the rubric. Skip until Saturday, October 10 if no key exists

---

## Phase 6: Polish

- [ ] T029 [P] Run `ruff check --fix` and `ruff format` on `score_context.py` and `tests/`, then `ruff check` clean
- [ ] T030 [P] Add the scorecard command and `uv sync` to the Commands section of `CLAUDE.md`
- [ ] T031 Draft the README scorecard section in `README.md` with the user (plan step 4): the rubric, the coverage tables from the committed report, the 3 to 5 examples, and the heuristic note. The user edits the wording
- [ ] T032 Run the employer-data check from the vault plan (`grep -riE "jdna|finish line|workday|employee"` over tracked files) and confirm it returns nothing (SC-006)
- [ ] T033 Run all 8 quickstart.md scenarios end to end and report each result, including scenario 8, the user's out-loud walkthrough (SC-003)

---

## Dependencies & Execution Order

- **Setup (T001 to T004)** → **Foundational (T005 to T013)** → user stories.
- **US1** depends on Foundational and on the two USER GATES T014 and T015. Nothing in T016 onward starts before the user approves the rules.
- **US2** depends on US1's `grade_all()` and `render_report()` (T020). Its data comes from Foundational T011.
- **US3** depends on US1 (T021) for the CLI entry point. It is independent of US2.
- **Polish** runs after the stories that ship tonight. T031 needs a committed report from T022.

```text
T001 → T004 → T005..T013 → T014 (user) → T015 (user) → T016..T022 → T023..T025
                                                            └──────→ T026..T028
```

## Parallel Examples

- **Setup**: T002 and T003 together, after T001.
- **Foundational**: write T005, T006, T008, T010 and T012 together (separate test files), then implement T007, T009, T011 and T013 one at a time (same source file).
- **US1**: T016, T018 and T019 together once T015 is approved.
- **US2 and US3**: T023 and T026 together, since they touch different test files.

## Implementation Strategy

1. **Tonight, before stop point 1 (2:00 am)**: Setup and Foundational need no rubric and can run while the user writes `rubric.md`. That is the best use of the wait.
2. **MVP = US1** (through T022). A committed report is a complete deliverable.
3. **Next**: US2 (small, data is already loaded), then Polish T029 to T032.
4. **Saturday, October 10**: US3 if an API key exists, then the eval harness as its own spec.
