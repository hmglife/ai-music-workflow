---
name: ai-music-workflow
description: A complete workflow for audio/music designers. It (1) distills the designer's own past requirement docs into a reusable personal profile (working style + aesthetic + how they write briefs), (2) turns a new music idea into a polished, template-conformant Excel requirement document, and (3) takes that requirement forward two ways — either generate accurate prompts for AI music tools (Suno, Lyria 3, or any new tool via a pluggable adapter) and tune them by feedback, OR, when the music is produced by a professional music studio instead of AI, write a structured feedback document (Excel) after the designer listens to the studio's delivery. Use when the user wants to plan music, write a music requirement document, generate AI-music prompts, or write a feedback document on a studio's music. The stages are independent — stop at whichever one the user needs.
agent_created: true
author: hmglife
version: "1.0.0"
---

# AI Music Workflow

A reusable workflow built for **audio / music designers (音频策划)**. It learns one designer's
personal style once, then helps them go from a raw idea → a clean requirement document →
accurate AI-music prompts on any platform.

This skill is designed to be **packaged and shared** with other audio designers. Everything a
specific designer generates (their profile, their templates, their drafts) lives under `data/`,
which ships empty so each new user starts clean and builds their own.

---

## How to talk to the user (keep the machinery invisible)

The internal structure (stage numbers like "Stage 3B", the profile-gate, adapters, scripts,
feedback files) is **for you, not for the user**. To the audio designer it should feel like a
natural, capable collaborator — not a state machine narrating its own steps.

- **Never expose internal labels.** Don't say "这是 Stage 3B" / "进入阶段二" / "触发画像门控" /
  "调用 build_requirement.py". Just do the thing and talk about the work in human terms
  (e.g. "收到，你是听了音乐公司的成品想写修改反馈对吧？我确认两点就帮你整理成反馈文档。").
- **Don't announce mechanics.** No "我先检查是否存在 profile.md"; instead, if you haven't learned
  their style yet, say it naturally: "我还没熟悉你的写法，先看几份你以前的需求会更贴你的风格。"
- **Ask like a colleague, not a form.** Confirm the few things you genuinely need, in their language,
  without listing your internal checklist.
- **Stay results-first.** Lead with what you produced or need; keep any process talk to a minimum.
- It's fine to be transparent if the user *asks* how it works — then explain plainly. By default,
  keep it seamless.

---

## The stages (each is an independent stop point)

```
Stage 1  Distill profile   →  Stage 2  Requirement doc  →  Stage 3  Take it forward
  (learn the designer)         (idea → Excel)               ├─ 3A  AI-music prompts (Suno / Lyria / …)
                                                            └─ 3B  Feedback doc (studio-produced music → Excel)
```

Stage 3 has **two branches** depending on who makes the music:
- **3A — AI tools**: generate platform-accurate prompts and tune them by feedback.
- **3B — Professional studio**: the requirement is sent to a music studio (not AI); after the
  designer listens to the studio's delivery, write a structured **feedback document** (Excel).

**CRITICAL — do only what the user asked.** Read the user's request and decide the target:

| User intent | Run | Then stop after |
|---|---|---|
| "学习我的风格 / 蒸馏我的资料 / 重新蒸馏" | Stage 1 | Stage 1 |
| "帮我写需求文档 / 把这个需求整理成 Excel" | (ensure Stage 1) → Stage 2 | **Stage 2** |
| "给我生成 Suno/Lyria 提示词 / 这个需求怎么做成音乐" | (ensure Stage 1) → (Stage 2 if no doc) → **3A** | Stage 3A |
| "我听了音乐公司做的成品，帮我写反馈 / 写修改意见" | (ensure Stage 1) → **3B** | Stage 3B |
| "从头到尾走一遍" | 1 → 2 → 3A | Stage 3A |

Distinguish 3A vs 3B by **who produced the music**: AI tool → 3A; a human studio's delivered file
that the designer has listened to → 3B. If the user says "写反馈/修改意见" and it's clearly about a
studio's finished track (not an AI prompt result), go to **3B**.

