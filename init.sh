#!/usr/bin/env sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT_DIR"

echo "==> Working directory: $PWD"

required_files="
README.md
AGENTS.md
CLAUDE.md
claude-progress.md
feature_list.json
clean-state-checklist.md
evaluator-rubric.md
quality-document.md
session-handoff.md
init.sh
init.ps1
"

missing=""
for file in $required_files; do
  if [ ! -f "$file" ]; then
    missing="$missing $file"
  fi
done

if [ -n "$missing" ]; then
  echo "Missing required files:$missing" >&2
  exit 1
fi

grep -qi "TestFlow" README.md
grep -qi "TestFlow" feature_list.json

if command -v python3 >/dev/null 2>&1; then
  python3 -m json.tool feature_list.json >/dev/null
elif command -v python >/dev/null 2>&1; then
  python -m json.tool feature_list.json >/dev/null
else
  echo "==> Python not found; skipping JSON parser validation."
fi

if [ ! -f "pyproject.toml" ] || [ ! -d "src/testflow" ]; then
  echo "==> Implementation scaffold not present yet."
  echo "==> Docs-only baseline passed."
  echo "==> Next product feature: tf-001 - Create installable Python CLI skeleton."
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  echo "Python is required once the implementation scaffold exists." >&2
  exit 1
fi

echo "==> Installing package"
"$PYTHON_BIN" -m pip install -e .

echo "==> Running tests"
"$PYTHON_BIN" -m pytest tests/
