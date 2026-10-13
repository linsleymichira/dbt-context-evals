"""Score dbt column descriptions against the four-part rubric in rubric.md.

Table descriptions are scored on the rubric's three table parts.

Usage: .venv/bin/python score_context.py [--llm]

See specs/001-context-scorecard/ for the spec, plan, and CLI contract,
and specs/002-report-links-tables/ for the links, the data file and the
table grades.
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent
PROJECT_DIR = REPO_ROOT / "jaffle-shop"
RUBRIC_PATH = REPO_ROOT / "rubric.md"
RESULTS_DIR = REPO_ROOT / "results"
ENV_PATH = REPO_ROOT / ".env"
PACKAGE = "jaffle_shop"
DBT = str(Path(sys.executable).parent / "dbt")

PARTS = (
    "business_meaning",
    "allowed_values",
    "interpretation_guidance",
    "default_filter",
)
TABLE_PARTS = ("table_grain", "table_source", "table_scope")
COLUMN_SECTIONS = PARTS + ("not_applicable",)
RUBRIC_SECTIONS = COLUMN_SECTIONS + TABLE_PARTS
UNWRITTEN_MARKER = "<!-- YOU WRITE"
PII_TOKEN = re.compile(r"\s*\bPII\.")
KEY_TESTS = frozenset(
    {"unique", "not_null", "relationships", "accepted_values"}
)

# Rule summaries the user approved on 2026-10-09 (tasks.md T015). Each one
# is printed beside the user's own sentence from rubric.md (FR-003).
RULE_SUMMARIES = {
    "business_meaning": (
        "The description has at least 2 content words that are not in "
        "the column name and are not filler. A key column must name the "
        "table it joins to."
    ),
    "allowed_values": (
        "A column with an accepted_values test names every tested value "
        "in its description. A numeric or date column has a unit code in "
        "parentheses, a unit word, or an explicit range."
    ),
    "interpretation_guidance": (
        "The description contains a caveat phrase: unless, except, "
        "excluding, does not include, not the same as, even if, only when."
    ),
    "default_filter": (
        "The description has a filter phrase (filter to, exclude, include "
        "only, by default) and an override phrase (unless, except when, "
        "only if)."
    ),
    "not_applicable": (
        "A key column (unique plus not_null tests, or a relationships "
        "test) skips allowed values and default filter. A free-text "
        "column (varchar with no accepted_values test) skips allowed "
        "values."
    ),
    # The three table rules the user approved on 2026-10-13 (spec 002,
    # tasks.md T019).
    "table_grain": (
        "The description contains a grain phrase: one row per, one row "
        "for each, each row, one record per."
    ),
    "table_source": (
        "The description contains a source phrase: sourced from, loaded "
        "from, built from, comes from, derived from, source system."
    ),
    "table_scope": (
        "The description contains an exclusion or redirect phrase: "
        "excludes, excluding, does not include, only includes, instead, "
        "unless, except."
    ),
}
HEURISTIC_PARTS = frozenset(
    {
        "business_meaning",
        "interpretation_guidance",
        "table_grain",
        "table_source",
        "table_scope",
    }
)
API_KEY_NAME = "ANTHROPIC_API_KEY"
MODEL_ENV_NAME = "SCORECARD_MODEL"
DEFAULT_MODEL = "claude-sonnet-5-5"
PART_TITLES = {
    "business_meaning": "Business meaning",
    "allowed_values": "Allowed values",
    "interpretation_guidance": "Interpretation guidance",
    "default_filter": "Default filter",
    "not_applicable": "Not applicable",
    "table_grain": "Table grain",
    "table_source": "Table source",
    "table_scope": "Table scope",
}

STOPWORDS = frozenset(
    "a an and are as at be by can for from has have in is it its of on "
    "one or that the their they to was were which with".split()
)
FILLER = frozenset("this identifier unique id key column field value".split())
MIN_CONTENT_WORDS = 2
UNIT_OR_RANGE = re.compile(
    r"\([A-Z]{2,5}\)"
    r"|%|(?i:\b(?:percent|percentage|dollars|cents|days|hours|minutes"
    r"|seconds)\b)"
    r"|(?i:\b(?:between|at least|at most|greater than|less than|or more"
    r"|or fewer|non-negative|positive|negative|minimum|maximum|up to"
    r"|ranges? from)\b)"
    r"|[<>]=?|\b\d+ to \d+\b"
)
CAVEAT = re.compile(
    r"\b(?:unless|except|excluding|does not include|not the same as"
    r"|even if|only when)\b",
    flags=re.I,
)
FILTER = re.compile(
    r"\b(?:filter to|exclud(?:e|es|ing)|include only|by default)\b",
    flags=re.I,
)
OVERRIDE = re.compile(r"\b(?:unless|except when|only if)\b", flags=re.I)
TABLE_GRAIN = re.compile(
    r"\b(?:one row per|one row for each|each row|one record per)\b",
    flags=re.I,
)
TABLE_SOURCE = re.compile(
    r"\b(?:sourced from|loaded from|built from|comes from|derived from"
    r"|source system)\b",
    flags=re.I,
)
TABLE_SCOPE = re.compile(
    r"\b(?:excludes|excluding|does not include|only includes|instead"
    r"|unless|except)\b",
    flags=re.I,
)


class RubricUnwritten(Exception):
    """rubric.md still has sections the user has not written."""

    def __init__(self, sections):
        self.sections = tuple(sections)
        super().__init__(
            "rubric.md has unwritten sections: " + ", ".join(self.sections)
        )


class RefreshFailed(Exception):
    """dbt build or dbt docs generate exited nonzero."""


class LlmUnavailable(Exception):
    """--llm was passed but the anthropic package or the key is missing."""


@dataclass(frozen=True)
class Location:
    """Where a description is written. For navigation only, never grading."""

    path: str  # relative to the repo root
    line: int | None = None  # None when the location is a whole file


@dataclass(frozen=True)
class Column:
    model: str
    name: str
    status: str  # documented, undocumented, or stale
    description: str
    pii: bool
    facts: frozenset
    data_type: str | None
    accepted_values: tuple = ()
    location: Location | None = None


@dataclass(frozen=True)
class Table:
    model: str
    status: str  # documented or undocumented
    description: str
    location: Location | None = None


@dataclass(frozen=True)
class Grade:
    model: str
    name: str  # the column, or "" for a table grade
    part: str
    outcome: str  # pass, fail, or n/a (a model grade can be unreadable)
    reason: str
    grader: str = "rule"


# --- rubric ---------------------------------------------------------------


def _section_key(heading):
    """'1. Business meaning' -> 'business_meaning'."""
    words = re.sub(r"^\d+\.\s*", "", heading).strip().lower()
    return words.replace(" ", "_")


def load_rubric(path):
    """Return {section key: the user's sentence}, or raise RubricUnwritten.

    A section is unwritten when it is missing, empty, or still holds the
    YOU WRITE placeholder (FR-010).
    """
    text = Path(path).read_text()
    bodies = {
        _section_key(heading): body
        for heading, body in re.findall(
            r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", text, flags=re.M | re.S
        )
    }
    sentences = {
        key: re.sub(r"<!--.*?-->", "", bodies.get(key, ""), flags=re.S).strip()
        for key in RUBRIC_SECTIONS
    }
    unwritten = [
        key
        for key in RUBRIC_SECTIONS
        if UNWRITTEN_MARKER in bodies.get(key, "") or not sentences[key]
    ]
    if unwritten:
        raise RubricUnwritten(unwritten)
    return sentences


# --- dbt refresh ----------------------------------------------------------


def refresh_dbt():
    """Run dbt build, then dbt docs generate, inside the project (FR-012).

    The project's profiles.yml points at a relative DuckDB path, so dbt
    runs with the project as its working directory.
    """
    for step in (["build"], ["docs", "generate"]):
        result = subprocess.run(
            [DBT, *step],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RefreshFailed(
                f"dbt {' '.join(step)} failed:\n"
                f"{result.stdout}\n{result.stderr}"
            )


# --- columns --------------------------------------------------------------


def _accepted_values(nodes, model_id):
    """{column: tuple of values} from accepted_values tests on one model."""
    return {
        node["column_name"].lower(): tuple(
            str(value)
            for value in node["test_metadata"]
            .get("kwargs", {})
            .get("values", ())
        )
        for node in nodes.values()
        if node.get("resource_type") == "test"
        and node.get("attached_node") == model_id
        and node.get("column_name")
        and (node.get("test_metadata") or {}).get("name") == "accepted_values"
    }


def _column_facts(nodes, model_id):
    """{column: set of test names} for dbt tests attached to one model."""
    tests = {}
    for node in nodes.values():
        meta = node.get("test_metadata") or {}
        column = node.get("column_name")
        if (
            node.get("resource_type") == "test"
            and node.get("attached_node") == model_id
            and column
            and meta.get("name") in KEY_TESTS
        ):
            tests.setdefault(column.lower(), set()).add(meta["name"])
    return {
        column: frozenset(
            fact
            for fact, present in (
                ("primary_key", {"unique", "not_null"} <= names),
                ("foreign_key", "relationships" in names),
                ("accepted_values_test", "accepted_values" in names),
            )
            if present
        )
        for column, names in tests.items()
    }


def _mapping_value(node, key):
    """The value node under key in a composed YAML mapping, or None."""
    if not isinstance(node, yaml.MappingNode):
        return None
    for key_node, value_node in node.value:
        if key_node.value == key:
            return value_node
    return None


def _named_entries(sequence):
    """(name, line, entry) for each named entry of a composed YAML list."""
    if not isinstance(sequence, yaml.SequenceNode):
        return
    for entry in sequence.value:
        name = _mapping_value(entry, "name")
        if name is not None:
            yield name.value, name.start_mark.line + 1, entry


def find_column_line(text, model, column):
    """The 1-based line of a column's name under its model, or None.

    Two models often share a column name, so the file is parsed and the
    column is looked up inside the named model only.
    """
    models = _mapping_value(yaml.compose(text), "models")
    for model_name, _, entry in _named_entries(models):
        if model_name != model:
            continue
        columns = _mapping_value(entry, "columns")
        for column_name, line, _ in _named_entries(columns):
            if column_name.lower() == column:
                return line
    return None


def find_model_line(text, model):
    """The 1-based line of a model's name in a schema file, or None."""
    models = _mapping_value(yaml.compose(text), "models")
    for model_name, line, _ in _named_entries(models):
        if model_name == model:
            return line
    return None


def find_block_line(text, name):
    """The 1-based line that opens the docs block called name, or None."""
    opener = re.compile(rf"\{{%-?\s*docs\s+{re.escape(name)}\s*-?%\}}")
    for number, line in enumerate(text.splitlines(), 1):
        if opener.search(line):
            return number
    return None


def _repo_path(project_path):
    return f"{PROJECT_DIR.name}/{project_path}"


def _column_location(node, column, docs, schema_path, read):
    """Where one column's description is written (spec 002, research R2)."""
    entry = node["columns"].get(column)
    if entry is None or not schema_path:
        # Built by the SQL and declared in no schema file.
        sql_path = node.get("original_file_path")
        return Location(_repo_path(sql_path)) if sql_path else None
    blocks = entry.get("doc_blocks") or []
    block = docs.get(blocks[0]) if len(blocks) == 1 else None
    if block and block.get("original_file_path"):
        # The words that were graded live in the block, not in the schema.
        path = block["original_file_path"]
        line = None
        if read:
            try:
                line = find_block_line(read(path), block["name"])
            except OSError:
                # Same rule as the schema file: keep the file, lose the line.
                pass
        return Location(_repo_path(path), line)
    if read:
        try:
            schema_text = read(schema_path)
        except OSError:
            schema_text = ""
        line = find_column_line(schema_text, node["name"], column.lower())
    else:
        line = None
    return Location(_repo_path(schema_path), line)


def _model_columns(model_id, node, nodes, catalog_nodes, docs, read=None):
    schema_path = (node.get("patch_path") or "").partition("://")[2]
    declared = {name.lower(): name for name in node["columns"]}
    documented = {
        name.lower(): col.get("description") or ""
        for name, col in node["columns"].items()
    }
    built = {
        name.lower(): (col.get("type") or "").lower()
        for name, col in catalog_nodes.get(model_id, {})
        .get("columns", {})
        .items()
    }
    facts = _column_facts(nodes, model_id)
    values = _accepted_values(nodes, model_id)
    for name in documented.keys() | built.keys():
        raw = documented.get(name, "")
        description = PII_TOKEN.sub("", raw).strip()
        if name not in built:
            status = "stale"
        elif description:
            status = "documented"
        else:
            status = "undocumented"
        yield Column(
            model=node["name"],
            name=name,
            status=status,
            description=description,
            pii=bool(PII_TOKEN.search(raw)),
            facts=facts.get(name, frozenset()),
            data_type=built.get(name),
            accepted_values=values.get(name, ()),
            location=_column_location(
                node, declared.get(name, name), docs, schema_path, read
            ),
        )


def load_columns(manifest, catalog, read=None):
    """Every built or documented column of the project's models, sorted.

    read takes a project-relative path and returns the file's text. With
    it, each location carries the line where the description is written.
    """
    nodes = manifest["nodes"]
    columns = (
        column
        for model_id, node in nodes.items()
        if node.get("resource_type") == "model"
        and node.get("package_name") == PACKAGE
        for column in _model_columns(
            model_id,
            node,
            nodes,
            catalog.get("nodes", {}),
            manifest.get("docs", {}),
            read,
        )
    )
    return tuple(sorted(columns, key=lambda c: (c.model, c.name)))


# --- tables ---------------------------------------------------------------


def _table_location(node, read):
    """Where a table description is written (spec 002, research R2)."""
    schema_path = (node.get("patch_path") or "").partition("://")[2]
    if not schema_path:
        sql_path = node.get("original_file_path")
        return Location(_repo_path(sql_path)) if sql_path else None
    line = None
    if read:
        try:
            line = find_model_line(read(schema_path), node["name"])
        except OSError:
            # Same rule as a column: keep the file, lose the line.
            pass
    return Location(_repo_path(schema_path), line)


def load_tables(manifest, read=None):
    """One Table per model of the project, sorted by model.

    read is the same reader load_columns takes.
    """
    tables = (
        Table(
            model=node["name"],
            status="documented" if description else "undocumented",
            description=description,
            location=_table_location(node, read),
        )
        for node in manifest["nodes"].values()
        if node.get("resource_type") == "model"
        and node.get("package_name") == PACKAGE
        for description in [(node.get("description") or "").strip()]
    )
    return tuple(sorted(tables, key=lambda t: t.model))


# --- commit label ---------------------------------------------------------


def _git(*args):
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def commit_label():
    """Short HEAD hash, with -dirty if anything outside results/ changed."""
    sha = _git("rev-parse", "--short", "HEAD").strip()
    changed = [
        line[3:]
        for line in _git("status", "--porcelain").splitlines()
        if line.strip()
    ]
    dirty = any(not path.startswith("results/") for path in changed)
    return f"{sha}-dirty" if dirty else sha


# --- rules ----------------------------------------------------------------


def _is_key(column):
    return bool(column.facts & {"primary_key", "foreign_key"})


def _is_categorical(column):
    return "accepted_values_test" in column.facts


def _is_free_text(column):
    return (
        (column.data_type or "").startswith("varchar")
        and not _is_categorical(column)
        and not _is_key(column)
    )


def not_applicable(column, part):
    """The user's Not applicable rule (FR-004)."""
    if _is_key(column):
        return part in ("allowed_values", "default_filter")
    return _is_free_text(column) and part == "allowed_values"


def _stem(word):
    return word[:-1] if len(word) > 3 and word.endswith("s") else word


def _words(text):
    return [_stem(w) for w in re.findall(r"[a-z]+", text.lower())]


def _business_meaning(column, models):
    if _is_key(column):
        named = [
            model
            for model in sorted(models)
            if re.search(rf"\b{re.escape(model)}\b", column.description, re.I)
        ]
        if named:
            return "pass", ""
        return "fail", "key names no table it joins to"
    name_words = set(_words(column.name.replace("_", " ")))
    added = {
        word
        for word in _words(column.description.replace("'s", ""))
        if word not in name_words | STOPWORDS | FILLER
    }
    if len(added) >= MIN_CONTENT_WORDS:
        return "pass", ""
    return "fail", "adds fewer than 2 words to the column name"


def _allowed_values(column, models):
    if _is_categorical(column):
        if not column.accepted_values:
            return "fail", "accepted_values test lists no values to check"
        missing = [
            value
            for value in column.accepted_values
            if not re.search(
                rf"(?<!\w){re.escape(value)}(?!\w)",
                column.description,
                re.I,
            )
        ]
        if missing:
            return "fail", "values not listed: " + ", ".join(missing)
        return "pass", ""
    if UNIT_OR_RANGE.search(column.description):
        return "pass", ""
    return "fail", "no unit or range, only a type"


def _interpretation_guidance(column, models):
    if CAVEAT.search(column.description):
        return "pass", ""
    return "fail", "names no case where the obvious reading is wrong"


def _default_filter(column, models):
    if not FILTER.search(column.description):
        return "fail", "says no default rows to include or exclude"
    if not OVERRIDE.search(column.description):
        return "fail", "gives a default but not when to override it"
    return "pass", ""


RULES = {
    "business_meaning": _business_meaning,
    "allowed_values": _allowed_values,
    "interpretation_guidance": _interpretation_guidance,
    "default_filter": _default_filter,
}


def grade_column(column, models):
    """One rule Grade per rubric part, in PARTS order."""

    def outcome(part):
        if not_applicable(column, part):
            return "n/a", ""
        if column.status == "undocumented":
            return "fail", "no description"
        return RULES[part](column, models)

    return tuple(
        Grade(column.model, column.name, part, *outcome(part))
        for part in PARTS
    )


def grade_all(columns):
    """Grades for every built column. Stale columns are never graded."""
    models = frozenset(column.model for column in columns)
    return tuple(
        grade
        for column in sorted(columns, key=lambda c: (c.model, c.name))
        if column.status != "stale"
        for grade in grade_column(column, models)
    )


TABLE_RULES = {
    "table_grain": (TABLE_GRAIN, "does not say what one row is"),
    "table_source": (TABLE_SOURCE, "does not say where the data comes from"),
    "table_scope": (
        TABLE_SCOPE,
        "does not say what the table leaves out or which table to use",
    ),
}


def grade_table(table):
    """One rule Grade per table part, in TABLE_PARTS order."""

    def outcome(part):
        if table.status == "undocumented":
            return "fail", "no description"
        pattern, reason = TABLE_RULES[part]
        if pattern.search(table.description):
            return "pass", ""
        return "fail", reason

    return tuple(
        Grade(table.model, "", part, *outcome(part)) for part in TABLE_PARTS
    )


def grade_tables(tables):
    """Table grades for every model. No table part is ever skipped."""
    return tuple(
        grade
        for table in sorted(tables, key=lambda t: t.model)
        for grade in grade_table(table)
    )


# --- model grader ---------------------------------------------------------


def _api_key():
    """The key from the environment, else from the gitignored .env."""
    key = os.environ.get(API_KEY_NAME, "").strip()
    if key or not ENV_PATH.exists():
        return key
    for line in ENV_PATH.read_text().splitlines():
        name, _, value = line.partition("=")
        if name.strip() == API_KEY_NAME:
            return value.strip().strip("'\"")
    return ""


def model_client():
    """An Anthropic client, or LlmUnavailable naming what is missing.

    The import lives here so a default run never loads the package
    (research.md R8).
    """
    try:
        import anthropic
    except ImportError:
        raise LlmUnavailable(
            "--llm needs the anthropic package: run uv sync --all-extras"
        ) from None
    key = _api_key()
    if not key:
        raise LlmUnavailable(
            f"--llm needs {API_KEY_NAME} in the environment or in .env"
        )
    return anthropic.Anthropic(api_key=key)


def _model_prompt(sentence, column):
    return (
        "You are grading one dbt column description against one rubric "
        "sentence.\n\n"
        f"Rubric sentence: {' '.join(sentence.split())}\n"
        f"Model: {column.model}\n"
        f"Column: {column.name}\n"
        f"Description: {column.description}\n\n"
        "Reply with only a JSON object: "
        '{"grade": "pass" or "fail", "reason": one sentence}.'
    )


def _model_verdict(text):
    """(outcome, reason) from the model's reply, never a guessed grade."""
    found = re.search(r"\{.*\}", text, flags=re.S)
    try:
        reply = json.loads(found.group()) if found else {}
    except json.JSONDecodeError:
        reply = {}
    grade = str(reply.get("grade", "")).lower()
    reason = " ".join(str(reply.get("reason", "")).split())
    if grade not in ("pass", "fail") or not reason:
        return "unreadable", "model reply was not the expected JSON"
    return grade, reason


def grade_with_model(client, rubric, columns, grades):
    """One model Grade per judgment part of every documented column.

    Rule grades are read only to skip n/a parts. Nothing here feeds a
    pass rate (FR-009).
    """
    model = os.environ.get(MODEL_ENV_NAME) or DEFAULT_MODEL
    by_column = _by_column(grades)

    def verdict(column, part):
        response = client.messages.create(
            model=model,
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": _model_prompt(rubric[part], column),
                }
            ],
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        return _model_verdict(text)

    return tuple(
        Grade(column.model, column.name, part, *verdict(column, part), "model")
        for column in sorted(columns, key=lambda c: (c.model, c.name))
        if column.status == "documented"
        for part in PARTS
        if part in HEURISTIC_PARTS
        and by_column[(column.model, column.name)][part].outcome != "n/a"
    )


