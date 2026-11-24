"""Versioned, inspectable computational namespace profiles.

Profiles are deliberately versioned independently of the fxy package.
A package release may add implementation features without changing a namespace
contract; a profile version changes only when its intended vocabulary changes.

The initial v1 profiles mirror fxy's existing "from fxy.<name> import *"
behaviour. This makes today's implicit namespaces explicit and inspectable,
while leaving room for curated contracts such as "cas/v2" later.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
import inspect
from types import ModuleType
from typing import Any, Dict, MutableMapping, Optional, Tuple, Union

from .dependencies import install_requirements


@dataclass(frozen=True)
class Profile:
    """Metadata describing a reusable computational vocabulary."""

    name: str
    version: int
    module: str
    description: str
    requirements: Tuple[str, ...] = ()

    @property
    def id(self) -> str:
        return f"{self.name}/v{self.version}"


_PROFILES: Dict[str, Profile] = {
    "calc/v1": Profile(
        "calc", 1, "fxy.calc",
        "Legacy CALC vocabulary (mpmath-oriented calculator).",
        ("mpmath>=1.3", "eday"),
    ),
    "cas/v1": Profile(
        "cas", 1, "fxy.cas",
        "Legacy CAS vocabulary (SymPy + mpmath).",
        ("sympy>=1.13", "mpmath>=1.3", "eday"),
    ),
    "lab/v1": Profile(
        "lab", 1, "fxy.lab",
        "Legacy LAB vocabulary (numeric/data/scientific stack).",
        (
            "sympy>=1.13",
            "mpmath>=1.3",
            "eday",
            "numpy",
            "pandas",
            "xarray",
            "scipy",
            "scikit-learn",
            "statsmodels",
        ),
    ),
}

_ALIASES: Dict[str, str] = {
    "calc": "calc/v1",
    "cas": "cas/v1",
    "lab": "lab/v1",
}


def available() -> Tuple[str, ...]:
    """Return all versioned profile identifiers."""

    return tuple(sorted(_PROFILES))


def resolve(name: Union[str, Profile]) -> Profile:
    """Resolve a profile id (or convenience alias) to profile metadata."""

    if isinstance(name, Profile):
        return name

    profile_id = _ALIASES.get(name, name)
    try:
        return _PROFILES[profile_id]
    except KeyError as exc:
        options = ", ".join(available())
        raise KeyError(
            f"unknown fxy profile {name!r}; available: {options}"
        ) from exc



def install(
    profile: Union[str, Profile],
    *,
    approve: bool = False,
) -> Tuple[str, ...]:
    """Install the dependencies declared by a built-in profile."""

    spec = resolve(profile)
    return install_requirements(
        spec.requirements,
        approve=approve,
        source=spec.id,
    )

def _module(profile: Union[str, Profile]) -> ModuleType:
    return import_module(resolve(profile).module)


def names(profile: Union[str, Profile]) -> Tuple[str, ...]:
    """Return names exported by a profile without modifying the caller.

    v1 follows Python's star-import rule: use __all__ when declared, otherwise
    export every module name that does not begin with an underscore.
    """

    module = _module(profile)
    exports = getattr(module, "__all__", None)
    if exports is None:
        exports = (name for name in vars(module) if not name.startswith("_"))
    return tuple(sorted(set(exports)))


def namespace(profile: Union[str, Profile]) -> Dict[str, Any]:
    """Materialize a profile as a new dictionary."""

    module = _module(profile)
    return {name: getattr(module, name) for name in names(profile)}


def use(
    profile: Union[str, Profile],
    target: Optional[MutableMapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Inject a profile into a namespace and return the injected mapping.

    With no explicit target, the caller's global namespace is used. This is
    intended primarily for interactive Python/IPython sessions.

    Library code should normally prefer explicit imports or namespace().
    """

    values = namespace(profile)

    if target is None:
        frame = inspect.currentframe()
        try:
            caller = frame.f_back if frame is not None else None
            if caller is None:
                raise RuntimeError("cannot determine caller namespace")
            target = caller.f_globals
        finally:
            del frame

    target.update(values)
    return values


def diff(
    left: Union[str, Profile],
    right: Union[str, Profile],
) -> Dict[str, Tuple[str, ...]]:
    """Compare the names exported by two profiles."""

    left_names = set(names(left))
    right_names = set(names(right))
    return {
        "added": tuple(sorted(right_names - left_names)),
        "removed": tuple(sorted(left_names - right_names)),
        "common": tuple(sorted(left_names & right_names)),
    }


def describe(profile: Union[str, Profile]) -> Dict[str, Any]:
    """Return profile metadata together with its current exported names."""

    spec = resolve(profile)
    return {
        "id": spec.id,
        "name": spec.name,
        "version": spec.version,
        "module": spec.module,
        "description": spec.description,
        "requirements": spec.requirements,
        "names": names(spec),
    }
