#!/usr/bin/env python3
"""Manage the distilled designer profile so a skill upgrade never loses it.

THE PROBLEM this solves
-----------------------
The distilled profile used to live at `<skill>/data/profile.md`. Upgrading a skill means replacing
the whole skill folder, so the one genuinely irreplaceable artefact — the designer's learned
profile, distilled from their real past documents — got wiped along with it. Re-distilling needs
those source documents again, which the designer may no longer have to hand.

THE FIX
-------
The profile's home is now OUTSIDE the skill folder, in the user's WorkBuddy data directory:

    <user_home>/.workbuddy/ai-music-workflow/profile.md        (the durable home)

Upgrades replace `<skill>/` and never touch that path. The skill reads the external copy first and
falls back to the legacy in-skill path, so an existing install keeps working untouched.

USAGE
-----
    # Where is the profile? What state is everything in? (run this first)
    python profile_store.py status

    # Move a legacy in-skill profile out to the durable home (safe, idempotent)
    python profile_store.py migrate

    # Import a profile from anywhere — e.g. an old skill folder, or a backup zip you extracted
    python profile_store.py import --from <path-to-old-profile.md>
    python profile_store.py import --from <path-to-old-skill-folder>     # finds data/profile.md

    # Back the profile up before re-distilling or upgrading
    python profile_store.py backup

    # Print the resolved profile path for other tooling to consume
    python profile_store.py path

Nothing is ever deleted without an explicit flag, and every overwrite is backed up first.
Standard library only.
"""
import os
import sys
import shutil
import argparse
from datetime import datetime

SKILL_NAME = "ai-music-workflow"
PROFILE_NAME = "profile.md"


