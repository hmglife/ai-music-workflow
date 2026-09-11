#!/usr/bin/env python3
"""Build a template-conformant Excel requirement / feedback document.

Filling a TEMPLATE preserves all of the template's formatting automatically — fonts (e.g. the
team's house font), row heights, column widths, fills and borders all come straight from the
template file. So the way to keep a designer's look-and-feel is simply: keep a real document as
the template (see make_template.py) and fill it here.

Modes:

  1) Inspect a template's structure (labels + the exact JSON keys to use):
       python build_requirement.py --inspect <template.xlsx>

  2) Fill a template with field values (formatting preserved), optionally embed a reference image:
       python build_requirement.py --template <template.xlsx> \
           --data <values.json> --out <output.xlsx> [--image <pic>] [--image-row <N>]

  3) Emit a clean default two-column sheet (Field / Content) when no template exists:
       python build_requirement.py --data <values.json> --out <output.xlsx>

`values.json` is a flat object whose keys match the template's column-A labels, e.g.
  {"Music Type": "...", "Duration": "...", "Requirement": "..."}

Label matching is whitespace-insensitive: a template label that wraps across two lines
("Reference\\nPicture") is matched by the plain key "Reference Picture". Any key that matches
nothing is appended at the end AND reported as a `[warn]`, so a silent typo can't hide.

LAYOUT POLICY — grow-only:
  Row heights from the template are treated as the designer's intent and are never shrunk.
  Each row is only *grown* when its wrapped text needs more room, estimated from the real font
  size of that cell and the real column width (CJK chars counted as double width). Heights are
  clamped to Excel's hard 409.5pt maximum, and rows past the last content row are left alone
  instead of being padded, so the sheet doesn't trail off into stretched empty rows.

Image embedding (--image):
  - The picture is placed in column B of the row whose column-A label contains both "reference"
    and "picture" (case-insensitive) — the standard Reference/Picture row in these briefs.
  - Override the target row with --image-row N if your template differs.
  - The image is scaled to fit that row's height and column B's width (aspect ratio kept).

Clean placeholders (--clean-placeholders):
  - Deletes rows whose value cell still holds an unfilled "<...>" placeholder. Handy for
    overall-mode feedback to drop the unused per-timestamp timeline rows.
  - Also removes a now-orphaned timeline block header (a `Time | ...` row whose segment rows
    were all just deleted), so overall-mode feedback leaves NO dangling `Time | Feedback` /
    `Time | Requirements List` row behind — no manual post-cleanup needed.
  - Row heights are shifted along with the deleted rows (openpyxl does NOT do this itself —
    it moves cell values but leaves `row_dimensions` behind, which silently desynchronises
    every height below the cut).

Dependencies: openpyxl (always); Pillow (only when --image is used).
"""
import sys
import json
import os
import re as _re
import math
import argparse
import unicodedata
from copy import copy
from datetime import datetime, date, time

# Excel's hard limit for row height, in points. Writing more produces a file Excel repairs.
MAX_ROW_H = 409.5
# Excel column-width units are defined against the workbook's default font (11pt).
BASE_FONT_PT = 11.0


