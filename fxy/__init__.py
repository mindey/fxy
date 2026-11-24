import importlib.util
import os
import subprocess
import sys


def interact(modules=(), mode=False):
    commands = "; ".join(f"from fxy.{module} import *" for module in modules)

    if mode:
        if importlib.util.find_spec("IPython") is None:
            raise RuntimeError(
                "IPython is not installed; install fxy[ipython] or fxy[all]."
            )
        command = [
            sys.executable,
            "-m",
            "IPython",
            "--no-banner",
            "-i",
            "-c",
            commands,
        ]
    else:
        command = [sys.executable, "-i", "-c", commands]

    try:
        subprocess.run(command, check=False)
    except FileNotFoundError as exc:
        if mode:
            raise RuntimeError(
                "IPython is not installed; install fxy[ipython] or fxy[all]."
            ) from exc
        raise


def run_qtconsole(name):
    required = ("IPython", "ipykernel", "jupyter_client", "qtconsole")
    missing = [module for module in required if importlib.util.find_spec(module) is None]
    if missing:
        raise RuntimeError(
            "QtConsole support is incomplete "
            f"(missing: {', '.join(missing)}); install fxy[qt] or fxy[all]."
        )

    from .kernels import kernel_exists, install_my_kernel_spec

    kernel = f"fxy_{name}"
    if not kernel_exists(kernel):
        install_my_kernel_spec(
            kernel,
            [f"from fxy.{name} import *", "from fxy.plot import *"],
        )

    command = [sys.executable, "-m", "qtconsole", "--kernel", kernel]

    subprocess.run(command, check=False)


def main():

    import argparse
    parser = argparse.ArgumentParser()

    # Mode
    parser.add_argument('-i', '--ipython', action='store_false', default=True, help='Verbose imports, IPython mode.')
    parser.add_argument('-q', '--qt', action='store_false', default=True, help='Kernel imports, QTConsole mode.')

    # Module
    parser.add_argument('-f', '--calc', action='store_false', default=True, help='CALC imports')
    parser.add_argument('-x', '--cas', action='store_false', default=True, help='CAS imports')
    parser.add_argument('-y', '--lab', action='store_false', default=True, help='LAB imports')
    parser.add_argument('-p', '--plotting', action='store_false', default=True, help='(MatplotLib, Seaborn)')


    args = parser.parse_args()

    # If QTConsole is selected, run the appropriate kernel
    if not(args.qt):

        if not(args.calc):
            run_qtconsole('calc')
            return
        if not(args.cas):
            run_qtconsole('cas')
            return
        if not(args.lab):
            run_qtconsole('lab')
            return

        run_qtconsole('calc')
        return

    # Choice of environment and plotting
    mode = not(args.ipython)
    plot = not(args.plotting)
    os.environ['_FXY_MODE_'] = mode and 'true' or ''
    os.environ['_FXY_PLOT_'] = plot and 'true' or ''
    # Default is MPMath for "calculator"
    module = 'calc'

    # Choice of library imports
    if not(args.calc):
        module = 'calc'
    if not(args.cas):
        module = 'cas'
    if not(args.lab):
        module = 'lab'

    interact([module], mode)


if __name__ == '__main__':
    main()

from ._version import __version__

# Versioned computational namespace profiles.
from .profiles import (
    Profile,
    available,
    describe as _local_describe,
    diff,
    names,
    namespace as _local_namespace,
    resolve,
    use as _local_use,
)
from . import remote


def _is_remote_profile(profile):
    # Consider GitHub sources only after local profile resolution.
    if not isinstance(profile, str):
        return False
    try:
        resolve(profile)
        return False
    except KeyError:
        return remote.is_source(profile)


def namespace(profile, **kwargs):
    if _is_remote_profile(profile):
        return remote.namespace(profile, **kwargs)
    if kwargs:
        raise TypeError("local profiles do not accept remote-profile options")
    return _local_namespace(profile)


def use(profile, target=None, **kwargs):
    # Resolve the caller here so both local and remote dispatch preserve an
    # interactive user's namespace rather than injecting into this wrapper.
    if target is None:
        import inspect
        frame = inspect.currentframe()
        try:
            caller = frame.f_back if frame is not None else None
            if caller is None:
                raise RuntimeError("cannot determine caller namespace")
            target = caller.f_globals
        finally:
            del frame

    if _is_remote_profile(profile):
        return remote.use(profile, target, **kwargs)
    if kwargs:
        raise TypeError("local profiles do not accept remote-profile options")
    return _local_use(profile, target)


def describe(profile, **kwargs):
    if _is_remote_profile(profile):
        return remote.describe(profile, **kwargs)
    if kwargs:
        raise TypeError("local profiles do not accept remote-profile options")
    return _local_describe(profile)


def install(profile, **kwargs):
    if not _is_remote_profile(profile):
        raise ValueError("dependency installation applies to remote profiles")
    return remote.install(profile, **kwargs)
