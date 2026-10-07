# Feature Specification: Context Coverage Scorecard

**Feature Branch**: `001-context-scorecard` (spec directory only, no branch created)

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: repository feature brief for the context coverage scorecard. Scoped to MVP 3, the context coverage scorecard (plan § 3 and § 4, step 3). MVP 1, the context-change eval harness, is a separate feature.

## Clarifications

### Session 2026-10-06

- Q: Should the default run grade all four rubric parts with code-based rules, or only the mechanical parts, leaving business meaning and interpretation guidance to the model grader? → A: Code-based rules grade all 4 parts by default, labeled as a heuristic. The model grader is an optional second opinion shown beside them.
- Q: Should each run save its report as a file committed to the repo, or only print it to the terminal? → A: Print to the terminal and also write a Markdown report to `results/`, named for the commit it scored, and commit it.
- Q: When the descriptions have changed since dbt last parsed or built the project, should the scorecard re-run dbt itself first, or stop and tell you to run it? → A: The scorecard refreshes the project's documentation output itself at the start of every run, then grades.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Score every column against the rubric (Priority: P1)

The author runs one command against the sample dbt project and gets a coverage report: for every column in every model, a pass, fail, or not-applicable grade on each of the four rubric parts (business meaning, allowed values, interpretation guidance, default filter), rolled up by model and by rubric part. The report says plainly that the grades come from rule-based heuristics, not human review.

**Why this priority**: the scorecard alone is a complete, shippable deliverable (stop point 1 in the plan). Everything else builds on it.

**Independent Test**: run the command on the baseline commit and confirm that every column appears with four grades and that the two roll-up tables print.

**Acceptance Scenarios**:

1. **Given** the user has written all five sections of `rubric.md`, **When** the author runs the scorecard, **Then** every column in all 5 models receives a grade on each of the 4 parts, and the report shows the pass rate per model and per part.
2. **Given** a column the rubric marks as exempt from a part (for example a primary key and default filters), **When** the scorecard grades it, **Then** that part is graded not applicable and is excluded from that part's pass rate denominator.
3. **Given** any graded column, **When** the author reads its row, **Then** each failing part shows a one-line reason naming the rubric rule it missed.
4. **Given** the same commit, **When** the scorecard runs twice, **Then** both reports are identical.

---

### User Story 2 - Surface documentation drift (Priority: P2)

The report lists columns that are documented but no longer exist in the built model, and columns that exist in the built model but have no documentation. The baseline has 1 stale column (`customers.total_order_amount`) and 7 undocumented columns, including `customers.customer_lifetime_value` and 6 staging columns.

**Why this priority**: an undocumented column is the worst case for an agent, and a coverage number that silently skips it overstates quality. It is also a concrete, real finding to show the reader.

**Independent Test**: run the scorecard on the baseline commit and confirm both known drift columns are reported in the right category.

**Acceptance Scenarios**:

1. **Given** a column that exists in a built model with no description, **When** the scorecard runs, **Then** it is listed as undocumented and counts as failing every applicable part.
2. **Given** a documented column that is absent from the built model, **When** the scorecard runs, **Then** it is listed as stale and excluded from the pass rates.

---

### User Story 3 - Optional model grader for judgment parts (Priority: P3)

The author can opt in to a language-model grader for the parts that need judgment (business meaning, interpretation guidance). Its grades appear in a separate column beside the rule-based grades, each with a short stated reason, so the two can be compared and the rule-based grade stays the default.

**Why this priority**: useful for showing where the heuristic and a judgment disagree, but the scorecard is complete without it, and it needs an API key that may not exist tonight.

**Independent Test**: run with the grader enabled on 3 columns and confirm each gets a model grade and reason without changing the rule-based grade.

**Acceptance Scenarios**:

1. **Given** no grader option is passed, **When** the scorecard runs, **Then** no model is called and no key is needed.
2. **Given** the grader option is passed and no key is configured, **When** the scorecard runs, **Then** it stops before grading with a message naming the missing key.
3. **Given** the grader option is passed with a key, **When** the scorecard runs, **Then** each graded part shows the model grade and reason next to the rule-based grade.

### Edge Cases

