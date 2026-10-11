# Feature Specification: Scorecard Report with Links, a Data File and Table Grades

**Feature Branch**: `002-report-links-tables` (spec directory only, no branch created)

**Created**: 2026-10-10

**Status**: Draft

**Input**: User description: "i want the results markdown file to also follow the new writing standard and i want it to link back to where the column is defined. also, should this be markdown or would it be better as json? also, this should test not just columns but also the table descriptions." The user then approved a plan with a data file beside the Markdown report, and said "for three use the starting point" for the table rubric. This feature changes the scorecard built in [001-context-scorecard](../001-context-scorecard/spec.md). It does not start the eval harness.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Go from a grade to the place the description is written (Priority: P1)

The author, or a reader on GitHub, sees a failing column in the report and opens the exact place where its description is written with one click. A reader who doubts a grade can check the words that were graded without searching the project.

**Why this priority**: a grade the reader cannot check is a grade the reader has to take on trust. The link is also the one field a later tool needs before it can propose a fix.

**Independent Test**: run the scorecard on the sample, open the report on GitHub, click the link on 3 rows (one described column, one column described through a shared documentation block, one undescribed column), and confirm each lands on the right file and line.

**Acceptance Scenarios**:

1. **Given** a column whose description is written in a model's documentation file, **When** the author reads its row, **Then** the row links to that file at the line where the column is declared.
2. **Given** a column whose description is a reference to a shared documentation block (`orders.status` on the baseline), **When** the author reads its row, **Then** the row links to the block that holds the words, not to the reference.
3. **Given** a built column that no documentation file declares (`customers.customer_lifetime_value` on the baseline), **When** the author reads its row, **Then** the row links to the model's query file, because that is the only place the column is defined.
4. **Given** a stale column (`customers.total_order_amount` on the baseline), **When** the author reads the drift section, **Then** the column links to the line that still describes it.
5. **Given** the same commit, **When** the scorecard runs twice or runs on a second machine, **Then** every link is identical, because no link holds a machine-specific path.

---

### User Story 2 - Hand the grades to a tool as data (Priority: P2)

Each run writes a data file beside the Markdown report, from the same grades. A person reads the Markdown. A later tool (the eval harness, the suggestion-to-PR loop, a check in CI) reads the data file and gets each failing item, its reason and its location as separate fields.

**Why this priority**: the project's third part is a loop that drafts a fix for a context gap and attaches a grade. That loop cannot start from a Markdown table. The Markdown report stays, because the first reader of this repo is a person.

**Independent Test**: run the scorecard, load the data file with a standard parser, and confirm that the counts, grades, reasons and locations match the Markdown report for the same commit.

**Acceptance Scenarios**:

1. **Given** a default run on a clean tree, **When** it finishes, **Then** `results/` holds a Markdown report and a data file named for the same commit.
2. **Given** both files from one run, **When** the author compares them, **Then** every pass rate, grade, fail reason, drift finding and location is the same in both.
3. **Given** the same commit, **When** the scorecard runs twice, **Then** both data files are byte-identical.
4. **Given** a run with the model grader on, **When** it finishes, **Then** the model grades go to a separate pair of files, and the pair for the default run is left untouched.
5. **Given** a run that stops early (unwritten rubric, failed refresh, missing key), **When** it exits, **Then** neither file is written.

---

### User Story 3 - Grade table descriptions as well as column descriptions (Priority: P3)

The scorecard grades each model's table description on three table parts: grain (what one row is), source (where the data comes from) and scope (what the table leaves out, or when to use a different table). A model with no table description fails all three and is listed as undocumented. On the baseline, `customers` and `orders` have a table description and the three staging models have none.

**Why this priority**: an agent picks a table before it picks a column, so a table description that does not say what one row is can send every later answer wrong. It ranks third because it needs two things from the user first: a constitution amendment and approved rubric sentences.

**Independent Test**: run the scorecard on the baseline and confirm that 5 models each get 3 table grades, that the 3 staging models are listed as undocumented tables, and that every column pass rate is unchanged from the report at `8eabd21`.