# --- report ---------------------------------------------------------------


def _by_column(grades):
    by_column = {}
    for grade in grades:
        by_column.setdefault((grade.model, grade.name), {})[grade.part] = grade
    return by_column


def select_examples(columns, grades):
    """3 to 5 columns for the README, one per distinct grade pattern.

    Patterns with the most passes come first and ties break on model then
    column, so every run picks the same columns (FR-008).
    """
    by_column = _by_column(grades)
    graded = sorted(
        (c for c in columns if (c.model, c.name) in by_column),
        key=lambda c: (c.model, c.name),
    )

    def pattern(column):
        parts = by_column[(column.model, column.name)]
        return tuple(parts[part].outcome for part in PARTS)

    first_of_pattern = {}
    for column in graded:
        first_of_pattern.setdefault(pattern(column), column)
    picks = sorted(
        first_of_pattern.values(),
        key=lambda c: (-pattern(c).count("pass"), c.model, c.name),
    )[:5]
    if not any("fail" in pattern(c) for c in picks):
        failing = [c for c in graded if "fail" in pattern(c)]
        picks = picks[:4] + failing[:1]
    fill = [c for c in graded if c not in picks]
    picks = picks + fill[: max(0, 3 - len(picks))]
    return tuple(picks)


def _table(header, rows):
    lines = [header, ["---"] * len(header), *rows]
    return "\n".join("|" + "|".join(cells) + "|" for cells in lines)


