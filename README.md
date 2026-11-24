# fxy

fxy is a small loader for reusable Python import vocabularies.

A vocabulary lives in a GitHub repository as a declarative fxy.py. fxy can
inspect it without importing its dependencies, install the packages it declares,
materialize its imports as a dictionary, or inject them into the current
interactive namespace.

    import fxy

    fxy.describe("mindey/cas")
    fxy.install("mindey/cas")
    fxy.use("mindey/cas")

The interpreter remains ordinary Python. The same vocabulary can be used from
CPython, IPython, Jupyter, QtConsole, a script, or another Python host.

## Profiles

A profile is deliberately small:

    __fxy_profile__ = 1
    __requires__ = [
        "sympy>=1.13",
        "mpmath>=1.3",
    ]

    import sympy as sp
    from sympy import Eq, diff, integrate, solve, symbols
    from mpmath import mp

Schema 1 permits only:

- an optional module docstring;
- __fxy_profile__ = 1;
- optional literal __requires__ = [...];
- absolute import and from ... import ... statements.

The profile file itself cannot contain function calls, definitions, control
flow, or other executable statements. Imported Python packages retain their
normal import-time behavior.

## Four operations

Inspect without importing the declared packages:

    info = fxy.describe("mindey/cas")
    info["requirements"]
    info["bindings"]
    info["sha256"]

Explicitly install the declared requirements into the current interpreter:

    fxy.install("mindey/cas")

Materialize the vocabulary without changing the caller:

    cas = fxy.namespace("mindey/cas")
    cas["solve"](...)

Or inject it into the current namespace:

    fxy.use("mindey/cas")
    solve(...)

install() is the only operation that modifies the Python environment.
namespace() and use() never install packages implicitly.

## Versioning and reproducibility

The profile schema and the vocabulary have separate versioning.

__fxy_profile__ = 1 versions the declarative profile language. Git versions the
vocabulary itself:

    fxy.use("mindey/cas@main")
    fxy.use("mindey/cas@v1")
    fxy.use("mindey/cas@44e0c10f778d8564fa4ff884b5a22ed651f368a5")

Pin a commit when reproducibility matters.

Unpinned branches are cached. Pass refresh=True to describe(), install(),
namespace(), or use() when you intentionally want to refetch one. The cache
defaults to the platform user cache directory and can be overridden with
FXY_CACHE_DIR.

## Installation

The core has no runtime dependencies:

    pip install fxy

Scientific, symbolic, plotting, data, or other packages belong to profiles,
not to fxy itself.

## Design

fxy does one thing:

> transport, validate, and realize import vocabularies.

It does not define scientific environments, own a package registry, provide a
calculator shell, install Jupyter kernels, or wrap numerical libraries.