def _dep_hint(pkg, group):
    """Point at the auto-installer, not at the designer.

    A raw `pip install` line is the wrong instruction twice over: the designer is not a Python user,
    and their shell `pip` may not even belong to the interpreter running this script — so following
    it can install into the wrong environment and the error survives.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    return (f"[missing dependency] {pkg} is not available in this interpreter.\n"
            f"  Install it automatically (do NOT ask the designer to run pip):\n"
            f'    "{sys.executable}" "{os.path.join(here, "ensure_deps.py")}" --for {group}')


def _load_openpyxl():
    try:
        import openpyxl  # noqa
        return openpyxl
    except ImportError:
        print(_dep_hint("openpyxl", "excel"))
        sys.exit(2)


def _norm(s):
    """Normalize a label for matching: collapse ALL whitespace (incl. newlines), drop colons.

    Template labels are often wrapped for looks ("Reference\\nPicture"); the JSON key the caller
    writes is the flat form ("Reference Picture"). Both must normalize to the same string.
    """
    t = str(s).replace("：", " ").replace(":", " ")
    t = _re.sub(r"\s+", " ", t).strip().lower()
    return t


def inspect(template_path):
    openpyxl = _load_openpyxl()
    wb = openpyxl.load_workbook(template_path)
    for ws in wb.worksheets:
        print(f"=== Sheet: {ws.title}  (dims {ws.dimensions}) ===")
        keys = []
        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None and str(cell.value).strip():
                    h = ws.row_dimensions[cell.row].height
                    extra = f"  [row h={h}]" if cell.column == 1 else ""
                    print(f"  {cell.coordinate}: {repr(cell.value)}{extra}")
            first = row[0] if row else None
            if first is not None and first.value is not None and str(first.value).strip():
                flat = _re.sub(r"\s+", " ", str(first.value)).strip()
                if flat not in keys:
                    keys.append(flat)
        print("\nUse these exact strings as keys in values.json:")
        print("  " + json.dumps(keys, ensure_ascii=False))
        print("  (labels that wrap across lines are matched by their single-line form)")


def _find_image_row(ws):
    """Row whose column-A label mentions both 'reference' and 'picture'."""
    for row in ws.iter_rows():
        a = row[0] if row else None
        if a is not None and a.value:
            t = str(a.value).lower()
            if "reference" in t and "picture" in t:
                return a.row
    return None


def _last_content_row(ws):
    """Last row that actually holds text in column A or B (ws.max_row over-reports)."""
    last = 0
    for r in range(1, ws.max_row + 1):
        for c in (1, 2):
            v = ws.cell(row=r, column=c).value
            if v is not None and str(v).strip():
                last = r
                break
    return last


# --------------------------------------------------------------------------- heights


def _text_units(s):
    """Text width in column-width units: CJK/full-width char = 2, everything else = 1."""
    u = 0.0
    for ch in s:
        u += 2.0 if unicodedata.east_asian_width(ch) in ("W", "F") else 1.0
    return u


def _col_width_units(ws, col_idx):
    from openpyxl.utils import get_column_letter
    w = ws.column_dimensions[get_column_letter(col_idx)].width
    return w if w else 8.43  # Excel default


def _font_pt(cell):
    try:
        sz = cell.font.size
        return float(sz) if sz else BASE_FONT_PT
    except (TypeError, ValueError, AttributeError):
        return BASE_FONT_PT


def _wrapped_lines(text, col_units, font_pt):
    """Estimated wrapped line count for `text` in a column of `col_units`, at `font_pt`.

    A bigger font fits fewer characters in the same physical column, so the usable capacity is
    scaled by BASE_FONT_PT / font_pt. Explicit newlines always break a line.
    """
    if text is None:
        return 1
    capacity = max(2.0, col_units * (BASE_FONT_PT / max(font_pt, 1.0)))
    total = 0
    for seg in str(text).split("\n"):
        seg = seg.rstrip()
        total += max(1, math.ceil(_text_units(seg) / capacity)) if seg else 1
    return total


def _autofit_row_heights(ws, base_heights, min_h=22.0, reserve_img_row=None, img_row_h=200.0):
    """Grow row heights so wrapped text in columns A/B stays fully visible.

    Grow-only: the template's own height for a row is a floor, never overwritten downwards, so the
    designer's house layout survives. Text that genuinely needs more room raises the row, clamped
    to Excel's MAX_ROW_H. Rows past the last content row are left untouched (no stretched blanks).
    """
    from openpyxl.styles import Alignment
    last = _last_content_row(ws)
    unitsA = _col_width_units(ws, 1)
    unitsB = _col_width_units(ws, 2)
    overflow = []

    for r in range(1, last + 1):
        a = ws.cell(row=r, column=1)
        b = ws.cell(row=r, column=2)
        for c in (a, b):
            al = c.alignment
            c.alignment = Alignment(horizontal=al.horizontal, vertical=al.vertical or "top",
                                    wrap_text=True, text_rotation=al.text_rotation,
                                    indent=al.indent)
        lines_a = _wrapped_lines(a.value, unitsA, _font_pt(a))
        lines_b = _wrapped_lines(b.value, unitsB, _font_pt(b))
        # Line pitch tracks the real font size of the cell that drives the line count.
        pitch_a = _font_pt(a) * 1.45
        pitch_b = _font_pt(b) * 1.45
        need = max(lines_a * pitch_a, lines_b * pitch_b) + 4.0

        floor_h = base_heights.get(r) or min_h
        h = max(floor_h, need, min_h)
        if reserve_img_row and r == reserve_img_row:
            h = max(h, img_row_h)
        if h > MAX_ROW_H:
            if need > MAX_ROW_H:
                overflow.append(r)
            h = MAX_ROW_H
        ws.row_dimensions[r].height = round(h, 1)

    # Never leave inherited height on trailing blank rows — that's what makes a doc look padded.
    # (`customHeight` is a read-only derived property in openpyxl; clearing `height` is enough.)
    for r in range(last + 1, ws.max_row + 1):
        if ws.row_dimensions[r].height is not None:
            ws.row_dimensions[r].height = None

    if overflow:
        print(f"[warn] row(s) {overflow} hold more text than Excel's {MAX_ROW_H}pt row limit can "
              f"show; height clamped. Consider splitting that content or widening column B.")
    return last


def _delete_rows_keep_heights(ws, row, amount=1):
    """Delete rows AND shift row heights up with them.

    openpyxl's delete_rows moves cell values but leaves `row_dimensions` indexed as before, so
    every height below the cut ends up attached to the wrong row. This wrapper re-maps them.
    """
    heights = {r: ws.row_dimensions[r].height for r in range(1, ws.max_row + 1)}
    top = max(heights) if heights else 0
    ws.delete_rows(row, amount)
    new_h = {}
    for r, h in heights.items():
        if r < row:
            new_h[r] = h
        elif r >= row + amount:
            new_h[r - amount] = h
    for r in range(1, top + 1):
        ws.row_dimensions[r].height = new_h.get(r)


def _delete_placeholder_rows(ws, protect_rows=None):
    """Delete rows whose value cell (col B) is still an unfilled '<...>' placeholder.

    Useful e.g. for overall-mode feedback: drop the unused per-timestamp timeline rows.
    `protect_rows` (set of row indexes) is never deleted, and it MUST contain every row this run
    actually wrote a value into. A designer's real text can legitimately be wrapped in angle
    brackets (e.g. "<整体不错，但副歌太满>"); without that protection it would look like an
    unfilled placeholder and be silently dropped. Deletes bottom-up so indexes stay valid, and
    carries row heights along via _delete_rows_keep_heights.

    After dropping placeholder rows, any section header that has become orphaned (a `Time | <X>`
    style block header with no data rows left under it) is removed too, so overall-mode feedback
    doesn't leave a dangling `Time | Feedback` / `Time | Requirements List` row behind.
    """
    protect = protect_rows or set()
    to_del = []
    for r in range(1, ws.max_row + 1):
        if r in protect:
            continue
        b = ws.cell(row=r, column=2).value
        if isinstance(b, str):
            t = b.strip()
            if t.startswith("<") and t.endswith(">"):
                to_del.append(r)
    for r in sorted(to_del, reverse=True):
        _delete_rows_keep_heights(ws, r, 1)
    n = len(to_del)
    # Drop orphaned timeline block headers (col A == 'Time') whose data rows are now all gone.
    n += _delete_orphan_block_headers(ws, protect_rows=protect)
    return n


# A timeline segment label encodes a time range/point: '0-Xs', 'X-Ys', 'Y-Zs', '0-9s', '10-25s',
# '1:12', or the trailing 'PS:' note row. Real field labels ('Notes', 'Requirement', 'Time', …)
# must NOT match — they end the block.
_SEG_PAT = _re.compile(r"^(ps\s*[:：]?|[\dxyz][\dxyz:.\-]*\s*s?|\d+\s*[:：]\s*\d+.*)$", _re.IGNORECASE)


def _is_segment_label(val):
    if not isinstance(val, str):
        return False
    t = val.strip()
    if not t:
        return False
    return bool(_SEG_PAT.match(t))


def _delete_orphan_block_headers(ws, protect_rows=None):
    """Remove a `Time | ...` block header row that no longer has any segment rows beneath it.

    A timeline block is a header row whose col-A label is exactly 'Time' (the CG requirement's
    `Time | Requirements List` or the feedback `Time | Feedback`). If every row below it (until the
    next labelled block, or end of sheet) is empty in column B, the header is now meaningless and
    is deleted. Skips any row in `protect_rows`. Works bottom-up so indexes stay valid.
    """
    protect = protect_rows or set()
    headers = []
    for r in range(1, ws.max_row + 1):
        a = ws.cell(row=r, column=1).value
        if isinstance(a, str) and a.strip().lower() == "time":
            headers.append(r)
    # We scan only the rows belonging to THIS header's block: from hr+1 until the next field label
    # (a non-segment col-A label such as 'Notes' / 'Requirement' ends the block).
    to_del = []
    for hr in headers:
        if hr in protect:
            continue
        has_data = False
        for r in range(hr + 1, ws.max_row + 1):
            a = ws.cell(row=r, column=1).value
            # Stop at the next real field label (not a timeline segment) — block ends here.
            if isinstance(a, str) and a.strip() and not _is_segment_label(a):
                break
            b = ws.cell(row=r, column=2).value
            if isinstance(b, str) and b.strip():
                has_data = True
                break
        if not has_data:
            to_del.append(hr)
    for r in sorted(to_del, reverse=True):
        _delete_rows_keep_heights(ws, r, 1)
    return len(to_del)


# --------------------------------------------------------------------------- image


def _embed_image(ws, img_path, row):
    try:
        from openpyxl.drawing.image import Image as XLImage
    except ImportError:
        print(_dep_hint("Pillow", "image"))
        return False
    try:
        from PIL import Image as _PIL  # noqa  (openpyxl needs Pillow present)
    except ImportError:
        print(_dep_hint("Pillow", "image"))
        return False
    if not os.path.isfile(img_path):
        print(f"[warn] image not found, skipped: {img_path}")
        return False

    from openpyxl.utils import get_column_letter
    # Clear any placeholder text in the value cell so it doesn't show behind the image.
    vcell = ws.cell(row=row, column=2)
    if isinstance(vcell.value, str) and vcell.value.strip().startswith("<"):
        vcell.value = None
    try:
        pic = XLImage(img_path)
    except Exception as e:
        print(f"[warn] could not read image ({e}); skipped: {img_path}")
        return False
    # Scale to fit the target row height (Excel row height in points; ~1.333 px/pt) AND the width
    # of column B, keeping aspect ratio, so it never overflows onto neighbouring text.
    rh = ws.row_dimensions[row].height
    max_h = int(min(rh or 200.0, MAX_ROW_H) * 1.3)
    bw = ws.column_dimensions[get_column_letter(2)].width or 70
    max_w = int(bw * 7)  # ~7 px per Excel width unit
    if pic.width and pic.height:
        ratio = min(max_h / pic.height, max_w / pic.width, 1.0)
        if ratio < 1.0:
            pic.height = int(pic.height * ratio)
            pic.width = int(pic.width * ratio)
    ws.add_image(pic, f"B{row}")
    return True


# --------------------------------------------------------------------------- fill


def _copy_style(dst, src):
    try:
        dst._style = copy(src._style)
    except Exception:
        pass


def _write_value(ws, row, col, val):
    """Write a value into a cell, coercing it and neutralising inherited date formats.

    Several template cells (e.g. the `Submit Time` value cell, and the `Time` block header) carry a
    `mm-dd-yy` number format left over from the original documents. Writing a plain number like
    2026 into such a cell makes Excel render it as a DATE (1905-07-18), silently corrupting the
    content. These briefs never need real date arithmetic — the dates are text like "2026-08-20" —
    so any cell we fill gets a General format unless the value really is a date/time object.
    """
    cell = ws.cell(row=row, column=col)
    cell.value = _to_cell_value(val)
    if not isinstance(cell.value, (datetime, date, time)):
        fmt = (cell.number_format or "").lower()
        if fmt != "general" and any(ch in fmt for ch in ("y", "d", "h", "s")):
            cell.number_format = "General"
    return cell


def _to_cell_value(val):
    """Coerce a JSON value into something Excel accepts, without losing information.

    openpyxl rejects lists/dicts outright (ValueError: Cannot convert ... to Excel), which used to
    surface as a raw traceback. Lists are the common case — a caller naturally writes
    ["点1", "点2"] for a multi-point requirement — so join them into newline-separated lines
    (the wrap-text layout already renders that correctly).
    """
    if val is None:
        return None
    if isinstance(val, bool):
        return "Yes" if val else "No"
    if isinstance(val, (int, float, str)):
        return val
    if isinstance(val, (list, tuple)):
        return "\n".join(_flatten_lines(val))
    if isinstance(val, dict):
        return "\n".join(f"{k}: {_to_cell_value(v)}" for k, v in val.items())
    return str(val)


def _flatten_lines(seq):
    out = []
    for item in seq:
        if isinstance(item, (list, tuple)):
            out.extend(_flatten_lines(item))
        else:
            v = _to_cell_value(item)
            out.append("" if v is None else str(v))
    return out


def fill_template(template_path, values, out_path, image=None, image_row=None, clean=False):
    openpyxl = _load_openpyxl()
    if not os.path.isfile(template_path):
        print(f"[error] template not found: {template_path}")
        print("        Check the path, or list the available ones in data/templates/.")
        sys.exit(2)
    try:
        wb = openpyxl.load_workbook(template_path)
    except Exception as e:
        print(f"[error] could not open template ({e}): {template_path}")
        print("        Is it a real .xlsx? (.xls / .et are not supported — re-save as .xlsx)")
        sys.exit(2)
    ws = wb.active

    # The template's own row heights are the designer's intent — capture them BEFORE any edit so
    # autofit can use them as floors instead of replacing them with estimates.
    base_heights = {r: ws.row_dimensions[r].height for r in range(1, ws.max_row + 1)}

    # Labels come from the FIRST column only, so placeholder text in the value column can never be
    # mistaken for a label. Values are written into column B on the SAME row (overwriting any
    # placeholder) — the vertical label|value layout these briefs use. All template formatting
    # (fonts, row heights, widths, fills) is inherited from the template untouched.
    label_cells = {}
    for row in ws.iter_rows():
        first = row[0] if row else None
        if first is not None and first.value is not None and str(first.value).strip():
            label_cells.setdefault(_norm(first.value), first)

    used_keys = set()
    # Every row this run wrote into. These must survive --clean-placeholders even if the value
    # happens to look like a "<...>" placeholder (real feedback can be written that way).
    written_rows = set()
    for key, val in values.items():
        nk = _norm(key)
        if nk in label_cells:
            lc = label_cells[nk]
            _write_value(ws, lc.row, lc.column + 1, val)
            used_keys.add(key)
            written_rows.add(lc.row)

    leftover = [(k, v) for k, v in values.items() if k not in used_keys]
    if leftover:
        print(f"[warn] {len(leftover)} key(s) matched no template label and were appended at the "
              f"end: {[k for k, _ in leftover]}")
        print("       Run --inspect on the template and use the exact label strings it prints.")
        start = _last_content_row(ws) + 2
        style_a = label_cells[next(iter(label_cells))] if label_cells else None
        style_b = ws.cell(row=style_a.row, column=2) if style_a else None
        for i, (k, v) in enumerate(leftover):
            ca = ws.cell(row=start + i, column=1, value=k)
            cb = _write_value(ws, start + i, 2, v)
            written_rows.add(start + i)
            if style_a is not None:
                _copy_style(ca, style_a)
            if style_b is not None:
                _copy_style(cb, style_b)

    # Never clean a row this run filled in; also protect the Reference/Picture row when an image
    # will be embedded there.
    protect = set(written_rows)
    if image:
        pre = image_row or _find_image_row(ws)
        if pre:
            protect.add(pre)

    # Clean unfilled '<...>' placeholder rows (optionally), protecting the image row.
    cleaned = 0
    if clean:
        # Row indexes shift while cleaning, so heights must be re-read afterwards.
        cleaned = _delete_placeholder_rows(ws, protect_rows=protect)
        base_heights = {r: ws.row_dimensions[r].height for r in range(1, ws.max_row + 1)}

    # Re-resolve the image target AFTER cleaning (row indexes may have shifted).
    img_target = None
    if image:
        img_target = image_row if image_row else _find_image_row(ws)

    # Grow row heights where wrapped text needs it, keeping the template's heights as floors.
    _autofit_row_heights(ws, base_heights, reserve_img_row=img_target)

    embedded = False
    if image:
        if img_target:
            embedded = _embed_image(ws, image, img_target)
            if embedded:
                print(f"[image] embedded into B{img_target}")
        else:
            print("[image] no Reference/Picture row found; pass --image-row N to place it")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    wb.save(out_path)
    print(f"[ok] wrote {out_path} (matched {len(used_keys)} fields, "
          f"appended {len(leftover)} unmatched"
          f"{', cleaned %d placeholder rows' % cleaned if cleaned else ''}"
          f"{', image embedded' if embedded else ''})")


def default_sheet(values, out_path):
    openpyxl = _load_openpyxl()
    from openpyxl.styles import Font, Alignment, PatternFill
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Music Requirement"

    ws["A1"] = "Field"
    ws["B1"] = "Content"
    head_fill = PatternFill("solid", fgColor="D9E1F2")
    for c in ("A1", "B1"):
        ws[c].font = Font(bold=True)
        ws[c].fill = head_fill
        ws[c].alignment = Alignment(vertical="center")

    r = 2
    for k, v in values.items():
        ws.cell(row=r, column=1, value=k).alignment = Alignment(vertical="top", wrap_text=True)
        cell = ws.cell(row=r, column=2, value=_to_cell_value(v))
        cell.alignment = Alignment(vertical="top", wrap_text=True)
        r += 1

    ws.column_dimensions["A"].width = 18
    ws.column_dimensions["B"].width = 64
    # Same grow-only autofit so long requirement bodies are readable here too.
    _autofit_row_heights(ws, {}, min_h=20.0)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    wb.save(out_path)
    print(f"[ok] wrote default sheet {out_path} ({len(values)} fields)")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--inspect")
    ap.add_argument("--template")
    ap.add_argument("--data")
    ap.add_argument("--out")
    ap.add_argument("--image", help="optional reference image to embed")
    ap.add_argument("--image-row", type=int, help="row number to place the image (override)")
    ap.add_argument("--clean-placeholders", action="store_true",
                    help="delete rows whose value is still an unfilled '<...>' placeholder "
                         "(e.g. drop unused timeline rows in overall-mode feedback)")
    args = ap.parse_args()

    if args.inspect:
        if not os.path.isfile(args.inspect):
            print(f"[error] template not found: {args.inspect}")
            sys.exit(2)
        inspect(args.inspect)
        return

    if not args.data or not args.out:
        ap.error("--data and --out are required (unless using --inspect)")

    if not os.path.isfile(args.data):
        print(f"[error] data file not found: {args.data}")
        sys.exit(2)
    try:
        with open(args.data, "r", encoding="utf-8") as f:
            values = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[error] {args.data} is not valid JSON: {e}")
        sys.exit(2)
    if not isinstance(values, dict):
        print(f"[error] {args.data} must contain a JSON object mapping template labels to values, "
              f"got {type(values).__name__}.")
        sys.exit(2)
    if not values:
        print("[warn] the data file is an empty object — the output will just be the blank "
              "template.")

    if args.template:
        fill_template(args.template, values, args.out, image=args.image,
                      image_row=args.image_row, clean=args.clean_placeholders)
    else:
        default_sheet(values, args.out)


if __name__ == "__main__":
    main()
