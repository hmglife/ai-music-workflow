#!/usr/bin/env python3
"""Extract plain text from audio-design source materials.

Supports: .docx, .xlsx/.xlsm/.xls, .txt, .md
Usage:
    python read_materials.py <file_or_dir> [--json]

- Given a directory, walks it recursively and extracts every supported file.
- Given a single file, extracts just that file.
- Default output is human-readable; pass --json for a JSON array of {file, type, text}.

Dependencies (only the ones you actually need are required): `python-docx` for .docx sources,
`openpyxl` for .xlsx/.xls. Missing deps are reported with an auto-install command targeting this
same interpreter (`ensure_deps.py`) instead of crashing everything — the designer is never asked
to install anything by hand.
"""
import sys
import os
import json

SUPPORTED = {".docx", ".xlsx", ".xlsm", ".xls", ".txt", ".md"}


def _need(pkg, group):
    """Point at the auto-installer, not at the designer.

    A raw `pip install` line is the wrong instruction twice over: the designer is not a Python user,
    and their shell `pip` may not even belong to the interpreter running this script.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    return (f"[missing dependency] {pkg} is not available in this interpreter.\n"
            f"  Install it automatically (do NOT ask the designer to run pip):\n"
            f'    "{sys.executable}" "{os.path.join(here, "ensure_deps.py")}" --for {group}')


def read_docx(path):
    try:
        import docx  # python-docx
    except ImportError:
        return _need("python-docx")
    try:
        d = docx.Document(path)
        parts = [p.text for p in d.paragraphs if p.text and p.text.strip()]
        # also pull table cell text (briefs often live in tables)
        for t in d.tables:
            for row in t.rows:
                cells = [c.text.strip() for c in row.cells if c.text and c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
        return "\n".join(parts)
    except Exception as e:
        return f"[error reading docx: {e}]"


def read_xlsx(path):
    try:
        import openpyxl
    except ImportError:
        return _need("openpyxl")
    try:
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        out = []
        for ws in wb.worksheets:
            out.append(f"=== Sheet: {ws.title} ===")
            for row in ws.iter_rows(values_only=True):
                vals = [str(v).strip() for v in row if v is not None and str(v).strip()]
                if vals:
                    out.append(" | ".join(vals))
        wb.close()
        return "\n".join(out)
    except Exception as e:
        return f"[error reading xlsx: {e}]"


def read_text(path):
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
        except Exception as e:
            return f"[error reading text: {e}]"
    return "[error reading text: could not decode]"


def extract(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        return "docx", read_docx(path)
    if ext in (".xlsx", ".xlsm", ".xls"):
        return "xlsx", read_xlsx(path)
    if ext in (".txt", ".md"):
        return "text", read_text(path)
    return "unsupported", ""


def gather(target):
    files = []
    if os.path.isdir(target):
        for root, _dirs, names in os.walk(target):
            for n in names:
                if os.path.splitext(n)[1].lower() in SUPPORTED:
                    files.append(os.path.join(root, n))
    elif os.path.isfile(target):
        files.append(target)
    return sorted(files)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) > 1 else 1)
    target = sys.argv[1]
    as_json = "--json" in sys.argv[2:]

    files = gather(target)
    if not files:
        msg = f"No supported files found in: {target} (supported: {', '.join(sorted(SUPPORTED))})"
        print(json.dumps({"error": msg}) if as_json else msg)
        sys.exit(0 if os.path.exists(target) else 1)

    results = []
    for fp in files:
        ftype, text = extract(fp)
        results.append({"file": fp, "type": ftype, "text": text})

    if as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"\n{'#' * 60}\n# FILE: {r['file']}  ({r['type']})\n{'#' * 60}")
            print(r["text"] if r["text"] else "[empty / unreadable]")


if __name__ == "__main__":
    main()