def _counts(grades):
    """(passed, applicable, whole-number percent or None) for some grades."""
    applicable = [g for g in grades if g.outcome != "n/a"]
    passed = sum(g.outcome == "pass" for g in applicable)
    percent = (
        int(f"{100 * passed / len(applicable):.0f}") if applicable else None
    )
    return passed, len(applicable), percent


def _rate(grades):
    passed, applicable, percent = _counts(grades)
    shown = "n/a" if percent is None else f"{percent}%"
    return [str(passed), str(applicable), shown]


def _link(text, column):
    """text as a link to the column's location, relative to results/."""
    where = column.location
    if where is None:
        return text
    anchor = f"#L{where.line}" if where.line else ""
    return f"[{text}](../{where.path}{anchor})"


def _reasons(parts, keys):
    # A reason shared by several parts is written once (spec 002, FR-016).
    failed_parts = {}
    for part in keys:
        if parts[part].outcome == "fail":
            failed_parts.setdefault(parts[part].reason, []).append(
                PART_TITLES[part]
            )
    return ". ".join(
        f"{', '.join(titles)}: {reason}"
        for reason, titles in failed_parts.items()
    )


def _column_row(column, parts):
    return [
        column.model,
        _link(column.name, column),
        "PII" if column.pii else "",
        *(parts[part].outcome for part in PARTS),
        _reasons(parts, PARTS),
    ]


