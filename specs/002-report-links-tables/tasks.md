---

description: "Task list for the scorecard report with links, a data file and table grades"
---

# Tasks: Scorecard Report with Links, a Data File and Table Grades

**Input**: Design documents from `/specs/002-report-links-tables/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/report.md, quickstart.md

**Tests**: included. Every implementation task follows a test task that must fail first, as in feature 001.

**Organization**: grouped by user story. All code lives in `score_context.py`, so parallel work happens across test files only.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependency on an incomplete task)
- **USER GATE**: a task only the user can do. Implementation stops there until it is done.

---

## Phase 1: Foundational

- [ ] T001 Add a `located` fixture to `tests/conftest.py`: a documentation file, a shared documentation block and a manifest that names both, written under `tmp_path`, with known line numbers and one column name declared in two models

---

## Phase 2: User Story 1 - Go from a grade to the place the description is written (P1)

**Independent Test**: quickstart.md scenarios 3, 5 and 6.

- [ ] T002 [P] [US1] Write failing tests in `tests/test_locations.py` for each case in research R2: a declared column, the same column name in a second model, a shared block, an undeclared built column, a stale column, a table, a model with no documentation file, and an unreadable file that must not stop the run (FR-001 to FR-004)
- [ ] T003 [US1] Implement `Location`, `find_locations()` and the `location` field on `Column` in `score_context.py` to pass T002, with line marks from PyYAML (research R1)
- [ ] T004 [P] [US1] Add failing tests to `tests/test_locations.py` for the Markdown: the Column cell and the drift lists link to `../<path>#L<line>`, a row with no location shows the plain name, and no output holds an absolute path (FR-003)
- [ ] T005 [US1] Extend `render_report()` and `main()` in `score_context.py` to pass T004

---

## Phase 3: User Story 2 - Hand the grades to a tool as data (P2)

**Independent Test**: quickstart.md scenarios 1 to 4 and 8.

- [ ] T006 [P] [US2] Write failing tests in `tests/test_result.py`: the result holds every field in contracts/report.md, a stale column has no grades, rendering twice gives identical JSON text, and every grade, reason, rate and location in the result appears in the Markdown for the same inputs (FR-005 to FR-007, SC-003)
- [ ] T007 [US2] Implement `build_result()` and `render_json()` in `score_context.py` to pass T006
- [ ] T008 [P] [US2] Add failing tests to `tests/test_result.py` and `tests/test_llm.py`: a default run writes the `.md` and `.json` pair, a `--llm` run writes the `-llm` pair with model grades and leaves the default pair untouched, and an early exit writes neither file (FR-008, FR-009)
- [ ] T009 [US2] Extend `main()` in `score_context.py` to pass T008

---

## Phase 4: User Story 4 - A report that reads to one writing standard (P4)

**Independent Test**: quickstart.md scenario 7.

- [ ] T010 [P] [US4] Write failing tests in `tests/test_wording.py`: the notice never says "check", the dirty warning starts with a command and then gives the reason, no sentence the scorecard writes on its own passes 25 words, and a reason shared by several parts of one row is written once (FR-015, FR-016)
- [ ] T011 [US4] Change the notice, the warning and the reason cell in `score_context.py` to pass T010 (research R7), and update any feature 001 test that asserts the old wording

---

## Phase 5: Polish for the stories built now

- [ ] T012 [P] Run `ruff check --fix` and `ruff format` on `score_context.py` and `tests/`, then `ruff check` clean
- [ ] T013 [P] Update the scorecard lines in `CLAUDE.md` and the file names in `specs/001-context-scorecard/contracts/cli.md` step 4 to name the `.json` file
- [ ] T014 Run quickstart.md scenarios 1 to 4 and 6 to 9 and report each result
- [ ] T015 **USER GATE**: commit the code, then run the scorecard on the clean tree and commit the first `results/<sha>.md` and `results/<sha>.json` pair
- [ ] T016 Refresh `README.md` from that report: the report link, the data file, and one sentence on the links. The user edits the wording (FR-018)
- [ ] T017 **USER GATE**: after the push, run quickstart.md scenario 5 by clicking 3 links on GitHub

---

## Phase 6: User Story 3 - Grade table descriptions (P3, gated)

**Independent Test**: quickstart.md scenario 10.

- [ ] T018 [US3] **USER GATE**: amend constitution Principle I through `/speckit-constitution` so the rubric also defines a passing table description. Nothing below starts before this
- [ ] T019 [US3] **USER GATE**: approve or edit the three candidate table rules in research R8. Record the approved summaries as constants in `score_context.py`
- [ ] T020 [US3] Add the three approved sentences to `rubric.md` as sections `Table grain`, `Table source` and `Table scope`, exactly as approved on 2026-10-10
- [ ] T021 [P] [US3] Write failing tests in `tests/test_tables.py` from the approved rules: one description that passes and one that fails per part, an undocumented table fails all three and joins the drift section, an unwritten table section stops the run, and every column pass rate is unchanged (FR-010 to FR-014)
- [ ] T022 [US3] Implement `load_tables()`, the three rule functions, the table rows in `build_result()` and the table sections in `render_report()` to pass T021
- [ ] T023 [US3] Run quickstart.md scenario 10 on the baseline and confirm 5 tables, 15 grades, 3 undocumented tables and unchanged column rates
- [ ] T024 [US3] Refresh `README.md` to say that table descriptions are graded, with the table pass rates

---

## Dependencies & Execution Order

```text
T001 → T002..T005 → T006..T009 → T010..T011 → T012..T017
                                                  └→ T018 (user) → T019 (user) → T020..T024
```

- US2 depends on US1, because the result holds locations.
- US4 touches the same renderer as US1, so it runs after it.
- US3 depends on US2 for the result shape and on two USER GATES.

## Implementation Strategy

1. Build US1, US2 and US4 in one sitting. Each is shippable on its own.
2. Stop at T015. The commit and the first report in the new format are the user's call.
3. US3 waits for the amendment.
