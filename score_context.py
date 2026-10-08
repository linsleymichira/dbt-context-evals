"""Score dbt column descriptions against the four-part rubric in rubric.md.

Usage: .venv/bin/python score_context.py [--llm]

See specs/001-context-scorecard/ for the spec, plan, and CLI contract.
"""

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
PROJECT_DIR = REPO_ROOT / "jaffle-shop"
PACKAGE = "jaffle_shop"
DBT = str(Path(sys.executable).parent / "dbt")

PARTS = (
    "business_meaning",
    "allowed_values",
    "interpretation_guidance",
    "default_filter",
)
RUBRIC_SECTIONS = PARTS + ("not_applicable",)
UNWRITTEN_MARKER = "<!-- YOU WRITE"
PII_TOKEN = re.compile(r"\s*\bPII\.")
KEY_TESTS = frozenset(
    {"unique", "not_null", "relationships", "accepted_values"}
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


@dataclass(frozen=True)
class Column:
    model: str
    name: str
    status: str  # documented, undocumented, or stale
    description: str
    pii: bool
    facts: frozenset
    data_type: str | None


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


def _model_columns(model_id, node, nodes, catalog_nodes):
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
        )


def load_columns(manifest, catalog):
    """Every built or documented column of the project's models, sorted."""
    nodes = manifest["nodes"]
    columns = (
        column
        for model_id, node in nodes.items()
        if node.get("resource_type") == "model"
        and node.get("package_name") == PACKAGE
        for column in _model_columns(
            model_id, node, nodes, catalog.get("nodes", {})
        )
    )
    return tuple(sorted(columns, key=lambda c: (c.model, c.name)))


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