def _table_row(table, parts):
    return [
        _link(table.model, table),
        *(parts[part].outcome for part in TABLE_PARTS),
        _reasons(parts, TABLE_PARTS),
    ]


def _model_cells(parts):
    """The model grade and model reason cells for one column."""
    judged = [part for part in PARTS if part in parts]
    return [
        ". ".join(f"{PART_TITLES[p]}: {parts[p].outcome}" for p in judged),
        ". ".join(
            f"{PART_TITLES[p]}: {parts[p].reason.replace('|', '/')}"
            for p in judged
        ),
    ]


def _name_list(label, columns):
    names = (
        ", ".join(_link(f"`{c.model}.{c.name}`", c) for c in columns) or "none"
    )
    return f"{label} ({len(columns)}): {names}"


def _table_sections(tables, table_grades):
    """The report sections table grades add, keyed by where they go."""
    if tables is None:
        return {"rates": [], "drift": [], "tables": []}
    tables = sorted(tables, key=lambda t: t.model)
    by_table = _by_column(table_grades)
    undocumented = [t for t in tables if t.status == "undocumented"]
    names = ", ".join(_link(f"`{t.model}`", t) for t in undocumented) or "none"
    return {
        "rates": [
            "## Pass rate by table part",
            _table(
                ["Part", "Passed", "Applicable", "Rate"],
                [
                    [
                        PART_TITLES[part],
                        *_rate(g for g in table_grades if g.part == part),
                    ]
                    for part in TABLE_PARTS
                ],
            ),
        ],
        "drift": [f"Undocumented tables ({len(undocumented)}): {names}"],
        "tables": [
            "## Tables",
            _table(
                [
                    "Model",
                    *(PART_TITLES[part] for part in TABLE_PARTS),
                    "Why it failed",
                ],
                [_table_row(t, by_table[(t.model, "")]) for t in tables],
            ),
        ],
    }


