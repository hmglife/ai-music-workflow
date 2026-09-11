#!/usr/bin/env python3
"""Package this skill into a shareable, version-stamped zip — and refuse to leak private data.

Why this exists as a script rather than a documented procedure: the exclusion list is the only
thing standing between a shared package and one designer's private material. A rule written in a
README gets skipped; a rule written here cannot be. The build **fails** rather than warns when it
finds something that must not ship.

What must never be packaged:
  - the distilled profile (`data/profile*`) — it is one person's working style, learned from their
    real documents, and it is the one artefact in this skill that cannot be recreated
  - `data/inbox/*` — the designer's real requirement documents (often an entire project's briefs)
  - `data/feedback/*` — accumulated per-platform tuning notes, which quote real projects
  - installer metadata (`_user_meta.json` …), caches, editor cruft

Empty `.gitkeep` files are kept so the folder structure survives.

Usage:

    python scripts/package_skill.py                  # -> dist/ai-music-workflow-<version>.zip
    python scripts/package_skill.py --out-dir <dir>  # write somewhere else
    python scripts/package_skill.py --check          # audit only, build nothing

The version is read from the `version:` field in SKILL.md frontmatter — the single source of truth.
Each build gets its own filename, so previous releases stay available to roll back to.

No third-party dependencies — standard library only.
"""
import os
import re
import sys
import json
import zipfile
import argparse

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_NAME = os.path.basename(SKILL_ROOT)

# Files that are local to one machine or one person, never part of the skill.
EXCLUDE_NAMES = {"_user_meta.json", "_skillhub_meta.json", "_knot_meta.json",
                 ".DS_Store", "Thumbs.db", "desktop.ini"}
EXCLUDE_DIRS = {"__pycache__", ".git", ".idea", ".vscode", "dist", "node_modules"}
EXCLUDE_SUFFIX = (".pyc", ".pyo", ".bak", ".tmp", ".orig", ".swp")
# Directories whose *contents* are personal; the folder itself ships (via .gitkeep).
PRIVATE_DIRS = ("data/inbox/", "data/feedback/")
# Path prefixes that are personal outright.
PRIVATE_PREFIXES = ("data/profile",)


def read_version():
    """Single source of truth: the version field in SKILL.md frontmatter."""
    path = os.path.join(SKILL_ROOT, "SKILL.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(4000)
    except OSError as e:
        print(f"[error] cannot read SKILL.md: {e}")
        return None
    m = re.match(r"^---\s*\n(.*?)\n---", head, re.S)
    if not m:
        print("[error] SKILL.md has no YAML frontmatter")
        return None
    v = re.search(r'^version:\s*"?([^"\n]+)"?\s*$', m.group(1), re.M)
    if not v:
        print('[error] no version field in SKILL.md frontmatter. Add e.g.  version: "1.0.0"')
        return None
    version = v.group(1).strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        print(f'[warn] version "{version}" is not MAJOR.MINOR.PATCH; see CHANGELOG.md')
    return version


def classify(rel, name):
    """Return None to include, or a reason string to exclude."""
    if name in EXCLUDE_NAMES:
        return "local metadata"
    if name.endswith(EXCLUDE_SUFFIX):
        return "build/editor artefact"
    if any(rel.startswith(p) for p in PRIVATE_PREFIXES):
        return "PRIVATE: distilled profile"
    for d in PRIVATE_DIRS:
        if rel.startswith(d) and name != ".gitkeep":
            return f"PRIVATE: contents of {d}"
    return None


def walk_skill():
    """Yield (abs_path, rel_path, exclude_reason_or_None) for every file in the skill."""
    for root, dirs, files in os.walk(SKILL_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in sorted(files):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, SKILL_ROOT).replace("\\", "/")
            yield p, rel, classify(rel, f)


def audit(entries):
    """Report what will be excluded. Private material is reported loudly."""
    private = [(rel, why) for _, rel, why in entries if why and why.startswith("PRIVATE")]
    other = [(rel, why) for _, rel, why in entries if why and not why.startswith("PRIVATE")]
    if private:
        print(f"[privacy] {len(private)} private file(s) found and will be EXCLUDED:")
        for rel, why in private[:5]:
            print(f"          - {rel}  ({why})")
        if len(private) > 5:
            print(f"          - …and {len(private) - 5} more")
    if other:
        print(f"[skip] {len(other)} local/build file(s): {[r for r, _ in other][:4]}"
              + (" …" if len(other) > 4 else ""))
    return private, other


def verify_package(zip_path):
    """Re-open the built zip and prove nothing private got in. Belt and braces."""
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        bad = []
        for n in names:
            rel = n.split(f"{SKILL_NAME}/", 1)[-1]
            base = os.path.basename(rel)
            if classify(rel, base):
                bad.append(n)
        broken = z.testzip()
    return bad, broken, len(names)


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--out-dir", default=os.path.join(SKILL_ROOT, "dist"),
                    help="where to write the zip (default: <skill>/dist)")
    ap.add_argument("--check", action="store_true",
                    help="audit what would be included/excluded, but build nothing")
    args = ap.parse_args()

    version = read_version()
    if not version:
        return 2

    entries = list(walk_skill())
    included = [(p, rel) for p, rel, why in entries if why is None]
    audit(entries)

    print(f"[info] {SKILL_NAME} v{version} — {len(included)} file(s) to package")
    if args.check:
        print("[check] audit only, nothing written.")
        return 0

    out_dir = os.path.abspath(os.path.expanduser(args.out_dir))
    os.makedirs(out_dir, exist_ok=True)
    zip_path = os.path.join(out_dir, f"{SKILL_NAME}-{version}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p, rel in included:
            z.write(p, f"{SKILL_NAME}/{rel}")

    bad, broken, count = verify_package(zip_path)
    if bad:
        # Should be unreachable; if it happens, the package is unsafe to share.
        os.remove(zip_path)
        print(f"[FAIL] private/excluded files ended up in the package: {bad}")
        print("       The package was deleted. Fix the exclusion rules before sharing.")
        return 1
    if broken:
        os.remove(zip_path)
        print(f"[FAIL] zip integrity check failed at {broken}; package deleted.")
        return 1

    size_kb = os.path.getsize(zip_path) / 1024
    print(f"[ok] {os.path.relpath(zip_path, os.getcwd()) if os.path.isabs(zip_path) else zip_path}")
    print(f"     {count} entries, {size_kb:.1f} KB — verified clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
