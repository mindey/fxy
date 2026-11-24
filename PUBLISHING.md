# Publishing fxy

The release workflow is intentionally local and explicit for now. The PyPI API token stays outside Git.

## One-time setup

Create a release environment and install the release tools:

    python3 -m venv ~/.local/share/venvs/fxy-release
    ~/.local/share/venvs/fxy-release/bin/python -m pip install --upgrade pip build twine

Create the private PyPI config:

    cp scripts/pypirc.example ~/.pypirc
    chmod 600 ~/.pypirc

Replace REPLACE_WITH_PYPI_TOKEN with a project-scoped token for fxy.

## Build and validate

From the repository root:

    PYTHON=~/.local/share/venvs/fxy-release/bin/python scripts/build-release.sh

The script runs tests, builds both sdist and wheel, validates their metadata, and prints SHA-256 hashes.

## Publish

After the release commit is merged and tagged:

    PYTHON=~/.local/share/venvs/fxy-release/bin/python scripts/publish-pypi.sh

The publish helper refuses to upload while the placeholder remains.

## Future direction

For a shared mutual-mind or self-owned package, prefer PyPI Trusted Publishing from a protected GitHub Actions environment instead of a long-lived API token.
