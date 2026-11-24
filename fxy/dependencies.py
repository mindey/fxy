"""Shared dependency installation policy for fxy profiles."""

import subprocess
import sys
from typing import Iterable, Tuple


class InstallApprovalRequired(RuntimeError):
    """Raised when a profile wants packages installed without explicit approval."""


def install_requirements(
    requirements: Iterable[str],
    *,
    approve: bool = False,
    source: str = "profile",
) -> Tuple[str, ...]:
    """Install a profile's declared requirements into the current interpreter.

    This is the single package-installation boundary used by built-in and remote
    profiles.  The caller must opt in explicitly.
    """

    declared = tuple(requirements)
    if not declared:
        return ()

    if not approve:
        raise InstallApprovalRequired(
            f"explicit approval required for {source}: " + ", ".join(declared)
        )

    subprocess.run(
        [sys.executable, "-m", "pip", "install", *declared],
        check=True,
    )
    return declared
