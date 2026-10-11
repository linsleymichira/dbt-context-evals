<!--
Sync Impact Report
- Version change: 1.1.0 → 1.2.0 (MINOR: one principle added, two materially expanded)
- Modified principles: II. Baseline and Diffable History (adds the committed doc sets the eval harness compares), V. Smallest Harness That Works (names the three parts of the project and the one approved external service)
- Added principles: VI. Pre-Register the Eval
- Added sections: none. Evaluation Workflow is split into a scorecard workflow and a harness workflow
- Removed sections: none
- Unchanged: I, III, IV. Principle I still limits the rubric to column descriptions. Scoring other kinds of context (semantic models, workspace guides, endorsements) needs its own amendment
- Templates: plan-template.md, spec-template.md and tasks-template.md were not modified (they read this file at runtime)
- Dependent artifacts: specs/001-context-scorecard/plan.md was checked against v1.1.0 and still passes, because Principle VI applies to the harness and not to the scorecard. No edit needed
- Deferred TODOs: the user reviews the wording of II, V and VI before the first harness spec. The suggestion source for the loop is not chosen, so V leaves it to that feature's spec
- Why: the user moved the eval harness onto LangSmith and took the suggestion-to-PR loop into scope on 2026-10-10. Principle V as written at v1.1.0 forbade both, and pre-registration was a plan principle the constitution never stated
- History: v1.0.0 ratified 2026-10-06 with five principles inferred from rubric.md, CLAUDE.md and the baseline commit e68d4c3. v1.0.1 and v1.1.0 set bounded workflow rounds to exactly one description
-->

# dbt-context-evals Constitution

## Core Principles

### I. The Rubric Is the Standard

`rubric.md` is the only definition of a passing column description. Every documented column is scored on the four parts it defines (business meaning, allowed values, interpretation guidance, default filter), subject to its "not applicable" carve-out. The pass criteria under each part MUST be authored by the user. Tooling and agents MUST NOT fill a `YOU WRITE` placeholder or invent a criterion the rubric does not state. The reference standard is the `account_status` example from LangChain's post "How LangChain Built an Agent-First Data Stack" (July 27, 2026).

Rationale: an eval whose criteria are written by the thing being evaluated measures nothing.

### II. Baseline and Diffable History

The untouched `jaffle-shop` descriptions are committed as the baseline (commit `e68d4c3`). Every scorecard rewrite of a description MUST land as its own commit on top of that baseline, so before and after are recoverable with `git diff`. Scores MUST name the commit they were computed against.

The eval harness compares two doc sets: `docs_weak/`, which carries column names only or one-line restatements, and `docs_strong/`, which the user writes to the rubric. Each doc set MUST be committed whole before any experiment runs against it. Each experiment MUST name the commit of the doc set and of the question set it ran against. The baseline commit is never rewritten.

Rationale: the eval's output is a comparison, and a comparison without a fixed "before" cannot be reproduced.

### III. Score What dbt Resolves

Scoring MUST read descriptions as dbt resolves them, from `jaffle-shop/target/manifest.json` after `dbt parse`, not from raw YAML. `{{ doc("...") }}` references resolve through `models/docs.md` and are invisible in the YAML alone. A rewrite is only valid when `dbt build` still passes.

Rationale: the agent consuming this context sees the resolved text, so that is what gets scored.

### IV. Code Scores, the Model Judges

Checks that code can answer deterministically (a column is documented, an `accepted_values` test exists, a value list is present) MUST be done in code. A model is used only for judgment calls the rubric requires, such as whether a sentence states business meaning beyond restating the column name. Each model judgment MUST record which rubric part it scored and why.

Rationale: deterministic checks are cheaper, repeatable, and cannot drift between runs.

### V. Smallest Harness That Works

The project has three parts over one dbt project, and no more: the context coverage scorecard, the context-change eval harness, and the suggestion-to-PR loop. Each part gets its own spec.

- The scorecard MUST run with no service, database or framework beyond dbt and the standard library.
- The eval harness MAY use LangSmith for datasets and experiments. LangSmith is the only approved external service for experiments. A local run that needs no LangSmith account MUST be kept as the fallback and MUST produce the same pass or fail per question.
- The suggestion-to-PR loop MAY read context suggestions from one external source, named in its spec, or from a committed mock. Every change it proposes MUST arrive as a pull request with a human reviewer and MUST carry the eval result for that change. The loop never merges its own work.

No other service, database or framework is added unless a spec names the requirement that cannot be met without it. Speculative abstractions are out of scope.

Rationale: the project tests context quality, not infrastructure. Each added service is one more thing a reader has to trust before trusting the number.

### VI. Pre-Register the Eval

The eval questions and their golden SQL MUST be committed before `docs_strong/` exists in the repo. The README MUST cite that commit hash. After the freeze, a question or its golden SQL MUST NOT be edited to change a result. A correction to a wrong golden query is allowed only as its own commit, and the README MUST list it. Questions that depend on the documentation and control questions that do not MUST be reported separately.

Rationale: questions written after the strong docs can be fitted to them. A reader who suspects that has no reason to believe the gain.

## Evaluation Constraints

- Test subject: the vendored `jaffle-shop` dbt project (seeds `raw_customers`, `raw_orders`, `raw_payments`, staging models, marts `customers` and `orders`).
- Stack: `dbt-core` 1.11 with `dbt-duckdb`, run from the root `.venv` inside `jaffle-shop/`.
- Build artifacts (`target/`, `logs/`, `*.duckdb`) are never committed.
- Columns flagged as PII in their descriptions (`first_name`, `last_name`) keep that flag through every rewrite.

## Evaluation Workflow

### Scorecard

1. Score the baseline commit and record the result.
2. Rewrite exactly one description in one bounded round, then commit that rewrite.
3. Run `dbt build` and `dbt parse` and confirm both pass.
4. Re-score against the new commit and compare to the prior score per column and per rubric part.

### Eval harness

1. Commit the questions and golden SQL. Record the hash (Principle VI).
2. Commit `docs_weak/`, then `docs_strong/`.
3. Run the same frozen questions against each doc set as one experiment per set.
4. Score each answer in code, by matching its result set against the golden SQL result (Principle IV). No model grades an answer.
5. Report the pass rate for each doc set, with documentation questions and control questions shown separately.

## Governance

This constitution takes precedence over other workflow guidance in this repo. `CLAUDE.md` holds runtime development guidance and MUST NOT contradict it. Amendments are made through `/speckit-constitution`, recorded in the Sync Impact Report at the top of this file, and versioned by semantic versioning: MAJOR for removing or redefining a principle, MINOR for adding a principle or materially expanding one, PATCH for wording. Every spec and plan MUST be checked against Principles I through VI before implementation starts.

**Version**: 1.2.0 | **Ratified**: 2026-10-06 | **Last Amended**: 2026-10-10
