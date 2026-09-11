# Stage 3 — AI-music prompt generation procedure

Goal: convert a requirement (the Stage-2 Excel, or a direct idea) into **accurate, copy-paste-ready
prompts** for a chosen AI music tool, strictly following that tool's **official** prompting docs,
then iterate based on the designer's feedback.

The design principle: **one adapter per AI tool.** Each adapter encodes that tool's exact prompt
grammar from its official documentation. This makes the skill work for Suno and Lyria today, and
any future tool tomorrow — without changing the core flow.

---

## Step 1 — Get the requirement
- Preferred: read the Stage-2 Excel from the user's workspace (the path where it was generated, or a
  path the user gives) with `python <skill>/scripts/read_materials.py <file>`.
- Or accept a direct idea in chat. (If there's no profile yet, results are generic — consider
  running Stage 1 first.)

Write any prompt-output file (e.g. a `*_prompts.md`) to the **user's workspace**, not the skill folder.

## Step 2 — Pick the platform / adapter
Ask which AI music tool, or read it from the brief. Built-in adapters in `adapters/`:
- `suno.md` — Suno (v6 family: v6 / v6-wild / v6-mini)
- `lyria.md` — Lyria (current: Lyria 3.5, via Gemini app / API / Flow Music)
- New / other tool → build one from `adapters/_TEMPLATE.md` (see "Adding a new tool" below).

Load the chosen adapter file and follow it **exactly** — field layout, hard rules, syntax.

## Step 3 — Map requirement → prompt
Use the adapter to translate the requirement into the tool's fields. General mapping that every
adapter specializes:
- genre/subgenre, mood, instruments, tempo (BPM), key, vocals, structure, length, exclusions.
- Honor the distilled profile's aesthetic defaults when the brief is silent (e.g. preferred BPM range).
- Never use copyrighted artist/game names — decompose into technical descriptors (all major tools
  filter artist names).

## Step 4 — Present
Output in the adapter's presentation format (Chinese labels, copy-paste blocks). Include:
- The exact field contents for that tool.
- 2-3 concrete tuning tips from the adapter.
- A note on which adapter/version + official source was used.

## Step 5 — Feedback loop (tuning)
When the user reports how the generated music turned out:
1. Diagnose with the adapter's **troubleshooting table** (symptom → cause → fix).
2. Revise the prompt and present the new version, explaining what changed and why.
3. If the fix is generally reusable (not one-off), append it to `data/feedback/<platform>.md`
   as a dated note: `## <date> symptom → fix`. Future runs should read this file and apply
   learned fixes proactively.
4. If feedback reveals the official rules changed (new model, new tags), trigger the sync step.

---

## Adding a new AI music tool (core extensibility feature)
1. Copy `adapters/_TEMPLATE.md` → `adapters/<toolname>.md`.
2. **Obtain the official prompting documentation:**
   - First, try to fetch it from the web (vendor docs, official prompt guide).
   - If you cannot reach it, **guide the user**: tell them where the official guide usually lives
     (the vendor's site, in-app "help"/"prompt guide", API docs) and ask them to paste the content.
   - Do NOT write prompt rules from memory or third-party blogs alone. Official first; reputable
     secondary sources only to supplement.
3. Fill every section of the template from the official docs: source URL + version + date checked,
   prompt anatomy, hard rules, field layout, worked example, troubleshooting table.
4. Use the new adapter exactly like the built-in ones.

## Keeping adapters current (official-docs sync)
Each adapter has a header block: **Official source / Model version / Last checked**.
- When the user mentions a new model or version, or an adapter's date is old, re-fetch the official
  docs, update the adapter content, and bump the date + version.
- If the docs are unreachable, ask the user to supply the latest official guide, then update.
- Record what changed at the bottom of the adapter under "Changelog".