- A `YOU WRITE` placeholder is still present in `rubric.md`: the scorecard refuses to run and names each unwritten section, rather than grading against criteria nobody wrote.
- A description is a reference to a shared documentation block: it is graded on the resolved text, never on the reference itself.
- A description is empty or whitespace only: graded as undocumented.
- A column carries a PII flag in its description (`first_name`, `last_name`): the flag does not count toward any rubric part, and the report notes it.
- The project has not been built or parsed since the last description change: the scorecard refreshes the documentation output first, so it never grades stale text. If the refresh fails, the scorecard stops with the refresh error and writes no report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The scorecard MUST grade every column of every model in the sample project, including undocumented columns, on each of the 4 rubric parts as pass, fail, or not applicable.
- **FR-002**: Grades MUST be computed from descriptions as the documentation tool resolves them, including referenced documentation blocks.
- **FR-003**: Each rubric part's rule MUST be traceable to the user-written sentence in `rubric.md` it implements, and the report MUST print that rule in plain language so the user can check it against their own wording.
- **FR-004**: The not-applicable decision MUST follow the user's "Not applicable" section of the rubric and MUST NOT be decided by the scorecard on its own.
- **FR-005**: The report MUST include a pass rate by model, a pass rate by rubric part, and a per-column table with a reason for every fail. Each run MUST print the report to the terminal and write it as a Markdown file in `results/`, named for the commit it scored. The file is committed so README numbers trace to a saved run.
- **FR-006**: The report MUST list stale (documented but missing) and undocumented (present but not described) columns separately.
- **FR-007**: The report MUST state that grades are heuristic.
- **FR-008**: The scorecard MUST be able to emit 3 to 5 graded example columns, chosen to show at least one pass and one fail, for the README.
- **FR-009**: Rule-based grades MUST cover all 4 parts on every run, including the judgment parts (business meaning, interpretation guidance), and those two parts MUST be marked as heuristic in the report. The model grader MUST be off by default, MUST NOT replace rule-based grades, and MUST show a reason for every grade it gives. Published numbers come from the rule-based grades.
- **FR-010**: The scorecard MUST refuse to run while any rubric section is unwritten.
- **FR-011**: Rule-based output MUST be deterministic for a given commit.
- **FR-012**: Every run MUST refresh the project's resolved documentation and built column list before grading, with no separate manual step.

### Key Entities

- **Rubric part**: one of the 4 criteria (business meaning, allowed values, interpretation guidance, default filter), with the user's pass sentence and the rule derived from it.
- **Column grade**: a model, column, rubric part, and outcome (pass, fail, not applicable), with a reason and the grader that produced it (rule or model).
- **Drift finding**: a column that is stale or undocumented, with its model.
- **Coverage report**: the roll-ups by model and by part, the per-column table, the drift findings, the heuristic notice, and the commit it was run against.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One command produces the full report from a fresh checkout in under 10 seconds, with the model grader off.
- **SC-002**: 100% of columns in the 5 sample models appear in the report, including both known drift columns.
- **SC-003**: For any column picked at random, the user can explain its grade on every part, using only the report and `rubric.md`, in under 1 minute (checked during the 5-minute out-loud walkthrough).
- **SC-004**: Two runs on the same commit produce byte-identical rule-based reports.
- **SC-005**: The report names the commit it was computed against, so every published number can be reproduced.
- **SC-006**: A search of the repo for employer names, systems, and employee terms returns nothing.

## Assumptions

- Scope is MVP 3 only. The context-change eval harness (frozen questions, SQL agent, weak against strong docs) is a separate feature.
- The user writes the rubric sentences (plan step 2) before the scorecard is run for real. Claude derives the rules from those sentences, and the user approves each rule.
- "Every column" means every column in the built models, not only the documented ones, so undocumented columns lower the score. Seeds are out of scope because they are raw inputs, not documented models.
- Staging and mart models are scored the same way and reported separately by model.
- The baseline is commit `e68d4c3`. Description rewrites happen after the scorecard ships and are scored against their own commits.
- The model grader, when used, needs an API key in a gitignored environment file. No key is needed for the default run.
- Plan § 5 says the sample is kept out of the repo by submodule or gitignore. That was superseded on 2026-10-06: the sample is now vendored and tracked (commit `e68d4c3`).