def render_report(
    label,
    rubric,
    columns,
    grades,
    model_grades=None,
    tables=None,
    table_grades=(),
):
    """The Markdown report, in the section order of contracts/cli.md.

    model_grades is None on a default run. With --llm it adds two cells
    to each row of the per-column table and changes nothing else. With
    tables, the report gains the table sections of spec 002's contract,
    and no column section changes.
    """
    columns = sorted(columns, key=lambda c: (c.model, c.name))
    rubric_keys = COLUMN_SECTIONS + (() if tables is None else TABLE_PARTS)
    table_sections = _table_sections(tables, table_grades)
    by_column = _by_column(grades)
    by_model_grade = _by_column(model_grades or ())
    graded = [c for c in columns if (c.model, c.name) in by_column]
    column_header = [
        "Model",
        "Column",
        "PII",
        *(PART_TITLES[part] for part in PARTS),
        "Why it failed",
    ]
    sections = [
        f"# Context coverage scorecard at `{label}`",
        *(
            [
                "Warning: do not cite this report. The working tree had "
                "uncommitted changes, so the grades do not match a commit."
            ]
            if label.endswith("-dirty")
            else []
        ),
        "These grades come from rules and are a heuristic, not a "
        "judgment of quality. The rules for business meaning and "
        "interpretation guidance match patterns, and the rubric table "
        "marks them as heuristic.",
        "## Rubric",
        _table(
            ["Part", "Rubric sentence", "Rule", "Heuristic"],
            [
                [
                    PART_TITLES[key],
                    " ".join(rubric[key].split()),
                    RULE_SUMMARIES[key],
                    "yes" if key in HEURISTIC_PARTS else "no",
                ]
                for key in rubric_keys
            ],
        ),
        "## Pass rate by part",
        _table(
            ["Part", "Passed", "Applicable", "Rate"],
            [
                [
                    PART_TITLES[part],
                    *_rate(g for g in grades if g.part == part),
                ]
                for part in PARTS
            ],
        ),
        *table_sections["rates"],
        "## Pass rate by model",
        _table(
            ["Model", "Passed", "Applicable", "Rate"],
            [
                [model, *_rate(g for g in grades if g.model == model)]
                for model in sorted({g.model for g in grades})
            ],
        ),
        "## Drift",
        _name_list(
            "Undocumented", [c for c in columns if c.status == "undocumented"]
        ),
        _name_list("Stale", [c for c in columns if c.status == "stale"]),
        *table_sections["drift"],
        *table_sections["tables"],
        "## Columns",
        _table(
            column_header
            + (
                [] if model_grades is None else ["Model grade", "Model reason"]
            ),
            [
                _column_row(c, by_column[(c.model, c.name)])
                + (
                    []
                    if model_grades is None
                    else _model_cells(
                        by_model_grade.get((c.model, c.name), {})
                    )
                )
                for c in graded
            ],
        ),
        "## Examples",
        _table(
            column_header[:2] + ["Description"] + column_header[3:],
            [
                [
                    *row[:2],
                    " ".join(c.description.replace("|", "/").split())[:120]
                    or "(none)",
                    *row[3:],
                ]
                for c in select_examples(columns, grades)
                for row in [_column_row(c, by_column[(c.model, c.name)])]
            ],
        ),
    ]
    return "\n\n".join(sections) + "\n"