**Acceptance Scenarios**:

1. **Given** the user has approved the three table sentences in `rubric.md`, **When** the scorecard runs, **Then** every model gets a pass or fail on each table part, with a reason for every fail.
2. **Given** a model with no table description, **When** the scorecard runs, **Then** the model fails all three table parts with the reason "no description" and appears in the drift section as an undocumented table.
3. **Given** the baseline commit, **When** the scorecard runs, **Then** the pass rate for each of the 4 column parts is the same as in `results/8eabd21.md`, because table grades are reported in their own rows and never mixed into a column rate.
4. **Given** a table section of `rubric.md` that is unwritten, **When** the scorecard runs, **Then** it refuses to run and names the section, as it does for a column section.
5. **Given** any table row, **When** the author reads it, **Then** it links to where the table description is written, by the rules of User Story 1.

---

### User Story 4 - A report that reads to one writing standard (Priority: P4)

The fixed text the scorecard writes into every report follows the eight writing rules the user borrowed from ASD-STE100 for documentation: one term for one thing, sentences of 25 words at most in a description, and a warning that starts with a command and then gives the reason.

**Why this priority**: the report is the first page a reader opens after the README, and the README was brought to this standard on 2026-10-10. It ranks last because it changes wording, not what the report can do.

**Independent Test**: check every sentence the scorecard writes on its own (not quoted from the rubric or from the sample's descriptions) against the eight rules, and find none that breaks one.

**Acceptance Scenarios**:

1. **Given** the report's notice about heuristic grades, **When** the author reads it, **Then** it uses "rule" for what the scorecard applies and never a second word for the same thing.
2. **Given** a run on a tree with uncommitted changes, **When** the author reads the warning, **Then** it starts with a command and then gives the reason.
3. **Given** a column that fails several parts for the same reason (an undescribed column), **When** the author reads its row, **Then** the reason is stated once for those parts and not repeated for each.
4. **Given** a rubric sentence or a description from the sample, **When** it appears in the report, **Then** it is quoted exactly as written, even if it breaks a rule.

### Edge Cases

- A column is declared in a documentation file with tests and no description text (5 staging columns on the baseline): it stays undocumented, and it links to the line where it is declared, because that is where its description belongs.
- A model has no documentation file at all: its table row and its undeclared columns link to the model's query file.
- The location of a description cannot be found: the row carries no link, the data file records the location as missing, and the run still succeeds. A missing link never changes a grade.
- A description contains a character that would break a table cell: it is escaped in the Markdown and stored unchanged in the data file.
- A table description is whitespace only: the table is undocumented.
- The rule summaries the user approved on 2026-10-09 already meet the writing rules. If a later check finds one that does not, the rewording is shown to the user before it lands.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every column row and every table row in the report MUST link to the place its description is written, or to the place the item is defined when it has no description.
- **FR-002**: A description that comes from a shared documentation block MUST link to that block.
- **FR-003**: Every link MUST be a path relative to the repo, with a line where one is known, and MUST work when the report is opened on GitHub. No output may hold a machine-specific path.
- **FR-004**: Locations are for navigation only. Grades MUST still be computed from the descriptions as the documentation tool resolves them (constitution Principle III).
- **FR-005**: Each successful run MUST write a data file beside the Markdown report, named for the same commit, built from the same grades.
- **FR-006**: The data file MUST hold, as separate fields: the commit, whether the tree was dirty, the rubric sentences and rule summaries, every pass rate, every drift finding, and for each column and table its model, name, description as resolved, location, and each grade with its reason.
- **FR-007**: A default run MUST produce a byte-identical data file for a given commit.
- **FR-008**: A run with the model grader MUST write its own pair of files and MUST NOT change the pair for the default run. The data file for that run MUST hold each model grade and reason beside the rule grade.
- **FR-009**: A run that stops early MUST write neither file.
- **FR-010**: The scorecard MUST grade every model's table description on the table parts defined in `rubric.md`, as pass or fail, with a reason for every fail.
- **FR-011**: The table parts, their pass sentences and any carve-out MUST come from `rubric.md` and MUST be approved by the user, sentence by sentence, before any table grade is published (constitution Principle I). The scorecard MUST refuse to run while a table section is unwritten.
- **FR-012**: A model with no table description MUST fail every table part and MUST be listed in the drift section as an undocumented table.
- **FR-013**: Table grades MUST be reported in their own rows and their own table. The pass rate of each column part and the per-model column rate MUST NOT change because tables are graded.
- **FR-014**: Each table rule MUST print in the report beside the user's sentence, and each rule that matches patterns MUST be marked as heuristic.
- **FR-015**: Every sentence the scorecard writes on its own MUST follow the user's eight borrowed ASD-STE100 rules. Quoted rubric sentences and quoted descriptions are exempt.
- **FR-016**: When several parts of one item fail for the same reason, the report MUST state that reason once.
- **FR-017**: The report at `results/8eabd21.md` MUST stay as it is, as the record of the first format.
- **FR-018**: The README numbers and examples MUST be refreshed from the first report in the new format, and MUST say that table descriptions are graded.

### Key Entities

- **Location**: where an item's description is written or where the item is defined. A repo-relative file and, when known, a line.
- **Table part**: one of the table criteria (grain, source, scope on the starting rubric), with the user's pass sentence and the rule derived from it.
- **Table grade**: a model, a table part and an outcome (pass or fail), with a reason and the grader that produced it.
- **Result**: everything one run found, held once and written twice: as the Markdown report for a person and as the data file for a tool.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the 27 built columns, the 1 stale column and the 5 tables on the baseline carry a link, and 3 links picked by the user open the right file and line on GitHub.
- **SC-002**: The user gets from a failing grade to the words that were graded in one click.
- **SC-003**: The Markdown report and the data file for one commit agree on every count, grade, reason and location, checked by a test and not by eye.
- **SC-004**: Two default runs on the same commit produce byte-identical files, for both the Markdown report and the data file.
- **SC-005**: On the baseline, the pass rates for the 4 column parts are 41%, 53%, 0% and 0%, the same as in `results/8eabd21.md`.
- **SC-006**: On the baseline, 5 models each get 3 table grades, and 3 models are listed as undocumented tables.
- **SC-007**: A check of the scorecard's own sentences against the eight writing rules finds 0 that break one.
- **SC-008**: One command still produces everything from a fresh checkout in under 10 seconds with the model grader off.
- **SC-009**: A search of the repo for employer names, systems and employee terms still returns only the check's own wording.

## Assumptions

- This feature changes the scorecard, the first of the project's three parts. The eval harness and the suggestion-to-PR loop are separate features and are not started here.
- **Table grading needs a constitution amendment first.** Principle I at v1.2.0 defines the rubric as the standard for a column description, and the Sync Impact Report says that scoring another kind of context needs its own amendment. User Story 3 is blocked until the user amends Principle I through `/speckit-constitution`. User Stories 1, 2 and 4 do not depend on it.
- The three table parts are the starting rubric the user accepted on 2026-10-10 ("for three use the starting point"): grain, source and scope. Claude drafted one sentence per part and the user approved all three as written on 2026-10-10 ("sentences ok"). Grain: "A table description passes when it says what one row is." Source: "A table description passes when it says where the data comes from." Scope: "A table description passes when it says what the table leaves out, or when to use a different table." They go into `rubric.md` when User Story 3 is built, after the amendment.
- No table part is skipped for any kind of model on the starting rubric. A carve-out for staging models, if the user wants one, is the user's to write.
- "Where the column is defined" means where its description is written. When there is no description, it means where the column is declared, and failing that the model's query file.
- The data file is JSON. The user asked whether the report should be Markdown or JSON and approved keeping both.
- Seeds and sources stay out of scope, as in feature 001. The other four context types named in the source post (workspace guides, the semantic model, endorsements, the repo as a whole) are out of scope.
- The four approved column rules, their summaries and the not-applicable rule do not change.
- The writing rules are the eight in the user's own rule file, which the user wrote from memory of ASD-STE100 and marked for a later check against Issue 9. The report is held to those eight, not to the full standard.
