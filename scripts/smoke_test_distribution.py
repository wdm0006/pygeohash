#!/usr/bin/env python
"""Smoke-test a built pygeohash distribution before it is published.

The script installs a built artifact into a throwaway virtual environment and
then re-runs itself with that environment's interpreter from a directory outside
the source checkout, so the probe cannot import the working tree. It exits
non-zero when the distribution is missing the ``pygeohash`` package, missing the
compiled ``pygeohash.cgeohash.geohash_module`` extension, or fails to reproduce
known encode/decode values.

Usage:
    python scripts/smoke_test_distribution.py --wheelhouse wheelhouse
    python scripts/smoke_test_distribution.py --sdist dist/pygeohash-3.4.0.tar.gz
"""

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import venv

SOURCE_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Known values, independent of the installed build. A distribution missing the
# package or its compiled extension fails before ever reaching them.
KNOWN_LATITUDE = 42.6
KNOWN_LONGITUDE = -5.6
KNOWN_GEOHASH = "ezs42"
KNOWN_CENTER = (42.60498046875, -5.60302734375)
KNOWN_ERRORS = (0.02197265625, 0.02197265625)
BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def check(condition, message):
    """Raise ``SystemExit`` with ``message`` when ``condition`` is falsy."""
    if not condition:
        raise SystemExit("distribution smoke test failed: {}".format(message))


def parse_args(argv):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--wheelhouse", help="Directory holding wheels built for this platform.")
    group.add_argument("--sdist", help="Path to the built source distribution tarball.")
    group.add_argument(
        "--verify",
        action="store_true",
        help="Internal: probe the pygeohash already installed for this interpreter.",
    )
    parser.add_argument(
        "--source-root",
        default=str(SOURCE_ROOT),
        help="Path to the source checkout the distribution was built from.",
    )
    return parser.parse_args(argv)


def venv_python(env_dir):
    """Return the interpreter path of a virtual environment created at ``env_dir``."""
    if os.name == "nt":
        return env_dir / "Scripts" / "python.exe"
    return env_dir / "bin" / "python"


def install_command(python, args):
    """Build the pip command that installs the requested artifact."""
    command = [str(python), "-m", "pip", "install", "--no-cache-dir"]
    if args.wheelhouse:
        # --no-index/--only-binary force the install to resolve to a wheel from
        # this build; pip selects the one matching this platform and interpreter.
        command += ["--no-index", "--only-binary", ":all:", "--find-links", args.wheelhouse, "pygeohash"]
    else:
        # Installing the tarball directly builds this package from source, which
        # is what consumers without a matching wheel get.
        command += [args.sdist]
    return command


def install_and_probe(args):
    """Install the artifact into a clean environment and probe it from outside the checkout."""
    work_dir = pathlib.Path(tempfile.mkdtemp(prefix="pygeohash-smoke-"))
    try:
        env_dir = work_dir / "venv"
        # symlinks matches what ``python -m venv`` defaults to per platform;
        # copying the interpreter breaks relocated builds.
        venv.EnvBuilder(with_pip=True, symlinks=os.name != "nt").create(str(env_dir))
        python = venv_python(env_dir)

        subprocess.run(install_command(python, args), check=True)  # noqa: S603
        # The probe runs with the temporary directory as its working directory so
        # a bare ``import pygeohash`` cannot resolve to the source checkout.
        subprocess.run(  # noqa: S603
            [str(python), str(pathlib.Path(__file__).resolve()), "--verify", "--source-root", args.source_root],
            check=True,
            cwd=str(work_dir),
        )
    finally:
        shutil.rmtree(str(work_dir), ignore_errors=True)
    return 0


def check_outside_source_tree(module, source_root):
    """Fail when the imported module is unfiled or resolves into the source checkout."""
    module_file = getattr(module, "__file__", None)
    check(
        module_file is not None,
        "{} has no file on disk; the distribution installed it as an empty namespace package".format(module.__name__),
    )
    module_dir = pathlib.Path(module_file).resolve().parent
    source_root = pathlib.Path(source_root).resolve()
    check(
        source_root != module_dir and source_root not in module_dir.parents,
        "imported {} from the source checkout ({}), not the installed distribution".format(module.__name__, module_dir),
    )
    return module_dir


def verify(source_root):
    """Import the installed distribution and assert known encode/decode values."""
    import pygeohash as pgh
    from pygeohash.cgeohash import geohash_module

    package_dir = check_outside_source_tree(pgh, source_root)
    check_outside_source_tree(geohash_module, source_root)

    check(
        not str(geohash_module.__file__).endswith(".py"),
        "pygeohash.cgeohash.geohash_module is not a compiled extension ({})".format(geohash_module.__file__),
    )
    check(geohash_module.get_base32() == BASE32, "compiled extension returned an unexpected base32 alphabet")

    encoded = pgh.encode(KNOWN_LATITUDE, KNOWN_LONGITUDE, precision=len(KNOWN_GEOHASH))
    check(encoded == KNOWN_GEOHASH, "encode returned {!r}, expected {!r}".format(encoded, KNOWN_GEOHASH))

    native_encoded = geohash_module.encode(KNOWN_LATITUDE, KNOWN_LONGITUDE, precision=len(KNOWN_GEOHASH))
    check(
        native_encoded == KNOWN_GEOHASH,
        "compiled extension encode returned {!r}, expected {!r}".format(native_encoded, KNOWN_GEOHASH),
    )

    decoded = pgh.decode(KNOWN_GEOHASH)
    check(
        (decoded.latitude, decoded.longitude) == KNOWN_CENTER,
        "decode returned {!r}, expected {!r}".format(tuple(decoded), KNOWN_CENTER),
    )

    exact = pgh.decode_exactly(KNOWN_GEOHASH)
    check(
        (exact.latitude_error, exact.longitude_error) == KNOWN_ERRORS,
        "decode_exactly returned errors {!r}, expected {!r}".format(
            (exact.latitude_error, exact.longitude_error), KNOWN_ERRORS
        ),
    )

    from importlib.metadata import version

    print("pygeohash {} smoke test passed from {}".format(version("pygeohash"), package_dir))
    return 0


def main(argv=None):
    """Install the requested artifact and probe it, or probe an already installed one."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.verify:
        return verify(args.source_root)
    return install_and_probe(args)


if __name__ == "__main__":
    sys.exit(main())
