"""Pilot run, build step 6: can a model answer the pilot questions from a doc set?

Swaps a doc set's schema.yml into a scratch copy of jaffle-shop, runs
dbt parse, and gives the model the descriptions dbt resolves (Principle III).
Each answer is run on the DuckDB build and compared with the golden SQL.
Local only, no LangSmith. This is a ceiling check, not the harness.

Usage: .venv/bin/python pilot/run_pilot.py [--docs docs_weak]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from score_context import DEFAULT_MODEL, MODEL_ENV_NAME, model_client  # noqa: E402

PROJECT = REPO_ROOT / "jaffle-shop"
DATABASE = PROJECT / "jaffle_shop.duckdb"
QUESTIONS = REPO_ROOT / "pilot" / "questions.yml"
RESULTS = REPO_ROOT / "results"
TABLES = ("customers", "orders")


def short_commit(path):
    """The last commit that touched a path, so the run names its inputs."""
    out = subprocess.run(
        ["git", "log", "-1", "--format=%h", "--", str(path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip() or "uncommitted"


def resolved_docs(docs_dir):
    """Model and column descriptions as dbt resolves them for this doc set."""
    with tempfile.TemporaryDirectory() as scratch:
        copy = Path(scratch) / "jaffle-shop"
        shutil.copytree(
            PROJECT,
            copy,
            ignore=shutil.ignore_patterns("target", "logs", "*.duckdb*"),
        )
        shutil.copy(docs_dir / "schema.yml", copy / "models" / "schema.yml")
        dbt = Path(sys.executable).parent / "dbt"
        subprocess.run(
            [str(dbt), "parse", "--profiles-dir", str(copy)],
            cwd=copy,
            capture_output=True,
            check=True,
        )
        manifest = json.loads((copy / "target" / "manifest.json").read_text())
    docs = {}
    for node in manifest["nodes"].values():
        if node["resource_type"] == "model" and node["name"] in TABLES:
            docs[node["name"]] = {
                "description": node.get("description", ""),
                "columns": {
                    name: col.get("description", "")
                    for name, col in node["columns"].items()
                },
            }
    return docs


def context_text(con, docs):
    """What the model sees: real columns and types, plus any description."""
    lines = []
    for table in TABLES:
        table_docs = docs.get(table, {"description": "", "columns": {}})
        header = f"Table {table}"
        if table_docs["description"]:
            header += f": {table_docs['description']}"
        lines.append(header)
        for name, col_type, *_ in con.sql(f"describe {table}").fetchall():
            line = f"- {name} ({col_type})"
            description = table_docs["columns"].get(name, "")
            if description:
                line += f": {description}"
            lines.append(line)
        lines.append("")
    return "\n".join(lines)


def ask(client, model, context, question):
    prompt = (
        "You write DuckDB SQL against these tables.\n\n"
        f"{context}\n"
        f"Question: {question}\n\n"
        "Reply with one SQL query in a ```sql block and nothing else."
    )
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in response.content if b.type == "text")
    # An unclosed fence still counts: take everything after ```sql.
    match = re.search(r"```sql\s*(.*?)(?:```|$)", text, flags=re.S)
    return (match.group(1) if match else text).strip()


def normalized(rows):
    """Rows as a sorted list, floats rounded, column names ignored."""

    def cell(value):
        return round(value, 2) if isinstance(value, float) else value

    return sorted((tuple(cell(v) for v in row) for row in rows), key=repr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", default="docs_weak")
    args = parser.parse_args()
    docs_dir = REPO_ROOT / args.docs

    questions = yaml.safe_load(QUESTIONS.read_text())["questions"]
    model = os.environ.get(MODEL_ENV_NAME) or DEFAULT_MODEL
    client = model_client()
    con = duckdb.connect(str(DATABASE), read_only=True)
    context = context_text(con, resolved_docs(docs_dir))

    results = []
    for q in questions:
        expected = normalized(con.sql(q["golden_sql"]).fetchall())
        sql = ask(client, model, context, q["question"])
        try:
            actual = normalized(con.sql(sql).fetchall())
            error = None
        except duckdb.Error as exc:
            actual, error = None, str(exc).splitlines()[0]
        results.append(
            {
                "id": q["id"],
                "group": q["group"],
                "question": q["question"],
                "sql": sql,
                "expected": expected,
                "actual": actual,
                "error": error,
                "outcome": "pass" if actual == expected else "fail",
            }
        )

    run = {
        "docs": args.docs,
        "docs_commit": short_commit(docs_dir),
        "questions_commit": short_commit(QUESTIONS),
        "model": model,
        "context": context,
        "results": results,
    }
    name = f"pilot-{args.docs.replace('/', '-')}-{run['docs_commit']}-{run['questions_commit']}"
    (RESULTS / f"{name}.json").write_text(
        json.dumps(run, indent=2, default=str) + "\n"
    )
    for group in ("context", "control"):
        rows = [r for r in results if r["group"] == group]
        passed = sum(r["outcome"] == "pass" for r in rows)
        print(f"{group}: {passed} of {len(rows)} pass")
    for r in results:
        print(f"{r['id']} {r['outcome']}: {r['sql']}")
    print(f"wrote results/{name}.json")


if __name__ == "__main__":
    main()
