#!/usr/bin/env bash
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo"

python="${PYTHON:-python3}"

"$python" -m unittest discover -v
rm -rf dist build fxy.egg-info
"$python" -m build
"$python" -m twine check dist/*

echo
echo "Built:"
sha256sum dist/*
