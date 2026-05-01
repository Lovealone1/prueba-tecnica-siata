#!/usr/bin/env bash
set -euo pipefail

# ROOT_DIR = root folder of the project
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Smart target resolution
# Converts dots to slashes and tries to find the path in tests/ if it's not already a path.
resolve_target() {
  local target="$1"

  # If it's already a path or a nodeid (contains / or .py or ::), return as is
  if [[ "$target" == *"/"* || "$target" == *".py"* || "$target" == *"::"* ]]; then
    echo "$target"
    return
  fi

  # If it's a module-like string (e.g. v1_0.modules.product)
  # 1. Try to find it as a directory in tests/
  local test_path="tests/${target//./\/}"
  if [[ -d "$test_path" ]]; then
    echo "$test_path"
    return
  fi

  # 2. Try to find it as a file in tests/
  if [[ -f "${test_path}.py" ]]; then
    echo "${test_path}.py"
    return
  fi

  # Fallback to original target (could be a pytest marker or just a file in root)
  echo "$target"
}

if [ $# -eq 0 ]; then
  echo ">> Running all tests in tests/"
  poetry run pytest tests/
else
  TARGET=$(resolve_target "$1")
  shift
  echo ">> Executing: pytest $TARGET $@"
  poetry run pytest "$TARGET" "$@"
fi
