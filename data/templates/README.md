# Templates folder

Excel templates, one per document type. This folder ships with three generic starter templates:

- `CG.xlsx` — for CG / cutscene briefs (includes a `Time | Requirements List` timeline-align block)
- `Lobby_Story_Login.xlsx` — shared by Main/Arena Lobby, Story, and Login briefs (same field set; only
  the `Music Type` value differs)
- `Feedback.xlsx` — revision feedback on a music studio's delivery (Stage 3B); has a
  `Time | Feedback` block for per-timestamp notes plus an overall-impression section

You can add more, or replace these with your own — see "Make your own" below.

## How a template is used
- Stage 2 (or 3B) lists the templates here and picks the right one for the document type.
- The chosen template's layout is detected by `scripts/build_requirement.py --inspect`, which also
  prints a copy-ready list of the JSON keys to use.
- The filler writes each requirement value into the cell to the right of its matching label,
  **preserving the template's formatting (fonts, row heights, widths, fills)** — so every doc of the
  same type comes out structurally identical and on-brand.

## Make your own (recommended for a new team)
The starter templates carry a specific house style. To match your own team's look, build a template
from one of your real documents — its font, sizes and layout are all kept:

```
python scripts/make_template.py --source <your_real_doc.xlsx> --out data/templates/<Type>.xlsx --clear-values
```

## Template conventions
- Column A = field labels (e.g. `Music Type` / `Duration` / `Order of Music` / `Requirement`).
- Column B = the value (placeholder text here is overwritten on fill).
- Keep label text stable — it becomes the key in the values JSON. A label may wrap across two lines
  (`Reference\nPicture`); matching is whitespace-insensitive, so the JSON key is the flat form
  (`"Reference Picture"`).
- For CG, keep the `Time | Requirements List` block; per-segment rows use labels like `0-Xs`.
- **Row heights are the design intent.** The filler only ever *grows* a row when its text needs more
  room, never shrinks it — so set each row to the height you actually want. Excel's hard maximum is
  409.5pt; the filler clamps to that and warns when content exceeds what one row can display.
- Don't edit these files with a script that calls openpyxl's `delete_rows` directly — it moves cell
  values but leaves row heights behind, which desynchronises every height below the cut.
