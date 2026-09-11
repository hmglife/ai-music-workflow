# Stage 2 — Requirement document (Excel) procedure

Goal: turn the designer's raw idea into a **polished, professional, template-conformant Excel**
requirement document, written in their voice (per the distilled profile).

The Excel structure must be **consistent** (driven by a template) while still letting you improve
clarity and layout — the designer isn't a document-formatting expert; you are.

---

## Step 1 — Confirm the brief
Collect the requirement from the user's message. Then fill gaps with **targeted** questions only —
mirror the question style in the distilled profile; don't interrogate.

Checklist of fields to nail down (skip ones already clear, adapt to the chosen template):
- 项目 / 模块 (project / module)
- 场景与用途 (scene & usage — e.g. CG 过场、主界面 Lobby、战斗)
- 情绪 / 基调 (mood / tone)
- 参考曲或参考风格 (reference track or reference style)
- 时长 (length)
- 结构 (structure — intro / loop / build / end …)
- 是否需要循环 & 循环方式 (loop? how it loops)
- 乐器 / 编制偏好 (instrument / instrumentation preferences)
- 交付格式 (deliverable format — wav/mp3, stems?, bpm?)
- 截止时间 (deadline)

Echo back a one-paragraph confirmed brief before generating, so the user can correct it.

### Reference materials (encouraged — and always archived)
The designer can attach a reference image (concept art, a key visual, or a **screenshot from a
reference video**), reference footage, or a temp track. Video content itself can't be read, so ask
for a still when the musical intent depends on what's on screen.

**Every provided file gets archived into the delivery folder** so the document ships with its
originals:
```bash
python <skill>/scripts/collect_assets.py \
  --out-dir <workspace>/output/<Project>_<Type>_<date> \
  --asset <each file or folder the designer gave> \
  --note "<path>=<what it is / what the music should take from it>"
```
Then reference the archived relative paths inside the brief (e.g. "录屏见 `Video/xxx.mp4`，
0:12 为重点同步点") and embed the key image at the Reference/Picture row (Step 4 `--image`), using the
**archived copy** so document and asset stay together. Files land in `Image/` `Video/` `Audio/`
`Other/` directly inside the delivery folder.

## Step 2 — Choose a template
Templates live in `data/templates/`. Different music types use different templates so the output
stays structurally consistent within each type.

**Formatting & fonts are inherited from the template.** Templates are real, formatted documents, so
filling one automatically preserves the designer's house font, font sizes, row heights, column
widths, fills and borders — do not re-style; just fill. (If you need a fresh template, build it from
one of the designer's real documents with `scripts/make_template.py`, which keeps all formatting.)

Templates are **two-column vertical layouts**: column A = field labels, column B = values
(placeholder text in B is overwritten on fill). The CG template additionally has a timeline-align
block: a `Time | Requirements List` header followed by per-segment rows (`0-Xs`, `X-Ys`, …) and a
`PS:` row — fill those by using the segment label (e.g. `"0-Xs"`) as a key in the values JSON.

> Default templates shipped (built from real briefs, formatting preserved):
> - `CG.xlsx` — CG / cutscene (includes the timeline-align block).
> - `Lobby_Story_Login.xlsx` — shared by Main/Arena Lobby, Story, and Login (same field set; only the
>   `Music Type` value differs). Save a type-specific copy if you want separate files.
> A new user can also distill their own and replace these — see `examples/sample_briefs/`.

1. List available templates. If several fit, ask which one (recommend based on the brief's scene).
2. Inspect the chosen template's structure with:
   ```bash
   python <skill>/scripts/build_requirement.py --inspect <skill>/data/templates/<name>.xlsx
   ```
   This prints the template's field layout (which cells / columns are the labels and where values go).

### If no suitable template exists (bootstrap)
- Ask the user to drop a template or a representative past document into `data/templates/`.
- If they give a past *document* rather than a blank template, convert it into a reusable template:
  keep the field labels and layout, clear the example values, save as `data/templates/<type>.xlsx`.
- Record the template's field map so `build_requirement.py` can fill it (see the script's
  `--inspect` output and the `templates/README.md` convention).

## Step 3 — Polish the content
Rewrite the requirement professionally:
- Follow the distilled profile for **voice, field set, and music-type conventions**.
- Follow the **template** for which fields must be present and their order.
- Improve clarity, fix vague descriptions, structure references properly, normalize terminology.
- Do not invent requirements the user didn't intend; mark assumptions explicitly if you must add any.

## Step 4 — Generate the Excel
Write the output into the **delivery folder in the user's current workspace** (the same folder
`collect_assets.py` archived the assets into), NOT inside the skill folder. Resolve `<workspace>` at
runtime; do not hardcode.
```bash
python <skill>/scripts/build_requirement.py \
  --template <skill>/data/templates/<name>.xlsx \
  --data <path-to-json-of-field-values> \
  --out <workspace>/output/<Project>_<Type>_<date>/<Project>_<Type>_<date>.xlsx \
  [--image <archived reference image>]
```
- Pass the polished field values as JSON (key = template field label, value = content). Labels match
  whitespace-insensitively, so a template label wrapped as `Reference\nPicture` is filled by the key
  `"Reference Picture"`. Run `--inspect` first if unsure — it prints a copy-ready key list.
- **Read the script's `[warn]` output.** `matched no template label` means a mistyped key (its value
  lands appended at the end, not in its row) — fix the key and re-run. A clamped-row warning means
  that field's text exceeds Excel's 409.5pt single-row limit; split the content or move detail into
  the timeline rows instead of leaving it truncated.
- The script fills the template, **preserving all of its formatting (incl. fonts)**, growing row
  heights only where wrapped text needs it, and writes to the path given in `--out`.
- `--image` embeds the reference image into the Reference/Picture row (scaled to fit column B and the
  row height). Use `--image-row N` if the template's layout differs.
- If you don't have a template yet and the user accepts a default layout, the script can emit a
  clean default two-column (Field / Content) sheet — but a real template is strongly preferred for
  structural consistency.

## Editing an already-generated doc later (via the local Office editor)

When the user asks to revise a field in a doc this skill already generated, and that file is open in
the host's local Tencent Docs preview (an `<active_document>`/`file_id` is injected), route the edit
through `tencent-docs-routing` → `tencent-local-office-edit` (a targeted cell write) instead of
re-running `build_requirement.py` — that keeps it in sync with the live preview the user is looking
at, and avoids re-embedding the image from scratch.

**Known quirk — row-shift after the local engine opens an openpyxl-built file.** The WPS/Tencent
local editor can silently split a wrapped two-line merged label (e.g. `Reference\nPicture`, one row
in the openpyxl template) into two separate rows the first time it opens/saves the file — pushing
every field below it down by one row. This has been observed to be **internally consistent** (labels,
values, and the embedded image all shift together, nothing gets mismatched or lost), but it means the
row indices from the original `--inspect` output go stale after the first local-editor round trip.
**Before writing to any cell in a doc that has already been opened/saved via the local editor once,
re-read the actual current label column (`sheet_get_cell_data` on column A) to find the live row
index — don't trust the original template's row numbers.**

## Step 5 — Present & confirm
Present the delivery as a package (result-presentation step): the generated Excel **and**
`ASSETS.md`, so the designer sees the archived materials too. Briefly note which template was used.
Ask whether anything needs adjusting.

**Then STOP** unless the user wants AI-music prompts. If unsure, ask:
> "需求文档已生成。需要我继续把它转成 AI 音乐提示词吗（Suno / Lyria / 其他）？"