# --- data file ------------------------------------------------------------


def _rate_entry(key, name, grades):
    passed, applicable, percent = _counts(grades)
    return {
        key: name,
        "passed": passed,
        "applicable": applicable,
        "rate": percent,
    }


def _grade_entry(grade, model_grade):
    entry = {"outcome": grade.outcome, "reason": grade.reason}
    if model_grade is not None:
        entry["model_grade"] = {
            "outcome": model_grade.outcome,
            "reason": model_grade.reason,
        }
    return entry


def _qualified(columns, status):
    return [f"{c.model}.{c.name}" for c in columns if c.status == status]


def _location_entry(location):
    if location is None:
        return None
    return {"path": location.path, "line": location.line}


def _with_tables(result, rubric, tables, table_grades):
    """result plus the table fields, in the key order of data-model.md."""
    tables = sorted(tables, key=lambda t: t.model)
    by_table = _by_column(table_grades)
    return {
        **{key: result[key] for key in ("schema_version", "commit", "dirty")},
        "rubric": result["rubric"]
        + [
            {
                "part": key,
                "applies_to": "table",
                "sentence": " ".join(rubric[key].split()),
                "rule": RULE_SUMMARIES[key],
                "heuristic": key in HEURISTIC_PARTS,
            }
            for key in TABLE_PARTS
        ],
        "pass_rates": {
            **result["pass_rates"],
            "table_parts": [
                _rate_entry(
                    "part", part, (g for g in table_grades if g.part == part)
                )
                for part in TABLE_PARTS
            ],
        },
        "drift": {
            **result["drift"],
            "undocumented_tables": [
                t.model for t in tables if t.status == "undocumented"
            ],
        },
        "tables": [
            {
                "model": t.model,
                "status": t.status,
                "description": t.description,
                "location": _location_entry(t.location),
                "grades": {
                    part: _grade_entry(by_table[(t.model, "")][part], None)
                    for part in TABLE_PARTS
                },
            }
            for t in tables
        ],
        "columns": result["columns"],
    }