def skill_dir():
    """The skill folder = parent of this script's directory (scripts/ lives inside it)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def durable_dir():
    """Stable per-user home for learned data, outside the skill folder."""
    return os.path.join(os.path.expanduser("~"), ".workbuddy", SKILL_NAME)


def durable_profile():
    return os.path.join(durable_dir(), PROFILE_NAME)


def legacy_profile():
    return os.path.join(skill_dir(), "data", PROFILE_NAME)


def resolve_profile():
    """The profile the skill should read: durable copy wins, legacy is the fallback."""
    d, l = durable_profile(), legacy_profile()
    if os.path.isfile(d):
        return d
    if os.path.isfile(l):
        return l
    return None


def _stamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _backup(path):
    """Copy `path` next to itself with a timestamp. Returns the backup path, or None."""
    if not os.path.isfile(path):
        return None
    base, ext = os.path.splitext(path)
    dst = f"{base}.bak-{_stamp()}{ext}"
    shutil.copy2(path, dst)
    return dst


def _describe(path):
    if not path or not os.path.isfile(path):
        return "缺失 / absent"
    size = os.path.getsize(path)
    when = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
    return f"{size} B · 修改于 {when}"


def cmd_status(_args):
    d, l = durable_profile(), legacy_profile()
    active = resolve_profile()
    print("画像存放情况 / Profile store")
    print(f"  持久位置 (升级不受影响): {d}")
    print(f"      {_describe(d)}")
    print(f"  技能内旧位置 (升级会被覆盖): {l}")
    print(f"      {_describe(l)}")
    print()
    if active is None:
        print("  → 当前没有任何画像。做一次蒸馏，或用 import 导入旧版画像。")
        return 0
    which = "持久位置" if active == d else "技能内旧位置"
    print(f"  → 生效中的画像: {which}")
    print(f"     {active}")
    if active == l:
        print()
        print("  ⚠ 这份画像还在技能文件夹里，升级技能时会被清掉。")
        print("    建议现在执行:  python profile_store.py migrate")
    backups = []
    for folder in (durable_dir(), os.path.dirname(l)):
        if os.path.isdir(folder):
            backups += [os.path.join(folder, f) for f in sorted(os.listdir(folder))
                        if f.startswith("profile") and ".bak" in f]
    if backups:
        print()
        print(f"  备份 {len(backups)} 份:")
        for b in backups[-5:]:
            print(f"    · {b}")
    return 0


def _install(src, why):
    """Copy `src` into the durable home, backing up whatever is already there."""
    if not os.path.isfile(src):
        print(f"[error] 找不到画像文件: {src}")
        return 2
    os.makedirs(durable_dir(), exist_ok=True)
    dst = durable_profile()
    if os.path.abspath(src) == os.path.abspath(dst):
        print(f"[ok] 已经在持久位置，无需处理: {dst}")
        return 0
    b = _backup(dst)
    if b:
        print(f"[backup] 原有画像已备份 → {b}")
    shutil.copy2(src, dst)
    print(f"[ok] {why}")
    print(f"      来源: {src}")
    print(f"      现在: {dst}")
    return 0


def cmd_migrate(args):
    l = legacy_profile()
    if not os.path.isfile(l):
        if os.path.isfile(durable_profile()):
            print(f"[ok] 技能内没有旧画像，持久位置已有一份: {durable_profile()}")
            return 0
        print("[note] 没有需要迁移的画像（技能内和持久位置都没有）。")
        return 0
    rc = _install(l, "画像已迁移到持久位置，之后升级技能不会再丢")
    if rc == 0 and args.remove_legacy:
        b = _backup(l)
        try:
            os.remove(l)
            print(f"[ok] 已移除技能内的旧副本（备份在 {b}）")
        except OSError as e:
            # Some environments block deletes (sandbox / no recycle bin / read-only skill dir).
            # The migration itself already succeeded, so this is a cleanup nicety, not a failure.
            print(f"[warn] 无法自动删除技能内的旧副本: {e}")
            print(f"       迁移本身已成功，持久位置的画像才是生效的那份。")
            print(f"       如需清理，手动删除: {l}")
    elif rc == 0:
        print("      技能内的旧副本保留未动；确认无误后可加 --remove-legacy 清掉。")
    return rc


def _find_in_dir(root, depth=4):
    """Look for a profile inside a folder the user pointed at.

    Accepts anything a designer might plausibly hand over: the old skill folder, its `data/`
    subfolder, an extracted backup, or a folder that just contains the file. Searches the obvious
    spots first, then walks a bounded depth so a nested copy is still found.
    """
    for cand in (os.path.join(root, "data", PROFILE_NAME),
                 os.path.join(root, PROFILE_NAME),
                 os.path.join(root, SKILL_NAME, "data", PROFILE_NAME)):
        if os.path.isfile(cand):
            return cand
    hits = []
    root_depth = root.rstrip(os.sep).count(os.sep)
    for cur, dirs, files in os.walk(root):
        if cur.count(os.sep) - root_depth >= depth:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            # profile.md plus timestamped backups like profile.bak-20260811-151519.md
            if f == PROFILE_NAME or (f.startswith("profile") and f.endswith(".md")):
                hits.append(os.path.join(cur, f))
    if not hits:
        return None
    # Prefer an exact profile.md over a .bak, then the most recently modified.
    hits.sort(key=lambda p: (os.path.basename(p) != PROFILE_NAME, -os.path.getmtime(p)))
    return hits[0]


def _extract_from_zip(zip_path):
    """Pull a profile out of a zipped-up old skill package into a temp file."""
    import zipfile
    import tempfile
    try:
        z = zipfile.ZipFile(zip_path)
    except Exception as e:
        print(f"[error] 无法打开 zip: {e}")
        return None
    members = [n for n in z.namelist()
               if n.endswith(f"/{PROFILE_NAME}") or n == PROFILE_NAME
               or (os.path.basename(n).startswith("profile") and n.endswith(".md"))]
    if not members:
        print(f"[error] zip 里没有找到 {PROFILE_NAME}: {zip_path}")
        return None
    members.sort(key=lambda n: os.path.basename(n) != PROFILE_NAME)
    pick = members[0]
    tmp = os.path.join(tempfile.mkdtemp(prefix="amw-profile-"), PROFILE_NAME)
    with z.open(pick) as fh, open(tmp, "wb") as out:
        shutil.copyfileobj(fh, out)
    print(f"[zip] 从压缩包取出: {pick}")
    return tmp


def cmd_import(args):
    src = os.path.expanduser(args.source.strip().strip('"').strip("'"))
    if not os.path.exists(src):
        print(f"[error] 路径不存在: {src}")
        print("        请给旧的 profile.md、旧技能文件夹，或旧技能的 zip 备份。")
        return 2
    if os.path.isdir(src):
        found = _find_in_dir(src)
        if not found:
            print(f"[error] 在这个目录里找不到画像文件: {src}")
            print(f"        找过 <dir>/data/{PROFILE_NAME}、<dir>/{PROFILE_NAME}，并递归搜索了 4 层。")
            return 2
        if os.path.basename(found) != PROFILE_NAME:
            print(f"[note] 没有 {PROFILE_NAME}，改用最近的备份: {os.path.basename(found)}")
        src = found
    elif src.lower().endswith(".zip"):
        src = _extract_from_zip(src)
        if not src:
            return 2
    return _install(src, "已导入旧版画像")


def cmd_backup(_args):
    active = resolve_profile()
    if not active:
        print("[note] 没有画像可备份。")
        return 0
    b = _backup(active)
    print(f"[ok] 已备份 → {b}")
    return 0


def cmd_path(_args):
    p = resolve_profile()
    if p:
        print(p)
        return 0
    print("", end="")
    return 1


def main():
    ap = argparse.ArgumentParser(description="管理蒸馏画像的存放位置，使技能升级不丢数据")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("status", help="显示画像位置与状态（先跑这个）").set_defaults(func=cmd_status)

    m = sub.add_parser("migrate", help="把技能内的画像迁到持久位置")
    m.add_argument("--remove-legacy", action="store_true",
                   help="迁移成功后删除技能内的旧副本（会先备份）")
    m.set_defaults(func=cmd_migrate)

    i = sub.add_parser("import", help="从旧技能目录或备份导入画像")
    i.add_argument("--from", dest="source", required=True,
                   help="旧的 profile.md，或包含它的目录（如旧技能文件夹）")
    i.set_defaults(func=cmd_import)

    sub.add_parser("backup", help="备份当前画像").set_defaults(func=cmd_backup)
    sub.add_parser("path", help="打印生效中的画像路径").set_defaults(func=cmd_path)

    args = ap.parse_args()
    if not getattr(args, "func", None):
        ap.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
