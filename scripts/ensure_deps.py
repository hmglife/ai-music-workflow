#!/usr/bin/env python3
"""Make sure this skill's Python dependencies are available — without bothering the designer.

Why this exists: an audio designer is not a Python user. Telling them to "run pip install openpyxl"
is a wall at step one, and it is also ambiguous — the host may run these scripts with a managed
interpreter that is NOT whatever `pip` resolves to in their shell, so following that instruction can
install the package into the wrong environment and the error stays.

So the assistant runs this instead. It installs into **the exact interpreter that will run the
scripts** (`sys.executable`), which removes the wrong-environment failure mode entirely.

Usage:

    # Ensure everything the skill can need (safe default before a session)
    python ensure_deps.py

    # Only what a specific job needs
    python ensure_deps.py --for excel      # openpyxl
    python ensure_deps.py --for image      # openpyxl + Pillow  (embed a reference picture)
    python ensure_deps.py --for word       # python-docx        (distil from .docx source docs)

    # Report only, install nothing (exit 1 if something is missing)
    python ensure_deps.py --check

Notes:
  - Standard library only, so this script itself can never fail on a missing dependency.
  - Already-satisfied packages are skipped, so re-running is cheap and safe.
  - If installation is impossible (no pip, no network, locked-down environment), it says so plainly
    and exits non-zero instead of pretending. The caller should then tell the user what is degraded
    (e.g. "the document will be generated without the embedded reference image") rather than
    dumping a pip command on them.
"""
import sys
import argparse
import importlib
import subprocess

# import name -> (pip name, what it unlocks)
PACKAGES = {
    "openpyxl": ("openpyxl", "read/write the Excel requirement & feedback documents"),
    "PIL": ("Pillow", "embed a reference picture into the Excel"),
    "docx": ("python-docx", "read .docx source documents during distillation"),
}

GROUPS = {
    "excel": ["openpyxl"],
    "image": ["openpyxl", "PIL"],
    "word": ["docx"],
    "all": ["openpyxl", "PIL", "docx"],
}


def have(mod):
    try:
        importlib.import_module(mod)
        return True
    except Exception:
        # A broken install (ImportError from a bad binary wheel, etc.) counts as "not usable".
        return False


def install(pip_name):
    """Install into THIS interpreter. Returns (ok, message)."""
    cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q", pip_name]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except FileNotFoundError:
        return False, "interpreter cannot be invoked"
    except subprocess.TimeoutExpired:
        return False, "timed out after 300s (no network?)"
    if proc.returncode == 0:
        return True, ""
    err = (proc.stderr or proc.stdout or "").strip().splitlines()
    tail = err[-1] if err else f"pip exited {proc.returncode}"
    if "externally-managed-environment" in "\n".join(err):
        tail = "environment is externally managed (pip refuses to install here)"
    elif "No module named pip" in "\n".join(err):
        tail = "this interpreter has no pip"
    return False, tail


def main():
    ap = argparse.ArgumentParser(description="Ensure this skill's Python dependencies are present.")
    ap.add_argument("--for", dest="group", choices=sorted(GROUPS), default="all",
                    help="only ensure what this job needs (default: all)")
    ap.add_argument("--check", action="store_true",
                    help="report status only, install nothing")
    args = ap.parse_args()

    wanted = GROUPS[args.group]
    print(f"[env] interpreter: {sys.executable}")

    missing = [m for m in wanted if not have(m)]
    for m in wanted:
        pip_name, why = PACKAGES[m]
        if m not in missing:
            print(f"  [ok]      {pip_name:12} already available")

    if not missing:
        print("[ok] all required dependencies are present — nothing to do.")
        return 0

    if args.check:
        for m in missing:
            pip_name, why = PACKAGES[m]
            print(f"  [missing] {pip_name:12} needed to {why}")
        print(f"[check] {len(missing)} missing. Run this script without --check to install them.")
        return 1

    failed = []
    for m in missing:
        pip_name, why = PACKAGES[m]
        print(f"  [install] {pip_name} ... ({why})", flush=True)
        ok, msg = install(pip_name)
        if ok and have(m):
            print(f"  [ok]      {pip_name:12} installed")
        else:
            failed.append((pip_name, why, msg or "import still fails after install"))

    if failed:
        print(f"[error] {len(failed)} dependency/dependencies could not be installed:")
        for pip_name, why, msg in failed:
            print(f"  - {pip_name}: {msg}")
            print(f"    (needed to {why})")
        print("[error] Do NOT relay a raw pip command to the designer — explain in plain language")
        print("        what is unavailable, or retry in an environment that allows installs.")
        return 2

    print("[ok] all dependencies ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