def build_result(
    label,
    rubric,
    columns,
    grades,
    model_grades=None,
    tables=None,
    table_grades=(),
):
    """Everything one run found, as plain data (spec 002, contracts).

    It takes the same inputs as render_report, so the data file and the
    Markdown report cannot be built from different grades.
    """
    columns = sorted(columns, key=lambda c: (c.model, c.name))
    by_column = _by_column(grades)
    by_model_grade = _by_column(model_grades or ())
    result = {
        "schema_version": 1,
        "commit": label,
        "dirty": label.endswith("-dirty"),
        "rubric": [
            {
                "part": key,
                "applies_to": "column",
                "sentence": " ".join(rubric[key].split()),
                "rule": RULE_SUMMARIES[key],
                "heuristic": key in HEURISTIC_PARTS,
            }
            for key in COLUMN_SECTIONS
        ],
        "pass_rates": {
            "by_part": [
                _rate_entry(
                    "part", part, (g for g in grades if g.part == part)
                )
                for part in PARTS
            ],
            "by_model": [
                _rate_entry(
                    "model", model, (g for g in grades if g.model == model)
                )
                for model in sorted({g.model for g in grades})
            ],
        },
        "drift": {
            "undocumented_columns": _qualified(columns, "undocumented"),
            "stale_columns": _qualified(columns, "stale"),
        },
        "columns": [
            {
                "model": c.model,
                "column": c.name,
                "status": c.status,
                "pii": c.pii,
                "description": c.description,
                "location": _location_entry(c.location),
                "grades": {
                    part: _grade_entry(
                        parts[part],
                        by_model_grade.get((c.model, c.name), {}).get(part),
                    )
                    for parts in [by_column.get((c.model, c.name), {})]
                    for part in PARTS
                    if part in parts
                },
            }
            for c in columns
        ],
    }
    if tables is None:
        return result
    return _with_tables(result, rubric, tables, table_grades)


