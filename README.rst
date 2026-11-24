fxy
===

Reusable computational namespaces for Python.

``fxy`` is a small way to name, share, inspect, and reuse the imports that make a
Python session feel like a particular mathematical or scientific language.

Instead of repeating setup cells across notebooks::

    import sympy as sp
    from sympy import symbols, Eq, solve, diff, integrate
    from mpmath import mp

a profile can make that vocabulary explicit::

    import fxy
    fxy.use("mindey/cas")

The interpreter stays ordinary Python.  The same profile can be used from
CPython, IPython, Jupyter, QtConsole, scripts, or another Python host.

Quick start
-----------

Install the small core::

    pip install fxy

Then use a built-in profile::

    import fxy

    fxy.available()
    # ('calc/v1', 'cas/v1', 'lab/v1')

    fxy.use("cas/v1")

Unversioned built-in names are aliases for their current profile::

    fxy.use("cas")          # currently cas/v1

A profile can also be published independently on GitHub::

    fxy.use("mindey/cas")
    fxy.use("mindey/cas@main")
    fxy.use("mindey/cas@44e0c10f778d8564fa4ff884b5a22ed651f368a5")

The last form pins an immutable Git commit and is preferable when a notebook must
be reproducible.

What a profile is
-----------------

A profile is a computational vocabulary: a set of imports plus optional
dependency declarations.

Built-in profiles are registered by ``fxy`` itself.  GitHub-hosted profiles use
a declarative ``fxy.py`` at the repository root, for example::

    __fxy_profile__ = 1
    __requires__ = [
        "sympy>=1.13",
        "mpmath>=1.3",
    ]

    import sympy as sp
    from sympy import symbols, Eq, solve, diff, integrate
    from mpmath import mp

The profile file is parsed, not executed.  Schema version 1 permits import
statements and literal ``fxy`` metadata; arbitrary statements such as function
calls are rejected.  Imported Python packages retain their normal import-time
behavior.

This keeps two decisions separate:

1. **Which names should exist in this computational vocabulary?**
2. **Which packages may be installed into this Python environment?**

Dependency installation
-----------------------

Installing a profile's declared dependencies is always explicit::

    fxy.install("mindey/cas", approve=True)

For an interactive session, this is the equivalent one-step form::

    fxy.use("mindey/cas", install_missing=True)

Without approval, a missing dependency raises an error showing what the profile
declared rather than silently modifying the environment.

Profiles are cached under the user's cache directory.  Pass ``refresh=True`` to
``use()``, ``namespace()``, or ``describe()`` when you intentionally want to
refetch an unpinned branch or tag.

Inspecting profiles
-------------------

Profiles are inspectable without changing the current namespace::

    fxy.names("cas/v1")
    fxy.describe("cas/v1")
    fxy.diff("cas/v1", "lab/v1")

To materialize a profile as a dictionary instead of injecting it::

    ns = fxy.namespace("mindey/cas")
    ns["solve"](...)

Built-in profiles
-----------------

``calc/v1``
    The historical lightweight calculator vocabulary, centered on ``mpmath`` and
    ``eday``.

``cas/v1``
    The historical symbolic vocabulary, centered on SymPy and ``mpmath``.

``lab/v1``
    The historical numeric/data/scientific vocabulary.

The ``v1`` profiles intentionally preserve the legacy import-selection semantics.
Because the historical modules conditionally import optional dependencies, the
exact names realized by a ``v1`` profile can still depend on what is installed.

Future profile versions can be curated and dependency-declared without silently
changing notebooks that explicitly requested ``v1``.

Installing built-in capabilities
--------------------------------

The default installation stays small::

    pip install fxy

Optional built-in stacks are available as extras::

    pip install 'fxy[cas]'
    pip install 'fxy[lab]'
    pip install 'fxy[plot]'
    pip install 'fxy[ipython]'
    pip install 'fxy[qt]'
    pip install 'fxy[all]'

A GitHub-hosted profile does not need its own PyPI package merely to define a
vocabulary.  Its repository can declare the packages it needs.

Publishing a profile
--------------------

For a simple public profile:

1. Create a public GitHub repository, for example ``alice/cas``.
2. Put a schema-1 ``fxy.py`` at its root.
3. Use it as ``fxy.use("alice/cas")``.
4. Pin a tag or commit when reproducibility matters.

This deliberately follows the familiar ``owner/repo[@ref]`` convention used by
many plugin ecosystems.  A future registry can therefore remain a thin discovery
layer mapping short names to Git sources rather than becoming a second package
repository.

Why profiles instead of predefined environments?
-------------------------------------------------

A predefined Jupyter kernel, shell environment, or QtConsole profile couples a
vocabulary to one execution surface.

``fxy`` instead makes the vocabulary reusable.  A notebook and a terminal REPL
can share the same profile while keeping their own interpreter, kernel,
environment manager, and user interface.

That separation is the main design direction of ``fxy`` 0.8+.

Legacy compatibility
--------------------

The older interfaces remain available for compatibility::

    from fxy.calc import *
    from fxy.cas import *
    from fxy.lab import *
    from fxy.plot import *

and the historical ``fxy`` launcher options (including the CAS/LAB and QtConsole
presets) continue to work.

For new notebooks and reusable code, these environment-style star imports and
launcher presets are **deprecated as the primary interface**.  Prefer
``fxy.use(...)`` or ``fxy.namespace(...)`` so the vocabulary is named,
inspectable, shareable, and optionally version-pinned.

There is no removal date for the legacy interfaces in the 0.x series; they are
kept as compatibility surfaces and may receive maintenance fixes.

Command-line calculator
-----------------------

The small calculator command remains useful independently of the profile API::

    fxy
    python -m fxy "pi**2"

Use ``fxy -i`` if the IPython extra is installed and you want the interactive
IPython frontend.

Links
-----

- Source: https://github.com/mindey/fxy
- PyPI: https://pypi.org/project/fxy/
- Example external profile: https://github.com/mindey/cas
