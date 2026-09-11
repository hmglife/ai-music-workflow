# Document channels — which tool produces which file

This skill produces deliverables in more than one format. Two channels exist, and picking the wrong
one silently damages the deliverable. The rules below are **based on measured behaviour**, not
assumptions — re-verify before changing them.

---

## The two channels

| Channel | What it is | Use it for |
|---|---|---|
| **Template filler** | `scripts/build_requirement.py` + `openpyxl` | The Excel requirement / feedback documents — the skill's core deliverables |
| **Host Office channel** | WorkBuddy's built-in local Office editing (`edsdk.py`) | Word, PPT, and any other local Office format; edits to an existing file |

Both preserve a template's formatting. The split is **not** about quality — it is about one
measured incompatibility, below.

---

## The one hard rule: images in Excel

**Excel images must go through the template filler (`build_requirement.py --image`).**

Measured difference in how each channel stores a picture in a workbook:

| Channel | Storage | Cell XML | Opens correctly in |
|---|---|---|---|
| `build_requirement.py --image` | `xl/media/` + drawing anchor | normal | **Every** Excel / WPS / preview |
| host `sheet_insert_image` | `xl/richData/media/` (Excel-365 "image in cell") | `t="e" vm="1"` → `<v>#VALUE!</v>` | Only Excel 365 / compatible viewers |

The requirement document is emailed to an outside music studio. If they open it in an older Excel,
in WPS, or in a mail preview, a rich-data image renders as **`#VALUE!`** — the Reference/Picture row
would show an error instead of the concept art. That is unacceptable for a deliverable, so:

- Reference/Picture in a **requirement / feedback Excel** → `build_requirement.py --image <path>`.
- `sheet_insert_image` is acceptable only when the user explicitly wants an in-cell image in a
  workbook that is not going out to the studio.

Word and PPT have no such problem: the host channel writes `word/media/` and `ppt/slides/media/`,
i.e. ordinary embedded pictures that open everywhere. **Images in Word/PPT go through the host
channel normally.**

---

## Producing Word / PPT / other formats

The designer may want the same brief as a Word doc (to paste into a wiki) or a PPT (to present the
plan). Build the content exactly as Stage 2 / 3B would — same brief confirmation, same profile-driven
polish, same asset archiving — then produce the file through the host channel, writing it into the
**same delivery folder** next to the archived assets.

The host channel handles three categories, detected from the file's content (extension is a
fallback):

| Category | Extensions |
|---|---|
| doc | `.doc` `.dot` `.wps` `.wpt` `.docx` `.dotx` `.docm` `.dotm` |
| sheet | `.xls` `.xlt` `.xlsx` `.xltx` `.xlsm` `.xltm` `.csv` `.tsv` |
| slide | `.ppt` `.pps` `.pot` `.pptx` `.ppsx` `.potx` `.pptm` `.ppsm` `.potm` |

Not supported: `.et` `.ett` `.dps` `.dpt` (ask the user to re-save as `.xlsx` / `.pptx`); `.pdf` and
`.ofd` are view-only. Macro-enabled files open, but macros do not run.

### Working with the host channel

Locate the tool wrapper at runtime — it lives with the host's local-office skill, not in this skill.
Then follow that skill's own documented flow. The essentials:

1. **Create or open.** `create_doc` / `create_sheet` / `create_slide` for a new file; `open_file` for
   an existing one. Use the `file_id` the tool returns — never invent one from a path.
   If a document is already open (the host may inject a live `file_id`, or `get_pool_status` lists
   it), reuse that instead of opening a second instance.
2. **Query the schema before every editing call**: `edsdk.py schema <tool>`. Do not guess parameters
   from a one-line summary — several tools take nested objects, and the tool names are not always
   what you would guess. Concrete examples are listed under rule 4.
3. **Save** with `save_file` (pass `file_path` to save somewhere else). Do **not** call `close_file`
   on a document the user is viewing.
4. **Custom templates work — but fill them by replacing placeholders.** Measured on a `.docx` whose
   heading run was 腾讯体 W7 / 22pt / bold / `#1F3B73`:

   | How the text was written | Result |
   |---|---|
   | `doc_find` the placeholder, then `doc_replace_text` over its range | new text keeps 腾讯体 W7 / 14pt / bold / `#1F3B73` ✓ |
   | `doc_insert_text` at an index past the existing content | lands in a **new, unstyled** paragraph (`font=None`) ✗ |

   Existing content is never damaged either way, but inserted text does **not** inherit a nearby
   run's formatting. So for a house-style Word/PPT template, write placeholders into the styled runs
   and fill by find-and-replace — same principle as the Excel template filler. Use
   `doc_insert_text` only for a document being built from scratch, where there is no style to match.

   Call shapes that cost a round-trip when guessed (hence rule 2):
   - `doc_replace_text` takes `ranges: [{begin, end}]` **and** a separate top-level `text` — not
     `text` inside each range, and not flat `begin`/`end`.
   - `sheet_set_cell_value` takes a `cell` object (`{row, col, value_type, string_value}`).
   - Adding a textbox to a slide is `slide_add_text`, not `slide_insert_text`.

5. **Multi-paragraph content: do not use `doc_insert_text`.** It rejects newlines outright —
   `text contains a placeholder/control character (code=10)`. A brief is inherently multi-section,
   so build it one of these two ways instead:

   | Tool | Notes |
   |---|---|
   | `doc_insert_markdown` | Best fit for a whole brief. **`idx` must be ≥ 0** (it rejects `-1`, unlike the paragraph tool). Markdown tables become **real Word tables** — measured: a 4×2 timeline table came through intact, which is exactly what the CG timeline block needs. |
   | `doc_insert_paragraph_with_text` | One paragraph per call, accepts `idx=-1` for "at the very start", and returns `end_index` to chain the next call. Use when you need per-paragraph heading levels or list numbering. |

   Reserve `doc_insert_text` for appending a single inline run with no line breaks.

### Visual check (optional)

`doc_to_image` renders a `.docx` to per-page PNGs. Useful to confirm layout after a batch of edits.
Call it once at the end, not after every edit.

---

## Never hand the core deliverable to generic document routing

The host also ships generic routing that wants to claim anything matching "生成 / 制作 / 新建 /
整理成 Excel" with no source spreadsheet — which describes this skill's Stage 2 exactly. Those
generic generators build a workbook **from scratch** with their own styling and never read
`data/templates/`, so the designer's house font and row heights would be silently lost.

Producing this skill's requirement / feedback document therefore stays with the template filler.
Generic routes remain fine for a genuinely different job the user asks for on a finished file
(e.g. "帮我在这个表里做个数据透视").
