#!/usr/bin/env sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT_DIR"

echo "==> Working directory: $PWD"

VENV_DIR=".venv"

find_venv_python() {
  if [ -x "$VENV_DIR/bin/python" ]; then
    printf '%s\n' "$VENV_DIR/bin/python"
  elif [ -x "$VENV_DIR/Scripts/python.exe" ]; then
    printf '%s\n' "$VENV_DIR/Scripts/python.exe"
  else
    return 1
  fi
}

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

if ! VENV_PYTHON=$(find_venv_python); then
  if command -v python3 >/dev/null 2>&1; then
    BASE_PYTHON=python3
  elif command -v python >/dev/null 2>&1; then
    BASE_PYTHON=python
  else
    echo "Python 3 is required to create .venv. Install Python, then rerun this script." >&2
    exit 1
  fi

  echo "==> Creating .venv"
  "$BASE_PYTHON" -m venv "$VENV_DIR"
  VENV_PYTHON=$(find_venv_python)
fi

if ! "$VENV_PYTHON" -c "import sys" >/dev/null 2>&1; then
  echo ".venv exists but its Python interpreter is not usable. Install Python 3, remove the broken .venv, then rerun this script." >&2
  exit 1
fi

echo "==> Using virtual environment: $VENV_DIR"
echo "==> Installing dependencies into .venv"
"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt

if [ -f "pyproject.toml" ]; then
  echo "==> Installing package into .venv"
  "$VENV_PYTHON" -m pip install -e .
fi

"$VENV_PYTHON" -m json.tool feature_list.json >/dev/null

if [ -d "tests" ]; then
  echo "==> Running tests in .venv"
  "$VENV_PYTHON" -m pytest tests/
else
  echo "==> No tests directory found."
  echo "==> .venv baseline passed."
fi
