# Research: Scorecard Report with Links, a Data File and Table Grades

## R1. How to find the line of a description (FR-001, FR-003)

- **Decision**: parse each documentation file with PyYAML's `yaml.compose`, which keeps a line mark on every node, and walk `models → name → columns → name`. The line recorded is the line of the column's `name` key, or of the model's `name` key for a table.
- **Rationale**: the manifest names the file (`patch_path`) and not the line. PyYAML is a hard dependency of `dbt-core`, so it is already in `.venv` and Principle V ("nothing beyond dbt and the standard library") holds. Measured 2026-10-10: `import yaml` works in `.venv` with no new install.
- **Alternatives considered**: a line scan with regular expressions (two models can declare the same column name, and indentation rules make it fragile). `ruamel.yaml` (a new dependency). dbt's own parser objects (not a stable interface).

## R2. Where a row links, by case (FR-001, FR-002)

|Case|Links to|Baseline example|
|---|---|---|
|Column declared in a documentation file, with or without description text|That file, at the column's `name` line|`customers.first_order`, `stg_orders.status`|
|Description that is a shared documentation block|The file that holds the block, at its `{% docs name %}` line|`orders.status` → `models/docs.md`|
|Built column that no documentation file declares|The model's query file, no line|`customers.customer_lifetime_value`|
|Table with a model entry in a documentation file|That file, at the model's `name` line|all 5 models|
|Model with no documentation file|The model's query file, no line|none on the baseline|

- **Decision**: the block case is read from the manifest's own `doc_blocks` list on the column (verified 2026-10-10: `orders.status` carries `doc.jaffle_shop.orders_status`, and `manifest["docs"]` gives its file). The block's line is found with a standard-library text search for `{% docs <name> %}`. A column with exactly one block links to the block. A column with none or several links to its `name` line.
- **Rationale**: the reader wants the words that were graded. For a block, those words are not in the documentation file.

## R3. Link form (FR-003)

- **Decision**: store `path` relative to the repo root and `line` as a number or null. In Markdown, render `[name](../<path>#L<line>)`, relative to `results/`. In JSON, store the two fields and no rendered link.
- **Rationale**: a relative link works on GitHub, in an editor preview and in a fork, and holds no machine-specific text. GitHub understands `#L<n>` on a source file.
- **Alternatives considered**: a full GitHub URL with the commit hash (ties the report to one remote and one owner, and a `-dirty` run would link to a commit that lacks the change).

## R4. One result, written twice (FR-005, FR-006, SC-003)

- **Decision**: add `build_result(...)`, which returns one plain dictionary holding everything the run found. `render_report` keeps its current arguments and gains the new ones, so the existing report tests stay as they are. A test proves the two outputs agree: every grade, reason, rate and location in the JSON appears in the Markdown for the same inputs.
- **Rationale**: the spec's requirement is that the two files cannot disagree. A test on agreement meets it without rewriting a renderer that 30 tests already cover.
- **Alternatives considered**: render the Markdown from the dictionary alone. Cleaner, and it would change the signature under every report test for no change in behavior. Noted as the right shape if the renderer is ever rewritten.

## R5. JSON determinism and shape (FR-007)

- **Decision**: `json.dumps(result, indent=2, ensure_ascii=False)` plus a final newline. Lists are sorted by model then name. Keys are written in a fixed order by construction. Rates are stored as `passed` and `applicable` integers, with `rate` as a whole-number percent or null when nothing applies.
- **Rationale**: integers cannot differ between machines. A top-level `schema_version` of 1 lets a later reader detect a change.

## R6. File names (FR-008, FR-009)

- **Decision**: `results/<label>.md` and `results/<label>.json` on a default run. `results/<label>-llm.md` and `results/<label>-llm.json` with `--llm`. Both files are written only after grading succeeds, the JSON first.
- **Rationale**: follows the rule set on 2026-10-10 for the Markdown file (commit `1fe569a`).

## R7. The scorecard's own sentences (FR-015, FR-016)

- **Decision**: three changes, and no others.

|Text|Now|Becomes|
|---|---|---|
|Heuristic notice|"These grades come from rule-based checks and are a heuristic, not a judgment of quality. Business meaning and interpretation guidance are pattern checks and are marked heuristic below."|"These grades come from rules and are a heuristic, not a judgment of quality. The rules for business meaning and interpretation guidance match patterns, and the rubric table marks them as heuristic."|
|Dirty warning|"Warning: the working tree had uncommitted changes, so this report does not match a commit."|"Warning: do not cite this report. The working tree had uncommitted changes, so the grades do not match a commit."|
|Repeated reason|"Business meaning: no description. Allowed values: no description. …"|"Business meaning, Allowed values, Interpretation guidance, Default filter: no description"|

- **Rationale**: measured against the eight rules on 2026-10-10. The notice used "check" and "rule" for one thing. The warning gave a reason and no command. The repeated reason is not a rule breach, and the user asked for it in the plan of 2026-10-10. The fail reasons are fragments in a table cell and break no rule. The five rule summaries the user approved on 2026-10-09 already pass, so they are not touched.

## R8. Table grades (US3, gated)

- **Decision**: three table parts read from three new `rubric.md` sections (`Table grain`, `Table source`, `Table scope`). One rule per part, proposed here and approved by the user in the US3 gate before any test is written, as in T015 of feature 001:

|Part|Candidate rule|Heuristic|
|---|---|---|
|Grain|A grain phrase: one row per, one row for each, each row, one record per|no|
|Source|A source phrase: sourced from, loaded from, built from, comes from, derived from, source system|yes|
|Scope|An exclusion or redirect phrase: excludes, excluding, does not include, only includes, instead, unless, except|yes|

- Table grades get their own rubric rows, their own pass-rate rows and their own table. The column pass rates and the per-model column rate are computed from column grades only (FR-013).
- A model with no table description fails all three with "no description" and joins the drift section as an undocumented table.
- **Rationale**: the candidates follow the shape of the approved column rules, a named list of phrases, so the user can check each against their sentence.
- **Open until the gate**: the candidates are a starting point and not a default. Expected baseline result under them: `customers` and `orders` fail all three, and the three staging models fail as undocumented. `[Assumption]` until run.
