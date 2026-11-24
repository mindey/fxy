#!/usr/bin/env bash
set -euo pipefail

repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo"

python="${PYTHON:-python3}"
pypirc="${PYPIRC:-$HOME/.pypirc}"

if [[ ! -f "$pypirc" ]]; then
    echo "Missing $pypirc; copy scripts/pypirc.example there and add a project-scoped PyPI token." >&2
    exit 2
fi

if grep -q 'REPLACE_WITH_PYPI_TOKEN' "$pypirc"; then
    echo "Refusing to publish: $pypirc still contains the token placeholder." >&2
    exit 2
fi

"$python" -m twine check dist/*
"$python" -m twine upload --config-file "$pypirc" --repository pypi dist/*
