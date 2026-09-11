# Stage 3B — Feedback document (for studio-produced music)

Use this when the music is made by a **professional music studio** (not AI), and the designer has
listened to the studio's delivery and needs to write **revision feedback** back to the studio.

Goal: turn the designer's listening reactions into a **structured, professional, actionable**
feedback document (Excel) in *their* voice (per the distilled profile) — consistent in look with their
requirement documents.

This is a sibling of 3A (AI prompts). Choose 3B when the producer is a human studio, not an AI tool.

---

## Step 1 — Anchor the feedback to a track
- Identify which delivery this is about. If the Stage-2 requirement Excel exists, reference it
  (project / character / type / the original target) so the feedback reads in context.
- Note the version (e.g. "v1 / first draft / oneshot") — studios iterate, so versioning matters.

## Step 2 — Collect the designer's reactions, and pick the feedback mode
Ask for, or read from the message, the designer's reactions to the track. Then decide the **mode**
automatically from what they give you:

- **Per-timestamp mode** — when the designer gives notes tied to moments ("0-9s 太单薄", "副歌进得太
  早", "1:12 的铜管该收一点"), and especially for **CG** music that must hit picture. They may also
  attach **screenshots** of the moment. → Use a timeline feedback layout (per-segment rows), like
  the CG requirement's `Time | Requirements List` block.
- **Overall mode** — when the feedback is holistic ("整体太商业""氛围不够压迫""混音偏闷"), typical for
  Lobby / Story / Login. → Use an overall feedback section.

If they give both, support both (overall summary + per-timestamp rows). If unsure which, ask one
short question: "你是想按时间点逐段给意见，还是整体说一下感受？"

## Step 3 — Make each note specific and actionable
Vague feedback wastes a studio round-trip. For each point, push toward: **what's off → the target →
a reference if any**. Examples of the shape to aim for (in the designer's voice/language):
- ❌ "不好听" → ✅ "副歌的弦乐太满，盖住了主题动机；想要更通透，参考 intro 的留白处理。"
- ❌ "节奏怪" → ✅ "0:18 的过渡有点拖，建议提前 1 小节进鼓，和画面切镜对齐。"
Keep the designer's habit of also stating **what already works well** (most briefs in `profile.md`
are encouraging + give creative freedom) — lead with a short overall impression, then specifics.

Follow the distilled profile for tone, language (e.g. English to the studio), and terminology.

## Step 4 — Archive the materials, then generate the Excel

First archive everything the designer handed over — the studio's delivered audio file, timestamp
screenshots, any reference track used to explain a note — into the delivery folder:
```bash
python <skill>/scripts/collect_assets.py \
  --out-dir <workspace>/output/<Project>_<Type>_feedback_v<N>_<date> \
  --asset <studio delivery / screenshots / reference tracks> \
  --note "<path>=<what it is / which note it illustrates>"
```
Archiving the **studio's delivered track** matters most here: the feedback only makes sense next to
the version it critiques, and v2 review needs v1 on hand.

Use the feedback template (ships at `data/templates/Feedback.xlsx`; same house style/fonts as the
requirement templates). Inspect its layout first if unsure:
```bash
python <skill>/scripts/build_requirement.py --inspect <skill>/data/templates/Feedback.xlsx
```
Fill it and write into the **same delivery folder** (NOT the skill folder):
```bash
python <skill>/scripts/build_requirement.py \
  --template <skill>/data/templates/Feedback.xlsx \
  --data <values.json> \
  --out <workspace>/output/<Project>_<Type>_feedback_v<N>_<date>/<Project>_<Type>_feedback_v<N>_<date>.xlsx \
  [--image <archived screenshot>]
```
- Meta fields (project / type / version / overall impression) fill by label. Labels match
  whitespace-insensitively; `--inspect` prints the exact keys to use.
- **Per-timestamp rows**: the template has a `Time | Feedback` block; fill segment rows by using the
  segment label (e.g. `"0-9s"`) as a JSON key, like the CG requirement timeline. You can also rename
  the placeholder segment labels (`0-Xs`…) to the real timestamps.
- **Overall mode**: don't fill the timeline rows; add `--clean-placeholders` to drop the unused
  `<...>` rows so the doc stays clean (just meta + overall impression + notes). The script also
  removes the now-orphaned `Time | Feedback` header automatically and keeps every remaining row's
  height correctly aligned, so no manual cleanup is needed.
- `--image` embeds a referenced screenshot into the Reference/Picture row — pass the **archived**
  copy so the doc and its asset stay together.
- Reference the archived paths inside the notes (e.g. "对比 `Audio/v1_delivery.wav` 的 0:18").
  Assets live in `Image/` `Video/` `Audio/` `Other/` directly inside the delivery folder.
- Heed any `[warn]` about unmatched keys (a typo — the value gets appended at the end) or a clamped
  row (text longer than one Excel row can display; split it).

If `Feedback.xlsx` is missing, build it once from a requirement template with `make_template.py`
(it keeps fonts/format), or fall back to the default two-column sheet — but a real template is
preferred for consistency.

## Step 5 — Present & confirm
Present the delivery (feedback Excel + `ASSETS.md`) via the result-presentation step. Note the
version and mode used. Ask whether anything needs adjusting before it goes to the studio.

## Notes
- This branch does **not** use the AI adapters or `data/feedback/` (that folder is for tuning AI
  prompt rules, a different thing). Studio feedback documents are deliverables → user's workspace.
- Across revision rounds, bump the version (v1 → v2) and, if helpful, keep prior feedback context so
  the studio can see what changed.
