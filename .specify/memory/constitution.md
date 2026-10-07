<!--
Sync Impact Report
- Version change: unversioned template → 1.0.0
- Principles defined (all new): I. The Rubric Is the Standard, II. Baseline and Diffable History, III. Score What dbt Resolves, IV. Code Scores, the Model Judges, V. Smallest Harness That Works
- Added sections: Evaluation Constraints, Evaluation Workflow, Governance
- Removed sections: none
- Templates: plan-template.md, spec-template.md and tasks-template.md were not modified (they read this file at runtime)
- Deferred TODOs: none. All five principles are inferred from rubric.md, CLAUDE.md and the baseline commit e68d4c3, not from explicit user input. Review them before the first /speckit-specify.
-->

# dbt-context-evals Constitution

## Core Principles

### I. The Rubric Is the Standard

`rubric.md` is the only definition of a passing column description. Every documented column is scored on the four parts it defines (business meaning, allowed values, interpretation guidance, default filter), subject to its "not applicable" carve-out. The pass criteria under each part MUST be authored by the user. Tooling and agents MUST NOT fill a `YOU WRITE` placeholder or invent a criterion the rubric does not state. The reference standard is the `account_status` example from LangChain's post "How LangChain Built an Agent-First Data Stack" (July 27, 2026).

Rationale: an eval whose criteria are written by the thing being evaluated measures nothing.

### II. Baseline and Diffable History

The untouched `jaffle-shop` descriptions are committed as the baseline (commit `e68d4c3`). Every rewrite of a description MUST land as its own commit on top of that baseline, so before and after are recoverable with `git diff`. Scores MUST name the commit they were computed against.

Rationale: the eval's output is a comparison, and a comparison without a fixed "before" cannot be reproduced.

### III. Score What dbt Resolves

Scoring MUST read descriptions as dbt resolves them, from `jaffle-shop/target/manifest.json` after `dbt parse`, not from raw YAML. `{{ doc("...") }}` references resolve through `models/docs.md` and are invisible in the YAML alone. A rewrite is only valid when `dbt build` still passes.

Rationale: the agent consuming this context sees the resolved text, so that is what gets scored.

### IV. Code Scores, the Model Judges

Checks that code can answer deterministically (a column is documented, an `accepted_values` test exists, a value list is present) MUST be done in code. A model is used only for judgment calls the rubric requires, such as whether a sentence states business meaning beyond restating the column name. Each model judgment MUST record which rubric part it scored and why.

Rationale: deterministic checks are cheaper, repeatable, and cannot drift between runs.

### V. Smallest Harness That Works

The harness stays a scorecard over one dbt project. No new services, databases, or frameworks are added unless a specific rubric part cannot be scored without them. Speculative abstractions are out of scope.

Rationale: the project tests description quality, not infrastructure.

## Evaluation Constraints

- Test subject: the vendored `jaffle-shop` dbt project (seeds `raw_customers`, `raw_orders`, `raw_payments`, staging models, marts `customers` and `orders`).
- Stack: `dbt-core` 1.11 with `dbt-duckdb`, run from the root `.venv` inside `jaffle-shop/`.
- Build artifacts (`target/`, `logs/`, `*.duckdb`) are never committed.
- Columns flagged as PII in their descriptions (`first_name`, `last_name`) keep that flag through every rewrite.

## Evaluation Workflow

1. Score the baseline commit and record the result.
2. Rewrite descriptions in one bounded round, then commit it.
3. Run `dbt build` and `dbt parse` and confirm both pass.
4. Re-score against the new commit and compare to the prior score per column and per rubric part.

## Governance

This constitution takes precedence over other workflow guidance in this repo. `CLAUDE.md` holds runtime development guidance and MUST NOT contradict it. Amendments are made through `/speckit-constitution`, recorded in the Sync Impact Report at the top of this file, and versioned by semantic versioning: MAJOR for removing or redefining a principle, MINOR for adding a principle or materially expanding one, PATCH for wording. Every spec and plan MUST be checked against Principles I through V before implementation starts.

**Version**: 1.0.0 | **Ratified**: 2026-10-06 | **Last Amended**: 2026-10-06
