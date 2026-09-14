#!/usr/bin/env python3
"""Make a skill's Python dependencies importable, installing quietly if they aren't.

Cowork gives every session a fresh container, so anything installed in a previous
session — or by a setup command someone ran last week — is gone. Relying on a setup
step means the first real use of a skill fails for most people. So each script asks
for what it needs, every run, and installs it if it isn't there.

Three rules this follows:

- **Silent.** Nothing is printed when the packages are already present, which is the
  normal case after the first run in a session. Output belongs to the skill, not to
  its plumbing.
- **Never fatal.** A package that won't install is reported to the caller as missing
  and the script carries on with whatever it can still do. A missing pyoxipng should
  cost slightly larger PNGs, not the whole run.
- **User scope only.** Installs go to the user's own site-packages. Nothing here
  writes system-wide or asks for elevation, which is also why gifsicle comes from the
  gifsicle-bin wheel rather than a package manager.

Two ways in:

    from ensure_deps import ensure            # inside a script
    ensure("image-compressor")

    python3 ensure_deps.py image-compressor   # or ahead of time, in the background,
                                              # while the skill is still asking questions
"""

import importlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_dependencies import REQUIREMENTS  # noqa: E402  (single source of truth)

_INSTALL_TIMEOUT = 180


def _needed_by(skill):
    for module, install, kind, level, used_by, _what in REQUIREMENTS:
        if skill in [u.strip() for u in used_by.split(",")]:
            yield module, install, kind, level


def _present(module, kind):
    if kind == "binary":
        from shutil import which
        return which(module) is not None
    try:
        importlib.import_module(module)
        return True
    except Exception:
        return False


def _adopt_user_paths():
    """Make a just-installed --user package usable without restarting.

    The interpreter resolved sys.path and PATH before pip ran, so a fresh install is
    on disk but invisible. Derive both from sysconfig rather than guessing at the
    layout — the user scripts directory is not a sibling of site-packages on macOS.
    """
    import sysconfig
    import site
    try:
        user_site = site.getusersitepackages()
        if user_site and user_site not in sys.path:
            sys.path.append(user_site)
    except Exception:
        pass
    for scheme in ("osx_framework_user", "posix_user", "nt_user"):
        if scheme not in sysconfig.get_scheme_names():
            continue
        try:
            scripts = sysconfig.get_path("scripts", scheme)
        except Exception:
            continue
        if scripts and os.path.isdir(scripts):
            path = os.environ.get("PATH", "")
            if scripts not in path.split(os.pathsep):
                os.environ["PATH"] = scripts + os.pathsep + path


def ensure(skill, quiet=True):
    """Install whatever `skill` needs and isn't already importable.

    Returns a dict of install-name -> level for anything still missing afterwards,
    so a caller can degrade deliberately instead of crashing on the import.
    """
    missing = [(m, i, k, l) for m, i, k, l in _needed_by(skill) if not _present(m, k)]
    if not missing:
        return {}

    targets = sorted({i for _m, i, _k, _l in missing})
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", "--quiet",
             "--disable-pip-version-check", *targets],
            check=False, timeout=_INSTALL_TIMEOUT,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    importlib.invalidate_caches()
    _adopt_user_paths()

    still = {i: l for m, i, k, l in missing if not _present(m, k)}
    if still and not quiet:
        for name, level in still.items():
            print(f"note: {name} unavailable ({level}) — continuing without it",
                  file=sys.stderr)
    return still


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        print(f"usage: {os.path.basename(__file__)} <skill-name>", file=sys.stderr)
        sys.exit(2)
    ensure(sys.argv[1])
    sys.exit(0)