Do **not** silently continue past what was asked. After Stage 2, if unsure, ask:
"需求文档已生成。接下来是要生成 AI 提示词，还是这首交给音乐公司做、之后我帮你写反馈文档？"

---

## Dependencies: handle them yourself, never make the designer install anything

The user of this skill is an **audio designer, not a Python user**. "Run `pip install openpyxl`" is a
wall at step one, and it is also frequently the *wrong* instruction: the interpreter running these
scripts is often a host-managed one, so whatever `pip` resolves to in the designer's own shell may
install into a different environment and leave the error in place.

So dependency management is **your job, silently**:

1. Before the first script run of a session (or the moment a script reports a missing dependency),
   run the installer with **the same interpreter you use for the other scripts**:
   ```bash
   python <skill>/scripts/ensure_deps.py --for excel   # or: image | word | all
   ```
   It installs into `sys.executable`, skips what is already present, and is safe to re-run.
2. Then retry the original command. Do not report the missing-dependency step to the designer at
   all — it is plumbing, and narrating it just makes the tool feel fragile.
3. **If installation genuinely fails** (no pip, no network, locked-down environment), do not relay
   the raw pip command as a to-do. Say in plain language what is degraded and offer the path
   forward — e.g. "参考图这次没能嵌进去，文档其他部分都正常，我把图放在交付夹的 `Image/` 里了"
   (a missing `Pillow` only costs the embedded image; the document itself still generates).

Only `openpyxl` is close to always-needed. `Pillow` matters only when embedding a reference
picture, and `python-docx` only when distilling from `.docx` source documents —
`collect_assets.py`, `profile_store.py`, `ensure_deps.py` and `package_skill.py` are
standard-library only and always work.

---

## Always do this first: profile gate

At the start of **any** stage, check whether a distilled profile exists. Resolve its location with:

```bash
python <skill>/scripts/profile_store.py path     # prints the active profile path, or exits 1
```

Two locations, in priority order:
1. `~/.workbuddy/ai-music-workflow/profile.md` — the **durable home**, outside the skill folder.
2. `<skill>/data/profile.md` — legacy in-skill location, still honoured as a fallback.

**If a profile exists** → load it and follow it for all downstream work (tone, structure,
naming habits, aesthetic preferences). Proceed to the requested stage.

**If none exists** → **ask before assuming they're a new user.** A missing profile has two very
different causes, and re-distilling someone who already has a profile wastes their material:

1. **They upgraded / switched machines and the old profile is elsewhere.** Ask for it — do NOT go
   hunting through their disk, and do NOT tell them to run commands themselves:
   > "我这边还没有你的画像。你之前蒸馏过吗？如果有，把旧技能文件夹（或那份 profile.md、
   > 旧技能的 zip 备份）的路径给我，我直接接过来，不用重新蒸馏。"

   Once they give a path, run the import for them — a folder, a file, or a `.zip` all work:
   ```bash
   python <skill>/scripts/profile_store.py import --from "<whatever path they gave>"
   ```
   Then confirm what was imported by showing a short summary of the profile's contents, so they can
   verify it's the right one.

2. **They're genuinely new** → run **Stage 1** (see `references/distillation.md`):
   > "那我们先做一次蒸馏，后续结果会更贴你的风格。把你过往的需求文档（Word/Excel/txt）放到
   > `data/inbox/`，然后告诉我开始。"

If the user explicitly only wants something trivial that doesn't need a profile, you may proceed
without one, but note that results will be generic.

**If the profile is still in the legacy in-skill location** → migrate it silently (no need to
involve the user), because upgrading the skill replaces that folder and would destroy it:
```bash
python <skill>/scripts/profile_store.py migrate
```

### Upgrading the skill without losing the profile

The distilled profile is the one **irreplaceable** artefact here — it came from the designer's real
past documents, which they may no longer have. Everything else in the skill can be re-shipped.

**Run the migration for the user; never hand them a command to type.** They asked for a working
skill, not a CLI. The scripts exist for you to call.

- **Always write new profiles to the durable home** (`profile_store.py` resolves it), never into
  `<skill>/data/`.