def render_json(result):
    """The data file's text. Same result, same bytes."""
    return json.dumps(result, indent=2, ensure_ascii=False) + "\n"


# --- entry point ----------------------------------------------------------


def main(argv=None):
    """Rubric check, refresh, grade, print and write (contracts/cli.md)."""
    use_llm = "--llm" in (sys.argv[1:] if argv is None else argv)
    try:
        rubric = load_rubric(RUBRIC_PATH)
    except RubricUnwritten as error:
        print(error, file=sys.stderr)
        return 2
    try:
        refresh_dbt()
    except RefreshFailed as error:
        print(error, file=sys.stderr)
        return 3
    try:
        client = model_client() if use_llm else None
    except LlmUnavailable as error:
        print(error, file=sys.stderr)
        return 4
    target = PROJECT_DIR / "target"
    manifest = json.loads((target / "manifest.json").read_text())

    def read(path):
        return (PROJECT_DIR / path).read_text()

    columns = load_columns(
        manifest,
        json.loads((target / "catalog.json").read_text()),
        read=read,
    )
    tables = load_tables(manifest, read)
    label = commit_label()
    grades = grade_all(columns)
    table_grades = grade_tables(tables)
    model_grades = (
        grade_with_model(client, rubric, columns, grades) if use_llm else None
    )
    report = render_report(
        label, rubric, columns, grades, model_grades, tables, table_grades
    )
    print(report, end="")
    RESULTS_DIR.mkdir(exist_ok=True)
    # Model wording varies between runs, so it never lands in the
    # deterministic pair of files for the commit.
    stem = f"{label}-llm" if use_llm else label
    result = build_result(
        label, rubric, columns, grades, model_grades, tables, table_grades
    )
    (RESULTS_DIR / f"{stem}.json").write_text(render_json(result))
    (RESULTS_DIR / f"{stem}.md").write_text(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
