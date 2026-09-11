# Changelog

All notable changes to **ai-music-workflow** are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versioning follows the rules below.

The version of record lives in one place only: the `version:` field in `SKILL.md`'s frontmatter.
The packaging script reads it from there, so there is nothing to keep in sync by hand.

---

## Versioning rules (read before bumping)

This is a workflow skill, not a library. "Breaking" therefore does **not** mean an API change — it
means **the designer has to do something, or work they already produced stops behaving the same.**
Two things carry that risk: their **distilled profile** and their **delivery folders**.

| Bump | When | Examples from this project's own history |
|---|---|---|
| **MAJOR** `x.0.0` | The user must migrate something, or existing artefacts no longer match | profile moved out of the skill folder; delivery layout changed (`assets/` level removed, folders capitalised); a template's field set changes so old briefs no longer regenerate identically |
| **MINOR** `1.x.0` | New capability, nothing existing breaks | asset archiving; Word/PPT output; a new platform adapter; profile import tooling |
| **PATCH** `1.0.x` | Fixes and corrections only | layout/formatting bugs; wrong or outdated wording in docs; refreshing an adapter's details within the same platform |

Two judgement calls worth stating, because they are not obvious:

- **An adapter rewrite for a retired model is MINOR, not PATCH.** When a platform retires the model
  an adapter targeted (Suno did exactly this), the old adapter does not degrade — it produces
  prompts for something that no longer exists. That is a capability change, not a typo fix.
- **A change to what lands in the delivery folder is MAJOR**, even if the code change is small.
  The folder is handed to an outside studio; a designer who has already sent v1 folders should not
  silently get a differently-shaped v2.

### Release checklist
1. Run the official validator, and run a real end-to-end generation on all three templates.
2. Update this file: move work out of *Unreleased* into a dated version heading.
3. Bump `version:` in `SKILL.md`.
4. `python scripts/package_skill.py` — it reads the version, refuses to package if personal data
   is present, and writes `dist/ai-music-workflow-<version>.zip`.
5. Refresh the **git repo folder from that zip** — never turn the live skill folder into a repo.
   GitHub's web drag-and-drop ignores `.gitignore`, so the only reliable protection is a repo
   folder that physically contains no private data. Then publish a Release with the zip attached
   (the audience are audio designers, not developers — they download a file, they don't clone).

---

## [Unreleased]

_Nothing yet._

---

## [1.0.0] — 2026-09-11

First release intended for sharing with other audio designers. Everything below was validated by
real end-to-end runs, not just review.

### Added
- **Stage 1 — profile distillation.** Reads a designer's own past requirement documents
  (`.docx` / `.xlsx` / `.txt` / `.md`) and distils a reusable profile: writing voice, aesthetic
  defaults, per-music-type conventions, delivery habits.
- **Stage 2 — requirement documents.** Turns a spoken idea into a template-conformant Excel brief.
  The generator fills an existing template rather than building a workbook, so the team's house
  font and layout are inherited exactly.
- **Stage 3A — AI-music prompts** via pluggable per-platform adapters, each recording its official
  source, model version and last-checked date. Ships with Suno and Lyria adapters plus a template
  for adding any new tool.
- **Stage 3B — feedback documents** for music produced by an external studio, in both
  per-timestamp and overall-impression modes.
- **Self-contained delivery folders.** Every reference the designer provides (image / video /
  audio / other) is copied beside the document and listed in a generated `ASSETS.md`, so the studio
  receives one package instead of a document referring to files it never got.
- **Upgrade-safe profile storage.** The distilled profile lives outside the skill folder, with
  `profile_store.py` to locate, back up, migrate and import it — including importing from an older
  skill folder, a bare `profile.md`, or a zipped backup.
- **Word / PPT / other formats** on request, produced through the host's local Office channel,
  including filling a designer's own Word/PPT template.
- **`QUICKSTART.md`** — a 5-minute onboarding path for a designer who has never used this before:
  what to install, how to distil a profile, how to build a template from their own real document,
  and the exact phrases that trigger each stage.
- **Docs for three audiences**: `README.md` (repository landing page), `QUICKSTART.md` (5-minute
  path for a designer), `USAGE.md` (full guide), plus `references/` for the assistant itself.
- **Versioning, changelog and a packaging script** with a built-in privacy guard (this release).
- **Zero-setup dependencies.** The designer never installs anything: `scripts/ensure_deps.py`
  installs what a job needs into the *same* interpreter that runs the scripts, and the assistant is
  instructed to do this silently and retry. A raw `pip install` hint was the wrong instruction
  twice over — the designer is not a Python user, and their shell's `pip` may belong to a different
  environment than the one running the scripts, so following it could leave the error in place.
  The script itself is standard-library only, and when installation is genuinely impossible it
  reports what is degraded in plain language instead of handing over a command.

### Fixed
Found by adversarial testing during development; all are user-visible:
- Row heights are now floors that only grow, so the template's designed layout survives; heights are
  clamped to Excel's 409.5pt limit instead of producing a file Excel offers to "repair".
- Line-count estimation uses each cell's real font size and column width, counting CJK as
  double-width.
- Field labels match whitespace-insensitively, so a label wrapped across two lines still fills.
  Unmatched keys now warn instead of vanishing silently.
- Deleting unused placeholder rows no longer leaves row heights behind on the wrong rows.
- **Silent data loss:** real content wrapped in angle brackets — ordinary in Chinese writing — was
  being deleted as if it were an unfilled placeholder. Only never-filled placeholders are removed now.
- Non-string values (lists, booleans, numbers) no longer raise; lists become multi-line text.
- Numbers no longer render as dates: stale date number-formats were cleared from the templates and
  are neutralised on write.
- Missing files and malformed input produce clear errors instead of raw tracebacks.
- **`make_template.py` produced a subtly broken template.** Any label without a built-in
  placeholder had its value blanked, which (a) erased section headers such as the CG timeline's
  `Time | Requirements List`, and (b) left unused rows empty instead of `<placeholder>` — so
  `--clean-placeholders` could no longer detect and remove them. Section headers are now
  preserved, timeline rows are matched by shape, and an unrecognised label gets a generic
  `<label>` hint plus a note listing which labels that applied to. Found while verifying the
  QUICKSTART, whose very first setup step tells a designer to build a template from their own
  document.

### Security / privacy
- The packaging script **refuses to build** if a distilled profile or source documents are present,
  so a fork can never accidentally ship one designer's private material.
- `.gitignore` excludes the same material, so it cannot be committed to a public repository either.
- Manifests record relative paths and original file names only — never absolute paths that would
  expose the designer's machine layout.

### Known limitations
- Excel templates carry one team's house style; other teams should build their own from a real
  document (`make_template.py` keeps fonts and layout).
- A Word/PPT version won't carry that house style unless the designer supplies their own template.
- AI-platform adapters go stale quickly — platforms retire models. Check each adapter's
  last-checked date before a high-stakes batch.
