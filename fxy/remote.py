"""GitHub-hosted declarative fxy profiles."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, MutableMapping, Optional, Tuple
from urllib.request import Request, urlopen


_SOURCE_RE = re.compile(
    r"^(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)"
    r"(?:@(?P<ref>[A-Za-z0-9_./-]+))?$"
)


class RemoteProfileError(RuntimeError):
    pass


class InvalidRemoteProfile(RemoteProfileError):
    pass


class InstallApprovalRequired(RemoteProfileError):
    pass


class ProfileDependencyError(RemoteProfileError, ImportError):
    pass


@dataclass(frozen=True)
class Source:
    owner: str
    repo: str
    ref: str = "HEAD"

    @property
    def spec(self) -> str:
        return f"{self.owner}/{self.repo}" + (
            "" if self.ref == "HEAD" else f"@{self.ref}"
        )

    @property
    def url(self) -> str:
        return (
            "https://raw.githubusercontent.com/"
            f"{self.owner}/{self.repo}/{self.ref}/fxy.py"
        )


@dataclass(frozen=True)
class RemoteProfile:
    source: Source
    requirements: Tuple[str, ...]
    imports: Tuple[ast.stmt, ...]
    sha256: str
    cache_path: Path


def is_source(value: str) -> bool:
    return _SOURCE_RE.fullmatch(value) is not None


def parse_source(value: str) -> Source:
    match = _SOURCE_RE.fullmatch(value)
    if not match:
        raise ValueError("expected GitHub source owner/repo[@ref]")
    owner = match.group("owner")
    repo = match.group("repo")
    ref = match.group("ref") or "HEAD"
    if owner in {".", ".."} or repo in {".", ".."}:
        raise ValueError("invalid GitHub owner/repository")
    if any(part in {".", ".."} for part in ref.split("/")):
        raise ValueError("invalid Git ref")
    return Source(owner, repo, ref)


def _cache_path(source: Source, cache_dir: Optional[Path]) -> Path:
    if cache_dir is None:
        root = Path(
            os.environ.get(
                "FXY_CACHE_DIR",
                Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
                / "fxy",
            )
        )
    else:
        root = Path(cache_dir)
    ref = hashlib.sha256(source.ref.encode()).hexdigest()[:16]
    return root / "github" / source.owner / source.repo / ref / "fxy.py"


def _parse(text: str, source: Source, path: Path) -> RemoteProfile:
    tree = ast.parse(text, filename=f"{source.spec}:fxy.py")
    requirements = ()
    schema = None
    imports = []
    body = list(tree.body)

    if body and isinstance(body[0], ast.Expr):
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            body.pop(0)

    for node in body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and node.level:
                raise InvalidRemoteProfile("relative imports are not permitted")
            imports.append(node)
            continue

        if isinstance(node, ast.Assign):
            if (
                len(node.targets) != 1
                or not isinstance(node.targets[0], ast.Name)
                or node.targets[0].id not in {"__fxy_profile__", "__requires__"}
            ):
                raise InvalidRemoteProfile("only fxy metadata assignments are permitted")
            name = node.targets[0].id
            value = ast.literal_eval(node.value)
            if name == "__fxy_profile__":
                if value != 1:
                    raise InvalidRemoteProfile("only profile schema 1 is supported")
                schema = value
            if name == "__requires__":
                if not isinstance(value, (list, tuple)) or not all(
                    isinstance(item, str) and item for item in value
                ):
                    raise InvalidRemoteProfile("__requires__ must be strings")
                requirements = tuple(value)
            continue

        raise InvalidRemoteProfile(
            f"{node.__class__.__name__} is not allowed in a remote profile"
        )

    if schema != 1:
        raise InvalidRemoteProfile("remote profile must declare __fxy_profile__ = 1")

    return RemoteProfile(
        source,
        requirements,
        tuple(imports),
        hashlib.sha256(text.encode()).hexdigest(),
        path,
    )


def fetch(
    value: str,
    *,
    refresh: bool = False,
    cache_dir: Optional[Path] = None,
    timeout: float = 10.0,
) -> RemoteProfile:
    source = parse_source(value)
    path = _cache_path(source, cache_dir)
    if path.exists() and not refresh:
        return _parse(path.read_text(), source, path)

    request = Request(source.url, headers={"User-Agent": "fxy/remote-profile"})
    try:
        with urlopen(request, timeout=timeout) as response:
            text = response.read().decode()
    except OSError:
        if path.exists():
            return _parse(path.read_text(), source, path)
        raise

    profile = _parse(text, source, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)
    return profile


def install(
    value: str,
    *,
    approve: bool = False,
    refresh: bool = False,
    cache_dir: Optional[Path] = None,
) -> Tuple[str, ...]:
    profile = fetch(value, refresh=refresh, cache_dir=cache_dir)
    if not profile.requirements:
        return ()
    if not approve:
        raise InstallApprovalRequired(
            "explicit approval required for: " + ", ".join(profile.requirements)
        )
    subprocess.run(
        [sys.executable, "-m", "pip", "install", *profile.requirements],
        check=True,
    )
    return profile.requirements


def _execute_import(node: ast.stmt, target: MutableMapping[str, Any]) -> None:
    if isinstance(node, ast.Import):
        for item in node.names:
            module = __import__(item.name, fromlist=["*"] if item.asname else [])
            target[item.asname or item.name.split(".", 1)[0]] = (
                module if item.asname else __import__(item.name.split(".", 1)[0])
            )
        return

    assert isinstance(node, ast.ImportFrom)
    module = __import__(node.module, fromlist=["*"])
    if len(node.names) == 1 and node.names[0].name == "*":
        names = getattr(module, "__all__", None)
        if names is None:
            names = [name for name in vars(module) if not name.startswith("_")]
        for name in names:
            target[name] = getattr(module, name)
        return

    for item in node.names:
        target[item.asname or item.name] = getattr(module, item.name)


def namespace(
    value: str,
    *,
    install_missing: bool = False,
    refresh: bool = False,
    cache_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    profile = fetch(value, refresh=refresh, cache_dir=cache_dir)
    if install_missing:
        install(value, approve=True, refresh=False, cache_dir=cache_dir)

    result: Dict[str, Any] = {}
    try:
        for node in profile.imports:
            _execute_import(node, result)
    except (ImportError, AttributeError) as exc:
        requirements = ", ".join(profile.requirements) or "(none declared)"
        raise ProfileDependencyError(
            f"{profile.source.spec} could not realize its imports: {exc}. "
            f"Declared requirements: {requirements}. "
            f"Install explicitly with fxy.install({profile.source.spec!r}, approve=True) "
            "or use install_missing=True."
        ) from exc
    return result


def use(
    value: str,
    target: MutableMapping[str, Any],
    *,
    install_missing: bool = False,
    refresh: bool = False,
    cache_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    values = namespace(
        value,
        install_missing=install_missing,
        refresh=refresh,
        cache_dir=cache_dir,
    )
    target.update(values)
    return values


def describe(
    value: str,
    *,
    refresh: bool = False,
    cache_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    profile = fetch(value, refresh=refresh, cache_dir=cache_dir)
    return {
        "source": profile.source.spec,
        "url": profile.source.url,
        "requirements": profile.requirements,
        "sha256": profile.sha256,
        "cache_path": str(profile.cache_path),
    }
