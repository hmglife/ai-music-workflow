#!/usr/bin/env python3
"""Archive the designer's reference materials next to the generated document.

Why this exists: an audio designer's brief is rarely just text. They hand over concept art, a
screen-recording of the cutscene, a temp track, a voice memo humming the melody. If only the Excel
is delivered, those originals stay scattered in chat attachments / Downloads and the studio (or the
designer six months later) can't find what "参考那个视频里 0:12 的感觉" referred to.

So every delivery is a self-contained folder, with the media folders sitting directly beside the
document (no extra nesting level):

    <workspace>/output/<ProjectSlug>_<Type>_<date>/
    ├── <ProjectSlug>_<Type>_<date>.xlsx    the requirement / feedback document
    ├── Image/      concept art, key visuals, video stills
    ├── Video/      reference footage the designer sent
    ├── Audio/      temp tracks, voice memos, studio deliveries
    ├── Other/      anything else (pdf, zip, project files …)
    └── ASSETS.md   manifest: what each file is, where it came from

Only the folders that actually receive files get created — a delivery with one reference image
contains `Image/` and nothing else.

Usage:

    # Archive files/folders into a delivery folder (copies, never moves — originals stay put)
    python collect_assets.py --out-dir <delivery_folder> \
        --asset <path> [--asset <path>...] [--note "<path>=<what it is>"]

    # Also accepts a whole folder; every supported file inside is archived recursively
    python collect_assets.py --out-dir <delivery_folder> --asset ~/Downloads/refs/

    # Emit machine-readable JSON of what was archived (handy for chaining into the Excel)
    python collect_assets.py --out-dir <folder> --asset a.png --json

Behaviour notes:
  - COPY, not move. The designer's originals are never touched or deleted.
  - Name collisions get a numeric suffix instead of overwriting (`ref.png` → `ref_2.png`).
  - Filenames are sanitised for cross-platform safety, but CJK characters are kept (a designer's
    "主角登场_参考.png" stays readable).
  - Re-running is safe: identical files (same size + content hash) are skipped, not duplicated.
  - **The manifest never records absolute paths.** A delivery folder is handed to an outside music
    studio, so leaking the designer's home directory layout would be a privacy leak. Only the
    archived relative path and the original *file name* are written.
  - Notes persist in `.assets_meta.json`, so a later run never wipes earlier descriptions.
  - The generated document itself (xlsx/docx/pptx in the delivery root) is never archived as an
    asset, so pointing --asset at the delivery folder can't create a copy of the deliverable.
  - ASSETS.md is regenerated from the folder's real contents each run, so it never goes stale.

No third-party dependencies — standard library only.
"""
import os
import re
import sys
import json
import shutil
import hashlib
import argparse
from datetime import datetime

# Capitalised on disk — they sit next to the deliverable and are seen by the studio, so they read
# as proper section names rather than lowercase code identifiers.
KINDS = ("Image", "Video", "Audio", "Other")

KIND_BY_EXT = {
    "Image": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff", ".heic", ".svg"},
    "Video": {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".wmv", ".flv"},
    "Audio": {".wav", ".mp3", ".flac", ".aiff", ".aif", ".m4a", ".ogg", ".aac", ".wma", ".mid",
              ".midi"},
}
# Junk that should never end up in a delivery folder.
SKIP_NAMES = {".ds_store", "thumbs.db", "desktop.ini", "assets.md"}
# The deliverable document itself is not a reference asset.
SKIP_EXT = {".xlsx", ".xlsm", ".xls", ".docx", ".doc", ".pptx", ".ppt"}
META_NAME = ".assets_meta.json"

KIND_LABEL = {
    "Image": "图片 / Image",
    "Video": "视频 / Video",
    "Audio": "音频 / Audio",
    "Other": "其他 / Other",
}


def kind_of(path):
    ext = os.path.splitext(path)[1].lower()
    for kind, exts in KIND_BY_EXT.items():
        if ext in exts:
            return kind
    return "Other"


def kind_dir(out_dir, kind):
    """Target folder for a kind, reusing a legacy lowercase folder if one really exists.

    Earlier versions wrote `image/` `video/` … Re-running against such a delivery must not create a
    second, differently-cased folder next to it. The check must compare the REAL directory entry
    name: on Windows/macOS `os.path.isdir("D/image")` also returns True when only `D/Image` exists,
    so a naive isdir() test would wrongly downgrade every new delivery to the legacy casing.
    """
    if kind.lower() != kind and os.path.isdir(out_dir):
        try:
            entries = os.listdir(out_dir)
        except OSError:
            entries = []
        if kind.lower() in entries and kind not in entries:
            return os.path.join(out_dir, kind.lower())
    return os.path.join(out_dir, kind)