- `import --from` accepts whatever the user has at hand: the old skill folder, a `data/` subfolder,
  an extracted backup, a nested copy (searched a few levels deep), a bare `profile.md`, or a `.zip`
  of the old skill. Quoted paths and paths with spaces are handled.
- If only timestamped backups survive (`profile.bak-*.md`), the newest one is used and this is
  reported.
- Before re-distilling, run `profile_store.py backup`. Overwrites are auto-backed-up anyway.
- Run `profile_store.py status` when unsure — it reports both locations, which one is live, and
  lists existing backups.

> Resolve the skill folder path at runtime. It is the directory containing this SKILL.md
> (typically `~/.workbuddy/skills/ai-music-workflow/`). All `data/`, `adapters/`, `scripts/`,
> `references/` paths below are relative to it.

---

## Output location (important)

**Deliverables go to the user's current workspace, never into the skill folder.**

Every delivery is a **self-contained folder**, so the studio (or the designer months later) gets the
document *and* every reference original in one package:

```
<workspace>/output/<Project>_<Type>_<date>/
├── <Project>_<Type>_<date>.xlsx    the requirement / feedback document
├── Image/    concept art, key visuals, video stills
├── Video/    reference footage the designer sent
├── Audio/    temp tracks, voice memos, studio deliveries
├── Other/    pdf, zip, project files …
└── ASSETS.md manifest: what each file is + a note on why it matters
```

Only the kind folders that actually receive files are created — a delivery with one reference image
has `Image/` and nothing else.

- Resolve `<workspace>` at runtime; do not hardcode paths.
- **Always archive the designer's materials** with `scripts/collect_assets.py` — see
  "Archiving the designer's materials" below. A delivery that references "参考那个视频" without
  shipping the video is incomplete.
- The skill folder only holds the skill's own assets: `data/templates/` (templates),
  `data/feedback/` (AI-prompt tuning notes), and `data/inbox/` (where the user drops source material
  for distillation). The learned profile lives outside it — see the profile gate above.
- This keeps the skill clean and portable for sharing, and puts results where the user expects them.

---

## Archiving the designer's materials (always do this)

Audio designers hand over more than text: concept art, a screen-recording of the cutscene, a temp
track, a voice memo humming the melody. Those originals must ship **with** the document.

Whenever the designer provides ANY file (image / video / audio / anything else) — attached, or as a
path they mention — copy it into the delivery folder:

```bash
python <skill>/scripts/collect_assets.py --out-dir <workspace>/output/<delivery_folder> \
  --asset <path> [--asset <path>...] \
  --note "<path>=<what it is / why it matters>"
```

Rules:
- Run it **before** generating the Excel, so the archived paths can be referenced inside the doc.
- Give a `--note` for every asset — describe *what it is and what the music should take from it*
  ("CG 全片录屏，0:12 转场是重点同步点"), not just the file name. These notes become `ASSETS.md`.
- Pass a folder to archive everything inside it recursively; files are sorted into
  `Image/` `Video/` `Audio/` `Other/` automatically (directly in the delivery folder — no extra
  nesting level).
- It **copies**, never moves — the designer's originals are untouched. Re-running is safe
  (identical files are skipped, earlier notes are preserved, and the deliverable document itself is
  never archived as an asset).
- **The manifest records relative paths only** — never the designer's absolute paths. The folder is
  handed to an outside studio; leaking the local directory layout would be a privacy leak.
- **Reference the archived relative paths inside the Excel** (e.g. `参考 Audio/temp_track.wav`,
  "录屏见 Video/xxx.mp4，0:12 为同步点") so the document and the assets are linked.
- For the Reference/Picture row, embed the image *and* keep it archived: pass the **archived** copy
  to `build_requirement.py --image Image/<file>`.
- Video files cannot be read for content — still ask for a still/screenshot when the musical intent
  depends on what's on screen, but archive the video itself regardless.
- Present the folder's key files at the end (the Excel + `ASSETS.md`), not just the Excel.

---

## Stage 1 — Distill the designer's profile

