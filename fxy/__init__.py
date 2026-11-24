"""Reusable import vocabularies for Python."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import inspect
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, MutableMapping, Optional, Tuple
from urllib.request import Request, urlopen


__all__ = (
    "Error",
    "InvalidProfile",
    "MissingDependency",
    "describe",
    "install",
    "namespace",
    "use",
)


_SOURCE_RE = re.compile(
    r"^(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)"
    r"(?:@(?P<ref>[A-Za-z0-9_./-]+))?$"
)


class Error(RuntimeError):
    """Base error raised by fxy."""


class InvalidProfile(Error):
    """Raised when fxy.py is not a valid declarative profile."""


class MissingDependency(Error, ImportError):
    """Raised when a profile cannot realize one of its imports."""


@dataclass(frozen=True)
class _Source:
    owner: str
    repo: str
    ref: str = "HEAD"

    @property
    def spec(self) -> str:
        suffix = "" if self.ref == "HEAD" else "@" + self.ref
        return self.owner + "/" + self.repo + suffix

    @property
    def url(self) -> str:
        return (
            "https://raw.githubusercontent.com/"
            + self.owner
            + "/"
            + self.repo
            + "/"
            + self.ref
            + "/fxy.py"
        )


@dataclass(frozen=True)
class _Profile:
    source: _Source
    requirements: Tuple[str, ...]
    imports: Tuple[ast.stmt, ...]
    sha256: str


def _source(value: str) -> _Source:
    match = _SOURCE_RE.fullmatch(value)
    if match is None:
        raise ValueError("expected GitHub source owner/repo[@ref]")

    owner = match.group("owner")
    repo = match.group("repo")
    ref = match.group("ref") or "HEAD"

    if owner in {".", ".."} or repo in {".", ".."}:
        raise ValueError("invalid GitHub owner/repository")
    if any(part in {".", ".."} for part in ref.split("/")):
        raise ValueError("invalid Git ref")

    return _Source(owner, repo, ref)


def _cache_path(source: _Source) -> Path:
    root = Path(
        os.environ.get(
            "FXY_CACHE_DIR",
            Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
            / "fxy",
        )
    )
    ref_key = hashlib.sha256(source.ref.encode()).hexdigest()[:16]
    return root / "github" / source.owner / source.repo / ref_key / "fxy.py"


def _parse(text: str, source: _Source) -> _Profile:
    try:
        tree = ast.parse(text, filename=source.spec + ":fxy.py")
    except SyntaxError as exc:
        raise InvalidProfile("profile is not valid Python") from exc
    body = list(tree.body)
    schema = None
    requirements = ()
    imports = []
    seen = set()

    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body.pop(0)

    for node in body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.level:
                raise InvalidProfile("relative imports are not permitted")
            imports.append(node)
            continue

        if isinstance(node, ast.Assign):
            if (
                len(node.targets) != 1
                or not isinstance(node.targets[0], ast.Name)
                or node.targets[0].id
                not in {"__fxy_profile__", "__requires__"}
            ):
                raise InvalidProfile(
                    "only fxy metadata assignments and imports are permitted"
                )

            name = node.targets[0].id
            if name in seen:
                raise InvalidProfile("duplicate " + name + " assignment")
            seen.add(name)

            try:
                value = ast.literal_eval(node.value)
            except (ValueError, TypeError, SyntaxError) as exc:
                raise InvalidProfile(name + " must be literal data") from exc

            if name == "__fxy_profile__":
                if value != 1:
                    raise InvalidProfile("only profile schema 1 is supported")
                schema = 1
                continue

            if not isinstance(value, (list, tuple)) or not all(
                isinstance(item, str) and item.strip()
                for item in value
            ):
                raise InvalidProfile("__requires__ must contain non-empty strings")
            if any(item.lstrip().startswith("-") for item in value):
                raise InvalidProfile(
                    "__requires__ entries must be package requirements, not pip options"
                )
            requirements = tuple(value)
            continue

        raise InvalidProfile(
            type(node).__name__ + " is not permitted in a declarative profile"
        )

    if schema != 1:
        raise InvalidProfile("profile must declare __fxy_profile__ = 1")

    return _Profile(
        source=source,
        requirements=requirements,
        imports=tuple(imports),
        sha256=hashlib.sha256(text.encode()).hexdigest(),
    )


def _fetch(value: str, *, refresh: bool = False) -> _Profile:
    source = _source(value)
    path = _cache_path(source)

    if path.exists() and not refresh:
        return _parse(path.read_text(), source)

    request = Request(source.url, headers={"User-Agent": "fxy"})
    try:
        with urlopen(request, timeout=10) as response:
            text = response.read().decode()
    except OSError:
        if path.exists():
            return _parse(path.read_text(), source)
        raise

    profile = _parse(text, source)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(text)
    os.replace(temporary, path)
    return profile


def _bindings(profile: _Profile) -> Tuple[str, ...]:
    names = []
    for node in profile.imports:
        if isinstance(node, ast.Import):
            for item in node.names:
                names.append(item.asname or item.name.split(".", 1)[0])
            continue

        for item in node.names:
            names.append(item.asname or item.name)

    return tuple(dict.fromkeys(names))


def describe(source: str, *, refresh: bool = False) -> Dict[str, Any]:
    """Inspect a profile without importing its declared packages."""

    profile = _fetch(source, refresh=refresh)
    return {
        "source": profile.source.spec,
        "url": profile.source.url,
        "requirements": profile.requirements,
        "bindings": _bindings(profile),
        "sha256": profile.sha256,
    }


def install(source: str, *, refresh: bool = False) -> Tuple[str, ...]:
    """Install a profile's declared requirements into this Python environment."""

    profile = _fetch(source, refresh=refresh)
    if profile.requirements:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                *profile.requirements,
            ],
            check=True,
        )
    return profile.requirements


def namespace(source: str, *, refresh: bool = False) -> Dict[str, Any]:
    """Materialize a profile as a new dictionary."""

    profile = _fetch(source, refresh=refresh)
    module = ast.Module(body=list(profile.imports), type_ignores=[])
    code = compile(module, profile.source.spec + ":fxy.py", "exec")
    values: Dict[str, Any] = {}

    try:
        exec(code, values)
    except ImportError as exc:
        requirements = ", ".join(profile.requirements) or "(none declared)"
        raise MissingDependency(
            profile.source.spec
            + " could not realize its imports: "
            + str(exc)
            + ". Declared requirements: "
            + requirements
            + ". Run fxy.install("
            + repr(profile.source.spec)
            + ")."
        ) from exc

    values.pop("__builtins__", None)
    return values


def use(
    source: str,
    target: Optional[MutableMapping[str, Any]] = None,
    *,
    refresh: bool = False,
) -> Dict[str, Any]:
    """Inject a profile into a namespace and return the injected names."""

    values = namespace(source, refresh=refresh)

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
