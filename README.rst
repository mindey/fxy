fxy
===
.. |isympy| replace:: ``isympy``

Imports and command ``fxy`` with parameters to import libraries often used in research to emulate CAS software, or LAB software. For more info, check out the `video <https://youtu.be/xkbRmfd86u8>`_.

Introduction
------------

1. People coming from ``R``, love that you can start quickly using it as a CALCulator,
2. People coming from use of CAS tools like ``Maple``, ``Mathematica`` have ``isympy``, that is narrowly focused,
3. People coming from computing LAB languages ``Matlab`` and ``R`` may find that ``Python`` requires quite a few imports just to do equivalent computing in Python.

This package ``fxy`` is a shorthand to do the imports packages to approximate these domains (CALC, CAS, and LAB) you've got a command ``fxy``, that starts Python with needed packages pre-imported: so, you can start using Python like a calculator right away.

Installation
------------

-  ``pip install fxy`` to get the import shortcuts.

Use as a calculator
-------------------
``$ fxy``
(pass, ``-i`` for IPython)

Usage as imports
----------------

- ``from fxy.calc import *`` for quick CALC - basic ``mpmath`` calculator, and ``eday`` for time
- ``from fxy.cas import *`` for basic CAS software ("Symbolic") emulation
- ``from fxy.lab import *`` for LAB software ("Numeric") emulation
- ``from fxy.plot import *`` for plotting imports.

Usage as command
----------------
The package defines the `fxy` command, if you just want Python with something, run:

- ``$ fxy --calc`` starts Python with CALC imports (basic ``mpmath`` calculator)
- ``$ fxy --cas`` (or ``-x``) starts Python with CAS (Computer Algebra System) imports (to emulate Maple, Matematica,..)
- ``$ fxy --lab`` (or ``-y``) starts Python with LAB (Linear AlgeBra system) imports (to emulate MATLAB, R,...)
- ``$ fxy --plot`` (or ``-p``) for plotting imports

So, for example, if you want LAB imports with plotting and in IPython, then you'd:

- ``$ fxy -ip --lab``

You can also run the equivalent of `--calc` environment, that imports ``mpmath`` and ``eday``, like this:

``python -m fxy "pi**2"``

The following are usage examples.

CALC
----

::

    >>> from fxy.calc import *
    >>> pi
    <pi: 3.14159~>
    >>> mp.dps = 250
    >>> print(pi)

    >>> from fxy.plot import *
    >>> plt.plot([1, 2, 3, 4])
    >>> plt.ylabel('some numbers')
    >>> plt.show()

CAS
---

::

    >>> from fxy.cas import *
    >>> f = x**4 - 4*x**3 + 4*x**2 - 2*x + 3
    >>> f.subs([(x, 2), (y, 4), (z, 0)])
    -1
    >>> plot(f)
    >>> plot3d(x**2-y**2)

LAB
---

::

    >>> from fxy.lab import *
    >>> df = pandas.DataFrame({'x': numpy.arange(10), 'y': np.random.random(10)})
    >>> df.sum()
    x    45.000000
    y     4.196558
    dtype: float64

    >>> X = [[0], [1], [2], [3]]
    >>> y = [0, 0, 1, 1]
    >>> neigh = sklearn.neighbors.KNeighborsClassifier(n_neighbors=3)
    >>> neigh.fit(X, y)
    >>> print(neigh.predict([[1.1]]))
    [0]
    >>> print(neigh.predict_proba([[0.9]]))
    [[0.66666667 0.33333333]]


Suggestions
-----------

If you envy ``R`` users being able to start their 'calculator' with just one key, add something like the below to your ``~/.zshrc``:

::

    # Basic Calculaor
    function f() {
        . ~/.venv/bin/activate
        fxy "$@"
    }

    # Computer Algebra System
    function F() {
        . ~/.venv/bin/activate
        fxy --qt --cas
    }


Aliasing ``fxy`` as ``f`` command as simplest generic, and commonly used specific as ``F`` command makes it possible to:

- Use ``f`` to start Python with just ``mpmath`` for fastest scientific calculations without ``IPython``.
- Use ``F`` to start Python with some specific other pre-configuration that you often use (e.g., ``f -ix`` emulates ``isympy``).


.. _isympy:
    https://linux.die.net/man/1/isympy

Versioned namespace profiles
----------------------------

fxy can also treat its computational vocabularies as named, inspectable
contracts rather than only as preconfigured environments. Profile versions are
independent of package versions, so a notebook can record the mathematical
dialect it expects::

    import fxy

    fxy.available()
    # ('calc/v1', 'cas/v1', 'lab/v1')

    fxy.use('cas/v1')
    f = x**2 + y**2

Unversioned names are convenience aliases for the current contract::

    fxy.use('cas')          # currently cas/v1

Profiles can be inspected without injecting anything into the current namespace::

    fxy.names('cas/v1')
    fxy.describe('cas/v1')
    fxy.diff('cas/v1', 'lab/v1')

The initial v1 profiles intentionally mirror the existing star-import behaviour.
Because the legacy modules conditionally import optional dependencies, the names
realized by a v1 profile still depend on the current Python environment. The v1
identifier therefore stabilizes the selection semantics and makes the realized
namespace inspectable; a future cas/v2 or lab/v2 can become a curated, explicitly
dependency-declared contract without silently changing old notebooks.

GitHub-hosted profiles
----------------------

A profile can also live in a public GitHub repository.  The source syntax follows
the familiar ``owner/repo`` convention, with an optional branch, tag or commit::

    fxy.use('mindey/cas')
    fxy.use('mindey/cas@main')
    fxy.use('mindey/cas@8f1810c')

The repository contains ``fxy.py`` at its root.  The file is declarative: fxy
parses it and permits imports plus literal profile metadata, but does not execute
arbitrary Python code::

    __fxy_profile__ = 1
    __requires__ = ['sympy>=1.13', 'mpmath>=1.3']

    import sympy as sp
    from sympy import symbols, Eq, solve, diff, integrate
    from mpmath import mp

Remote profiles are cached under the user's cache directory.  Unpinned
``owner/repo`` sources use GitHub's ``HEAD`` ref; pin a tag or commit when
reproducibility matters.  Cached sources are reused by default; pass
``refresh=True`` to ``use()``, ``namespace()`` or ``describe()`` to fetch the
selected ref again.

Dependency installation is never implicit.  A profile may declare requirements,
but installing them requires an explicit approval::

    fxy.install('mindey/cas', approve=True)

For interactive convenience, ``fxy.use(..., install_missing=True)`` is the
explicit auto-approval form.  Without it, a missing import raises an error that
shows the profile's declared requirements.

This GitHub source form is intentionally small enough to support a future
registry: a registry entry only needs to map a short name to an ``owner/repo``
(or pinned ``owner/repo@ref``) source.
