# Adapter — <AI MUSIC TOOL NAME>

> Blueprint for adding a new AI music tool. Copy this file to `adapters/<toolname>.md` and fill
> every section **from the tool's OFFICIAL prompting documentation**. If you can't reach the docs,
> guide the user to find them and paste the content — never write rules from memory or blogs alone.

| | |
|---|---|
| **Official source** | <paste the official prompt-guide / docs URL(s) here> |
| **Model version** | <model + version this adapter targets> |
| **Last checked** | <YYYY-MM-DD> |

---

## How prompting works (the tool's mental model)
- One field or several? Natural-language paragraph or keyword tags? Does it run a prompt rewriter /
  infer structure? Note the single biggest way it differs from other tools.

## Prompt anatomy / fields
- List each input field and what it controls. Give the recommended order/weighting if any.

## What to specify
- genre, mood, instruments, tempo/BPM, key, vocals, structure, length, exclusions — with the exact
  vocabulary/syntax this tool expects. Note limits (char caps, tag counts).

## Vocals & lyrics
- How to supply lyrics, how to direct the vocal performance, backing vocals syntax, languages.

## Structure / metatags (if any)
- The verified list of tags this tool recognizes and exactly where they go.

## Image / other modalities (if supported)
- e.g. image-to-music, audio reference, stems. Only use when the user actually provides input.

## Hard rules (do / don't)
- ✅ ...
- ❌ ... (especially: artist-name filtering, field misuse, length/duration behavior)

## Output presentation (Chinese)
```
### 🎵 <Tool> 提示词方案
【<field 1>】...
【<field 2>】...
💡 调优建议：
- ...
（依据：官方文档，本适配器核对于 <date>）
```

## Troubleshooting table
| Symptom | Likely cause | Fix |
|---|---|---|
| ... | ... | ... |

## Changelog
- <YYYY-MM-DD> — Initial adapter from official docs.
