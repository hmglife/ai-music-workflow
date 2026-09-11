# Stage 1 — Distillation procedure

Goal: learn one audio designer's **working style, aesthetic, and brief-writing habits** from
their own past documents, and persist it so every later stage sounds like them.

The profile's durable home is **outside** the skill folder, so upgrading the skill can't destroy it:

```bash
python <skill>/scripts/profile_store.py path     # resolves the active profile path
python <skill>/scripts/profile_store.py status   # both locations + which is live + backups
```
- Durable home: `~/.workbuddy/ai-music-workflow/profile.md` ← **write here**
- Legacy fallback (read-only concern): `<skill>/data/profile.md`

This runs once (or on demand when the user says "重新蒸馏 / 更新画像").

---

## Step 0 — Decide if distillation is needed
- If a profile already exists (check with `profile_store.py path`) and the user did NOT ask to
  re-distill → skip; just load it.
- If it exists but only in the legacy in-skill location → run `profile_store.py migrate` (silently,
  no need to involve the user) so the next upgrade doesn't wipe it, then load it.
- If re-distilling → run `profile_store.py backup` first, then continue.

### No profile found — ask before distilling
Do **not** assume a missing profile means a new user. They may have upgraded or changed machines,
with the old profile sitting in the replaced folder or a backup. Re-distilling in that case burns
their source material for nothing.

Ask once, plainly:
> "我这边还没有你的画像。你之前蒸馏过吗？如果有，把旧技能文件夹（或那份 profile.md、旧技能的 zip
> 备份）的路径给我，我直接接过来，不用重新蒸馏。"

Then **do the import yourself** — never ask the user to run the command:
```bash
python <skill>/scripts/profile_store.py import --from "<the path they gave>"
```
It accepts a folder (old skill folder, its `data/`, an extracted backup, a nested copy), a bare
`profile.md`, or a `.zip` of the old skill. After importing, show a short summary of what the
profile says so the user can confirm it's the right one.

Only proceed with a fresh distillation once they confirm there's nothing to import.

## Step 1 — Collect source material
Source material lives in `data/inbox/`. Supported formats: `.docx`, `.xlsx` / `.xls`, `.txt`, `.md`.

1. List the files in `data/inbox/`.
2. If it's empty, ask the user to drop their past requirement documents there:
   > "把你以往写过的音乐需求文档放到 `data/inbox/`（支持 Word / Excel / txt / Markdown），
   > 越多越能学准你的风格。放好后告诉我开始。"
3. Do NOT proceed to analysis with zero files.

## Step 2 — Extract text
Run the reader script over the whole inbox:

```bash
python <skill>/scripts/read_materials.py <skill>/data/inbox --json
```

- It walks the folder, extracts text from every supported file, and prints a JSON array of
  `{file, type, text}` (Excel is flattened sheet-by-sheet, cell by cell).
- If a dependency is missing it prints an auto-install command — run **that** (it installs into the
  same interpreter) and retry. Never hand the designer a `pip` command to run themselves.
- For very large outputs, read file-by-file instead (`read_materials.py <one-file>`).

## Step 3 — Analyze
Read all extracted text and infer, with evidence, the designer's patterns. Look for:

- **Document structure & fields** — which fields they always fill (项目、场景/用途、时长、结构、
  循环方式、参考曲、情绪、乐器、交付格式、截止时间…), in what order, with what column layout.
- **Writing voice** — terse vs. descriptive; Chinese/English mix; how they phrase moods and
  references; whether they cite reference tracks or describe vibes.
- **Aesthetic tendencies** — recurring genres, instrumentation, tempo ranges, emotional palette,
  production preferences, things they consistently avoid.
- **Music-type conventions** — e.g. CG vs Lobby vs Battle: structure (intro+loop+end?), typical
  length, looping requirements, dynamics.
- **Workflow habits** — naming conventions, versioning, how deliverables are specified, any
  recurring instructions to the composer/AI.

Prefer concrete, quoted evidence over guesses. If the inbox is thin, say so and mark low-confidence
items.

## Step 4 — Write the profile
Write it to the durable home — `~/.workbuddy/ai-music-workflow/profile.md` (create the folder if
needed). Never write it into `<skill>/data/`, which a skill upgrade replaces.

Use this structure (fill from evidence; omit a section if no evidence):

```markdown
# Audio Designer Profile
_Distilled on <YYYY-MM-DD> from N documents in data/inbox/_

## 1. Identity & scope
- Role / domain (e.g. game audio designer), typical music types handled.

## 2. Brief-writing voice
- Tone, language mix, level of detail, signature phrasings (with 1-2 short quoted examples).

## 3. Standard requirement fields (and order)
- The fields they consistently include, the order, and any house formatting.

## 4. Aesthetic profile
- Preferred genres / instruments / tempo ranges / mood palette / production traits.
- Things they avoid.

## 5. Music-type conventions
- Per type (CG / Lobby / Battle / …): structure, length, loop behavior, dynamics.

## 6. Workflow & deliverable habits
- Naming, versioning, formats, recurring instructions.

## 7. Open questions / low-confidence items
- Anything the agent inferred weakly and should confirm with the user.
```

## Step 5 — Confirm with the user
Show a concise summary (not the whole file) of what was learned and explicitly surface the
"open questions" so the user can correct them. Apply corrections to the profile.

Tell the user distillation is complete and that future requests will follow this profile, and that
they can re-run anytime with "重新蒸馏".