Goal: read the designer's existing requirement documents and produce a persistent profile capturing
their working style, aesthetic, and brief-writing habits.

Full procedure: **`references/distillation.md`**. Summary:
1. Check `data/inbox/` for source material. Support `.docx`, `.xlsx`/`.xls`, `.txt` (and `.md`).
2. Extract text with `scripts/read_materials.py` (handles all three formats).
3. Analyze and write the profile to the **durable home** (`scripts/profile_store.py path` resolves
   it; create `~/.workbuddy/ai-music-workflow/profile.md`), using the structure in the distillation
   reference. Do NOT write it into `<skill>/data/` — a skill upgrade would wipe it.
4. Show the user a short summary of what was learned and ask for corrections.

Re-distillation: if the user says "重新蒸馏 / 更新画像", run `scripts/profile_store.py backup`
first, then re-run and overwrite the profile.

**Adopting the designer's own template** (a natural companion to distillation — the bundled
templates carry *another* team's house style): when they say anything like "用这份文档当我的模板"
or point at a real document, run `scripts/make_template.py --source <doc> --out
data/templates/<Type>.xlsx --clear-values` yourself. They should never have to type that command;
just confirm which music type it maps to and report that future documents will match their format.

---

## Stage 2 — Generate the requirement document (Excel)

Goal: take the designer's spoken/written idea, confirm it, professionally polish it in *their*
voice, and output a structured **Excel** that conforms to a chosen template.

Full procedure: **`references/requirement_doc.md`**. Summary:
1. **Confirm the brief.** Collect the core requirement; ask targeted questions for any gaps
   (project, scene/usage, mood, reference, length, structure, loop?, format/deliverable, deadline).
   Mirror the profile's question style; don't over-ask.