def safe_name(name):
    """Strip characters that break on Windows/macOS while keeping CJK and spaces readable."""
    name = os.path.basename(name)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or "asset"


def file_hash(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0


def expand(targets, out_dir=None):
    """Turn a mix of files and directories into a flat list of real files.

    Skips junk files, the deliverable document itself, and anything already living inside the
    delivery folder's own kind folders — so pointing --asset at the delivery folder is harmless.
    """
    archived_roots = set()
    if out_dir:
        for k in KINDS:
            archived_roots.add(os.path.normcase(os.path.abspath(os.path.join(out_dir, k))))
            archived_roots.add(os.path.normcase(os.path.abspath(os.path.join(out_dir, k.lower()))))

    def keep(path):
        base = os.path.basename(path)
        if base.lower() in SKIP_NAMES or base.startswith("."):
            return False
        if os.path.splitext(base)[1].lower() in SKIP_EXT:
            print(f"[skip] deliverable document, not an asset: {base}")
            return False
        parent = os.path.normcase(os.path.abspath(os.path.dirname(path)))
        if parent in archived_roots:
            return False
        return True

    files = []
    for t in targets:
        t = os.path.expanduser(t)
        if os.path.isdir(t):
            for root, dirs, names in os.walk(t):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for n in sorted(names):
                    p = os.path.join(root, n)
                    if keep(p):
                        files.append(p)
        elif os.path.isfile(t):
            if keep(t):
                files.append(t)
        else:
            print(f"[warn] not found, skipped: {t}")
    return files


def unique_dest(dest_dir, name):
    base, ext = os.path.splitext(name)
    cand = os.path.join(dest_dir, name)
    i = 2
    while os.path.exists(cand):
        cand = os.path.join(dest_dir, f"{base}_{i}{ext}")
        i += 1
    return cand


def _meta_path(out_dir):
    return os.path.join(out_dir, META_NAME)


def load_meta(out_dir):
    """Previously recorded notes/sources, keyed by archived relative path.

    Persisted so that re-running (e.g. adding one more asset later, or just refreshing the
    manifest) never wipes the descriptions collected in an earlier run.
    """
    p = _meta_path(out_dir)
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            pass
    return {}


def save_meta(out_dir, meta):
    p = _meta_path(out_dir)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def archive(out_dir, targets, notes, meta):
    records = []
    for src in expand(targets, out_dir=out_dir):
        kind = kind_of(src)
        # Kind folders sit directly in the delivery folder — no intermediate 'assets' level.
        dest_dir = kind_dir(out_dir, kind)
        os.makedirs(dest_dir, exist_ok=True)
        name = safe_name(src)
        abs_src = os.path.abspath(src)
        note = notes.get(abs_src, notes.get(src, ""))

        # Idempotency: if an identical file is already archived here, don't duplicate it.
        try:
            src_size = os.path.getsize(src)
            src_hash = file_hash(src)
        except OSError as e:
            print(f"[warn] unreadable, skipped: {src} ({e})")
            continue
        already = None
        for existing in sorted(os.listdir(dest_dir)):
            ep = os.path.join(dest_dir, existing)
            if os.path.isfile(ep) and os.path.getsize(ep) == src_size and file_hash(ep) == src_hash:
                already = ep
                break
        if already:
            rel = os.path.relpath(already, out_dir).replace("\\", "/")
            print(f"[skip] already archived: {rel}")
        else:
            dest = unique_dest(dest_dir, name)
            shutil.copy2(src, dest)
            rel = os.path.relpath(dest, out_dir).replace("\\", "/")
            print(f"[ok] {kind:5s} → {rel}")

        prev = meta.get(rel, {})
        # Record only the original FILE NAME, never its absolute path: the delivery folder goes to
        # an outside studio and must not leak the designer's machine layout.
        meta[rel] = {"origin": os.path.basename(abs_src) or prev.get("origin", ""),
                     "note": note or prev.get("note", "")}
        records.append({"kind": kind, "file": rel, "origin": meta[rel]["origin"],
                        "size": src_size, "note": meta[rel]["note"]})
    return records


def scan_existing(out_dir):
    """Read back every archived file, so the manifest reflects the folder's real contents."""
    found = []
    for kind in KINDS:
        d = kind_dir(out_dir, kind)
        if not os.path.isdir(d):
            continue
        for n in sorted(os.listdir(d)):
            p = os.path.join(d, n)
            if os.path.isfile(p):
                found.append({"kind": kind,
                              "file": os.path.relpath(p, out_dir).replace("\\", "/"),
                              "size": os.path.getsize(p)})
    return found


def write_manifest(out_dir, meta):
    """Write ASSETS.md describing every archived file, using the persisted notes.

    Paths in the manifest are always relative to the delivery folder, and origins are bare file
    names — the document and its assets travel together, so relative paths are what the studio
    needs, and absolute paths would only leak the designer's directory structure.
    """
    rows = scan_existing(out_dir)
    # Name the folders that actually exist, so the sentence is true even in a legacy delivery
    # (older versions wrote lowercase folder names, and those are reused rather than duplicated).
    present = sorted({r["file"].split("/")[0] for r in rows})
    folder_list = " ".join(f"`{d}/`" for d in present) if present else "各类型子目录"
    lines = [
        "# 素材清单 / Asset manifest",
        "",
        f"生成时间 / Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"本目录随需求（或反馈）文档一起交付，{folder_list} 下是音频策划",
        "提供的全部参考原件。文档里引用素材时请使用下面的相对路径，音乐公司拿到整个文件夹即可对齐。",
        "",
    ]
    if not rows:
        lines += ["_（暂无素材）_", ""]

    def origin_of(r):
        """The designer's original file name, but only when the archived copy was renamed.

        A rename happens on a name collision or when characters had to be sanitised. When the name
        is unchanged the column would just repeat the file column, so it is omitted entirely.
        """
        o = (meta.get(r["file"], {}).get("origin") or "").replace("|", "\\|")
        return "" if o == os.path.basename(r["file"]) else o

    # Only carry the origin column when at least one file actually got renamed.
    show_origin = any(origin_of(r) for r in rows)

    for kind in KINDS:
        group = [r for r in rows if r["kind"] == kind]
        if not group:
            continue
        header = "| 文件 | 大小 | 说明 |" + (" 原始文件名 |" if show_origin else "")
        lines += [f"## {KIND_LABEL[kind]}", "",
                  header,
                  "|---|---|---|" + ("---|" if show_origin else "")]
        for r in group:
            note = (meta.get(r["file"], {}).get("note") or "").replace("|", "\\|") or "—"
            row = f"| `{r['file']}` | {human_size(r['size'])} | {note} |"
            if show_origin:
                row += f" {origin_of(r) or '—'} |"
            lines.append(row)
        lines.append("")
    path = os.path.join(out_dir, "ASSETS.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[ok] manifest: ASSETS.md  ({len(rows)} file(s))")
    return path, rows


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--out-dir", required=True,
                    help="the delivery folder (same folder the .xlsx is written into)")
    ap.add_argument("--asset", action="append", default=[],
                    help="a file or folder to archive; repeatable")
    ap.add_argument("--note", action="append", default=[],
                    help='describe an asset: --note "<path>=<what it is>"; repeatable')
    ap.add_argument("--json", action="store_true", help="print the archived records as JSON")
    args = ap.parse_args()

    notes = {}
    for n in args.note:
        if "=" in n:
            k, v = n.split("=", 1)
            k = os.path.expanduser(k.strip())
            notes[k] = v.strip()
            notes[os.path.abspath(k)] = v.strip()
        else:
            print(f"[warn] --note needs the form '<path>=<description>', got: {n}")

    out_dir = os.path.abspath(os.path.expanduser(args.out_dir))
    os.makedirs(out_dir, exist_ok=True)

    meta = load_meta(out_dir)
    records = archive(out_dir, args.asset, notes, meta) if args.asset else []
    # Allow annotating an already-archived file directly by its relative path.
    for k, v in notes.items():
        rel = k.replace("\\", "/")
        if rel in meta and v:
            meta[rel]["note"] = v
    save_meta(out_dir, meta)
    _, rows = write_manifest(out_dir, meta)

    if args.json:
        print(json.dumps({"out_dir": out_dir, "archived": records, "all": rows},
                         ensure_ascii=False, indent=2))
    if not args.asset:
        print("[note] no --asset given; only the manifest was refreshed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