2. **Pick a template.** List available templates from `data/templates/` (e.g. CG, Lobby).
   Different music types use different templates. If none exists, see the template-bootstrap note
   in the reference (you can convert one of the user's past docs into a template).
3. **Polish.** Rewrite the requirement professionally, following the distilled profile for tone and
   the template for required fields. Improve layout/clarity even though the user isn't a doc expert.
   Filling a template **preserves its formatting and fonts automatically** — don't re-style.
4. **Reference materials.** The designer may attach reference images (concept art, a still from a
   reference video), reference footage, or a temp track. **Archive all of them** into the delivery
   folder with `collect_assets.py` (see "Archiving the designer's materials"), then reference the
   archived paths in the brief. Read images to inform the brief, and embed the key one into the
   Excel with `build_requirement.py --image <archived path>` (it goes into the Reference/Picture
   row, like the designer's real documents). Video content can't be read — ask for a still when the
   musical intent depends on what's on screen, but archive the video anyway.
5. **Generate Excel** with `scripts/build_requirement.py`, writing into the **delivery folder in the
   current workspace** (see "Output location" above) — NOT into the skill folder.
   - Run `--inspect` on the template first when unsure of the exact field labels; it now prints a
     ready-to-copy list of JSON keys.
   - Watch the script's `[warn]` lines: an unmatched key means a typo (the value gets appended at
     the end instead of landing in its row), and a clamped row means the text exceeds what one
     Excel row can display.
6. Present the delivery (Excel + `ASSETS.md`) via the result-presentation step and ask if anything
   needs adjusting.

**Stop here unless the user wants prompts.**

---

## Stage 3 — Take the requirement forward (two branches)

Pick the branch by **who makes the music**:
- **3A — AI tools** (Suno / Lyria / …): generate prompts. See below.
- **3B — Professional studio**: after the designer listens to the studio's delivery, write a
  **feedback document** (Excel). Full procedure: **`references/feedback_doc.md`**. Summary:
  1. Identify the track it's about (link to the Stage-2 requirement if available).
  2. Collect the designer's reactions; ask for the music type (and whether they're giving
     **per-timestamp** notes — e.g. `0-9s`, the chorus — possibly with screenshots, or **overall**
     feedback). Adapt automatically: timeline notes → per-segment rows; otherwise → overall section.
  3. Polish the feedback in the designer's professional voice (per the distilled profile): keep it
     specific and actionable for the studio (what's off, the target, the reference), not vague.
  4. **Archive the materials** — the studio's delivered audio file, timestamp screenshots, any
     reference track used to explain the note — with `collect_assets.py` into the delivery folder,
     then generate the Excel from `data/templates/Feedback.xlsx` there, preserving fonts/format;
     embed a key screenshot with `--image` and reference the archived paths in the notes.
  5. Present the delivery (Excel + `ASSETS.md`) and ask if anything needs adjusting.

### 3A — Generate AI-music prompts (per-platform adapters)

Goal: convert a requirement (the Stage-2 Excel, or a direct idea) into **accurate prompts** for a
specific AI music tool, strictly following that tool's **official** prompting documentation, then
tune based on the designer's feedback.

Full procedure: **`references/prompt_generation.md`**. Summary:
1. **Pick the platform.** Ask which AI tool (or read it from the brief). Built-in adapters:
   - `adapters/suno.md` — Suno (v6 family: v6 / v6-wild / v6-mini)
   - `adapters/lyria.md` — Lyria (current: Lyria 3.5, via Gemini app / API / Flow Music)
   - Any other tool → use `adapters/_TEMPLATE.md` to build a new adapter (see below).
2. **Load the adapter** and generate the prompt(s) exactly per its rules and field layout.
3. **Present** the prompt in copy-paste-ready form, with the adapter's tuning tips.
4. **Feedback loop.** When the user reports the result ("低音太弱 / 不够史诗 / 结构乱了"),
   diagnose using the adapter's troubleshooting table, revise, and — if the fix is generally useful —
   append it to `data/feedback/<platform>.md` so the skill improves over time.

### Adding a new AI music tool (extensibility)
This is a core feature. To support any tool — including future ones:
1. Copy `adapters/_TEMPLATE.md` to `adapters/<toolname>.md`.
2. **Find the official prompting docs.** Try to fetch them from the web first. If you cannot reach
   them, **instruct the user** how to find the official guide (vendor site / in-app help) and ask
   them to paste the content; then write the adapter from that.
3. Fill the adapter: official source URL + version + date checked, prompt anatomy, hard rules,
   field layout, example, troubleshooting. **Base everything on the official docs, never guesswork.**

### Keeping adapters current (official-docs sync)
Every built-in adapter records its **official source, model version, and last-checked date**.

**Check that date at the start of Stage 3A, before generating anything.** AI music platforms do not
just add versions — they *retire* the old ones. On 2026-09-09 Suno shipped v6 and removed v4–v5.5
from the picker the same day, which silently turned a correct adapter into one describing models
that can no longer be selected. A stale adapter here does not degrade gracefully; it produces
prompts for a product that no longer exists.

So:
- **Last-checked date more than ~1 month old, or the user names a version the adapter doesn't
  cover** → re-fetch the official docs before generating, update the adapter, bump the header and
  Changelog. Say so briefly; don't silently generate against stale rules.
- **Prefer a fetchable official spec.** Google publishes one for Lyria, so that adapter is fully
  sourced. Suno does not, so its adapter tags each item **[官方]** vs **[实测]** — keep that
  distinction when editing, and never promote an observation to official wording.
- **Keep the version out of filenames** (`suno.md`, `lyria.md`) — the version belongs in the header,
  so a model bump doesn't require renaming files and fixing references everywhere.
- If you can't reach the docs, say so and guide the user to supply them rather than guessing.

---

## Which channel produces which document

Full details, with the measured evidence behind them: **`references/document_channels.md`**.
Read it before producing anything other than a standard Excel requirement doc.

The short version:

| Deliverable | Channel |
|---|---|
| Excel requirement / feedback doc (the core output) | `scripts/build_requirement.py` filling a template |
| **Any image inside an Excel deliverable** | `build_requirement.py --image` — **never** the host's in-cell image |
| Word / PPT versions, or any other local Office format | WorkBuddy's built-in local Office channel |
| Editing an existing document, or the designer's own Word/PPT template | Built-in local Office channel |

**Why images in Excel are pinned to the script:** the host's `sheet_insert_image` stores an
Excel-365 "image in cell" (`xl/richData/`), whose fallback cell value is `#VALUE!`. The studio opens
these briefs in whatever they have — an older Excel, WPS, or a mail preview — and would see
`#VALUE!` where the concept art should be. `build_requirement.py` writes an ordinary anchored
picture that renders everywhere. Word and PPT have no such issue; images there go through the host
channel normally.

**Why the core Excel stays with the template filler:** the host ships generic document routing that
claims anything phrased like "生成 / 制作 / 整理成 Excel" with no source spreadsheet — which is
exactly how Stage 2 is phrased. Those generators build a workbook from scratch with their own
styling and never read `data/templates/`, so the designer's house font and row heights would be
silently lost. Do not route this skill's requirement / feedback document to
`tencent-docs-sheet-generation`, a docs-routing gate, or a spreadsheet subagent.

Generic routes are fine for a **different** job the user explicitly asks for on a finished file
(e.g. "帮我在这个表里做个数据透视").

### If the designer asks for Word or PPT

Do not refuse — the content pipeline is the same, only the output format differs:

1. Build the content exactly as Stage 2 / 3B would (same brief confirmation, same profile-driven
   polish, same asset archiving into the delivery folder).
2. Produce the file through the built-in local Office channel, writing it into the **same delivery
   folder** beside the archived assets. See `references/document_channels.md` for the call flow.
3. If the designer has their own Word/PPT house template, open and fill it — that preserves its
   fonts and layout, same as the Excel path.
4. Excel remains the default for anything going to a studio: that is the format they receive today.

---

## Files in this skill

```
ai-music-workflow/
├── SKILL.md                      # this file — routing + profile gate
├── README.md                     # repository landing page (GitHub), not used at runtime
├── QUICKSTART.md                 # 5-minute onboarding for a designer (not used at runtime)
├── USAGE.md                      # human-facing usage guide (for the designer, not runtime)
├── CHANGELOG.md                  # version history + the rules for bumping a version
├── .gitignore                    # keeps the profile and real source docs out of a public repo
├── references/
│   ├── distillation.md           # Stage 1 detailed procedure
│   ├── requirement_doc.md        # Stage 2 detailed procedure
│   ├── prompt_generation.md      # Stage 3A detailed procedure + adapter rules
│   ├── feedback_doc.md           # Stage 3B — feedback doc for studio-produced music
│   └── document_channels.md      # which channel makes which file (Excel / Word / PPT / images)
├── adapters/
│   ├── _TEMPLATE.md              # blueprint for any new AI music tool
│   ├── suno.md                   # Suno v6 family (official announcement + FAQ based)
│   └── lyria.md                  # Lyria 3.5 (official Gemini API docs based)
├── scripts/
│   ├── ensure_deps.py            # install missing Python deps into THIS interpreter (stdlib only)
│   ├── read_materials.py         # extract text from docx/xlsx/txt/md
│   ├── make_template.py          # turn a real doc into a blank template (keeps fonts/format)
│   ├── build_requirement.py      # fill a template (preserves format) + optional --image embed
│   ├── collect_assets.py         # archive the designer's Image/Video/Audio into the delivery folder
│   ├── profile_store.py          # locate / migrate / import the distilled profile (upgrade-safe)
│   └── package_skill.py          # maintainer tool: version-stamped zip, refuses to ship private data
├── examples/                     # sample material for new users (not used at runtime)
│   ├── README.md
│   └── sample_briefs/            # anonymized sample CG/Lobby/Story briefs
└── data/                         # skill assets (NOT deliverables)
    ├── templates/                # Excel templates (CG / Lobby_Story_Login / Feedback)
    ├── inbox/                    # user drops source docs here for distillation
    └── feedback/                 # accumulated per-platform AI-prompt tuning notes (NOT studio feedback)

# The distilled profile lives OUTSIDE this folder, at ~/.workbuddy/ai-music-workflow/profile.md,
# so upgrading the skill never destroys it. See the profile gate section above.
#
# Deliverables (Excel + archived assets + ASSETS.md) are written to a self-contained folder in the
# USER'S WORKSPACE, not inside this skill folder. See "Output location" above.
```

## Excel layout guarantees (what the script handles for you)
`build_requirement.py` enforces these, so don't hand-patch the output:
- **Template heights are floors, never overwritten.** A row only grows when its wrapped text needs
  more room, so the designer's house layout (e.g. 60pt field rows) survives.
- **Heights are clamped to Excel's 409.5pt hard limit** — exceeding it produces a file Excel offers
  to "repair". The script warns which row was clamped so the content can be split instead.
- **Line-count estimates use each cell's real font size and column width**, counting CJK characters
  as double width.
- **Labels match whitespace-insensitively**, so a template label wrapped as `Reference\nPicture` is
  filled by the key `"Reference Picture"`.
- **Unmatched keys are reported as `[warn]`** (and appended with the template's styling) instead of
  silently vanishing.
- **Trailing blank rows get no inherited height**, so documents don't end in stretched empty rows.
- **`--clean-placeholders` shifts row heights along with deleted rows.** openpyxl's `delete_rows`
  moves cell values but leaves `row_dimensions` behind — a wrapper fixes this. Never call
  `delete_rows` directly on these templates.
- **`--clean-placeholders` never deletes a row this run filled in.** Real feedback can legitimately
  be written inside angle brackets ("<整体不错，但副歌太满>"); such a value would otherwise look
  like an unfilled `<...>` placeholder and be silently dropped.
- **Values don't have to be strings.** Numbers pass through, booleans become Yes/No, and a list
  becomes newline-separated lines (handy for multi-point requirements). Nothing raises.
- **Inherited date formats are neutralised.** Some template cells carry a `mm-dd-yy` number format
  from the original documents; writing `2026` into one would render as 1905-07-18. Any filled cell
  gets a General format unless the value really is a date object.
- **Missing/invalid inputs fail with a clear `[error]`**, not a traceback: absent template, absent
  or malformed data file, non-object JSON, unreadable image.

## Versioning, packaging / sharing notes

**Version of record:** the `version:` field in this file's frontmatter. `CHANGELOG.md` holds the
history and the rules for when to bump MAJOR / MINOR / PATCH — read it before changing the version.
For this skill "breaking" means the designer must migrate something (their profile, or a delivery
folder layout), not an API change.

**Always package with the script, never by hand:**
```bash
python <skill>/scripts/package_skill.py            # -> dist/ai-music-workflow-<version>.zip
python <skill>/scripts/package_skill.py --check    # audit only, build nothing
```
It reads the version from frontmatter, stamps it into the filename so older releases remain
available to roll back to, and **re-opens the finished zip to verify** nothing private got in —
deleting the package and failing if anything did. Hand-rolled zips have already been observed to
include files that should have been excluded; the script exists so that cannot happen again.

**What never ships** (enforced by the script, and by `.gitignore` for the repo case):
- `data/profile*` — the distilled profile and its backups. One designer's working style, learned
  from their real documents; the one artefact here that cannot be recreated.
- `data/inbox/*` — their real requirement documents. Often an entire project's commissions, and
  large.
- `data/feedback/*` — tuning notes that quote real projects.
- `_user_meta.json` and friends — installer metadata local to one machine; the runtime never reads it.
- `__pycache__/`, `*.pyc`, editor/OS cruft.

Each folder's `.gitkeep` is kept so the structure ships intact. `examples/sample_briefs/` contains
**anonymized** samples only and is safe to share.

**Other notes:**
- All commands resolve the skill's own folder at runtime — no hardcoded user paths.
- Python deps are handled **for** the designer — see "Dependencies" above. `openpyxl` (Excel),
  `Pillow` (image embed), `python-docx` (Word distillation) are installed on demand by
  `scripts/ensure_deps.py`; `collect_assets.py`, `profile_store.py`, `ensure_deps.py` and
  `package_skill.py` are standard-library only.
