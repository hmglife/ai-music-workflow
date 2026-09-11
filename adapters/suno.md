# Adapter — Suno (v6 family)

| | |
|---|---|
| **Official source** | Suno launch announcement "Introducing v6" (2026-09-09); Suno v6 FAQ + Creative Sliders help articles (quoted verbatim by multiple independent launch-week reports); in-app model picker copy. |
| **Model version** | **v6 / v6-wild / v6-mini** — v4, v4.5, v5 and v5.5 are **retired** |
| **Last checked** | 2026-09-11 |

> ⚠️ **v6 was a breaking change, not a version bump.** On 2026-09-09 Suno replaced the entire
> lineup and removed the older models from the picker. Any prompt guide written for v4/v5/v5.5 —
> including the previous version of this adapter — describes a model that can no longer be selected.
>
> **Provenance note:** Lyria's adapter is backed by a fetchable official spec; Suno publishes no
> equivalent. Items below are tagged **[官方]** (Suno's own announcement / FAQ wording) or
> **[实测]** (launch-week hands-on reports, independently corroborated). Treat 实测 items as
> strong defaults to verify on your own material, not as documented syntax.

---

## Step 0 — Settings first, prompt second (this is new and it matters most)

v6 added **Creative Sliders** in Custom mode → More Options. One of them **edits your prompt before
generation**. Getting these wrong makes even a perfect prompt come back off-brief.

| Control | Range | What it acts on | What to set for a brief |
|---|---|---|---|
| **Variety** | 0 → high | **Your style prompt text itself** | **0** |
| **Style Influence** | Loose → Strong | How closely output follows the style input | Raise above the 50% default |
| **Weirdness** | Safe → Chaos | Conventionality | 50% *is* the neutral default, not 0 |
| **Audio Influence** | Loose → Strong | Pull of an uploaded reference | only appears with an audio upload |
| **Max Mode** | on / off | Spends more credits for better adherence | on for the keeper take |

**[官方]** Suno's v6 FAQ on Variety: *"The Variety slider is designed to introduce variety in your
outputs by adjusting and updating your style prompts. If you'd like to retain full control of your
style tags, reduce the Variety slider to 0."*

Why this is rule #1 for this workflow: a requirement document exists to pin down a precise musical
intent. Variety at its default will rewrite that intent — reportedly blending in styles from your
recent generations — and the designer will conclude the brief was ignored. **Always tell the user to
set Variety to 0** when running a brief-derived prompt.

**[官方]** Max Mode is *"an option you can turn on for any generation when you want v6 to spend more
on getting it right"* — Suno names songs over two minutes, covers that must stay close to the
original, style transfer, and keeping vocals/style consistent across a track.

**[实测]** Slider values typed into the Style box do nothing. They are interface controls; text like
`Weirdness: 20%` is just read as style description. Never put them in the prompt.

**Model choice:** `v6` = reliable and precise (use this for a brief). `v6-wild` = *"best for
experimental ideas"*, deliberately less predictable (use when exploring, not when matching a spec).
`v6-mini` = free tier, no downloads / commercial use.

---

## Prompt anatomy (THREE fields now)

1. **Style** — sound descriptors only. **1,000 chars** [实测, unchanged from v5.5].
2. **Lyrics** — lyrics *and* structure tags. **5,000 chars** [实测, unchanged from v5.5].
3. **Exclude Styles** — **all negatives go here** [实测]. This is a change in practice from the old
   advice of writing `no vocals` inline.

**Why exclusions moved:** in the Style box, `male lead vocal` reads as an instruction to *include*
one. Negatives only subtract when they are in the Exclude Styles field. After generating, Suno
renders your Exclude terms back into the style view with `-` prefixes — that display is not the
model rewriting your prompt.

## Style field

Recommended order [实测, community-converged]:
`Genre` → `Vocals` → `Drums` → `Guitars` → `Bass` → `other instruments` → `Arrangement & energy` →
`Production` → `Ending instruction`

- **Genre**: be specific. "deep melodic techno, Berlin club sound" ≫ "electronic". Blend with
  commas / "meets" / "x". Era words work ("early 90s", "2000s").
- **Direct a musician, don't describe a record.** v6 rewards verbs over adjective stacks — give each
  instrument a *job relative to the others* ("pedal steel answers the end of each vocal line, never
  over the voice") rather than piling on moods.
- **Instruments**: name 3–5 specific ones. "analog Juno pads, 303 acid bassline" ≫ "synths".
- **BPM**: always state a number. (ambient 60–90, hip-hop/R&B 80–100, pop 100–120,
  house/techno 120–130, DnB 130–175.)
- **Key** (optional): useful when stitching multiple generations.
- **Production**: "clean mix, wide stereo, large hall reverb" / "lo-fi, warm tape saturation".
- **Ending**: state it explicitly — v6 likes to add a trailing outro otherwise.
- Sweet spot remains roughly **8–15 tags**; front-load what matters.

## Lyrics field — structure tags AND per-section direction

Rules:
- **One tag per line**, on its own line. **Tag before content.**
- Number verses (`[Verse 1]`, `[Verse 2]`) for different melodies; leave `[Chorus]` un-numbered to
  repeat its melody.

Structure tags:
`[Intro]` `[Verse]` `[Pre-Chorus]` `[Chorus]` `[Post-Chorus]` `[Bridge]` `[Breakdown]`
`[Build]`/`[Build-Up]`/`[Rise]` `[Drop]` `[Hook]` `[Interlude]` `[Instrumental]`
`[Guitar Solo]`/`[Drum Solo]` `[Outro]`/`[Ending]` `[Fade Out]` `[End]` (hard stop).

### What changed in v6: section cues now carry real performance direction

**[实测, strongest single finding of launch week]** v6 reads descriptive performance direction
*inside* the brackets, not just the section name. A tester wrote
`[Bridge Female — Whispered, pitch drifting slightly on the hold…]` — and v6's own description of
the finished track named a "whispered French bridge", detail that appeared **nowhere in the Style
field**.

Consequence: **bare section headers waste the model's new capability.** Describe the delivery,
dynamics and instrumentation per section inside the bracket.

> This supersedes the old v5 advice ("Suno ignores descriptive sentences, use short hard cues").
> On v6 the richer bracket wins.

## Multimodal input (new in v6)

**[官方]** v6 generates from **text, audio, images or video**, and can combine sources in one
request.

This connects directly to this skill's delivery folder: the reference material archived in
`Image/` `Video/` `Audio/` is now usable as *input*, not just as documentation for a human.
For a CG brief, the PV footage and concept art can drive the generation instead of being described
in words. Mention this to the designer when the delivery folder contains media assets.

## Editing an existing result (new in v6)

**[官方]** Rather than re-rolling the whole track:
- **Rewrite one section in plain language** ("make the chorus a gospel choir") — the rest is untouched.
- **Mashup** elements from multiple sources in one request.
- **Sample** one instrument from a moment in a track and build around it.
- **Edit individual lyric lines** without regenerating the song.

This maps well onto Stage 3B-style iteration: a targeted fix beats a full re-roll.

## Evaluating output — read this before tuning a prompt

**[实测]** Take-to-take variance on v6 is large: in one controlled test the difference between the
two takes of a *single* generation exceeded the effect of a deliberate prompt change. Judging a
prompt edit from one take is measuring noise.

- Listen to **both takes** before concluding anything.
- When A/B-testing a prompt change, set **Variety to 0** so the only thing moving is your edit.
- Change **one** thing per generation.

## Instrumental / game music (this skill's main case)

- Put `Instrumental` in the Lyrics field, or use section tags + performance cues with no words.
- Put `vocals`, `humming`, `lyrics` in **Exclude Styles** — not in the Style box.
- Use bracketed section cues as hard instrument changes: `[High-Register Cello Solo]`,
  `[Majestic Brass Section]`, and now add the delivery direction inside the bracket.
- Tension/space vocabulary: `[Building Tension]`, `[Crescendo]`, `[Tremolo Strings]`,
  `[Wide Spatial Reverb]`.

## Hard rules (do / don't)
- ✅ **Variety = 0** whenever the prompt came from a requirement document.
- ✅ Structure tags in **Lyrics**, negatives in **Exclude Styles**, descriptors in **Style**.
- ✅ State an explicit BPM and an explicit ending.
- ✅ Write per-section performance direction inside the brackets — v6 reads it.
- ✅ Decompose artist / game / IP references into technical descriptors; they are filtered, and v6
  was trained with artist names stripped from metadata.
- ❌ No negatives inline in Style — they read as "include".
- ❌ No slider values typed into the prompt text.
- ❌ No narrative paragraphs in Style — it stays keyword/verb driven.
- ❌ Don't judge a prompt change on a single take.

## Output presentation (Chinese)
```
### 🎵 Suno 提示词方案（v6）

【模型】v6（精准）/ v6-wild（实验）  ← 按需求文档生成时选 v6

【滑杆设置】⚠️ 先设置再生成
- Variety: 0        （必须——否则 Suno 会自动改写你的 Style）
- Style Influence: 高于默认 50%
- Weirdness: 50%（中性基准）
- Max Mode: 定稿那次打开

【Style / 音乐风格】（粘到 Style 框，≤1000 字符）
<genre → vocals → drums → guitars → bass → 其他乐器 → 编排与能量 → 制作 → 结尾指令>

【Exclude Styles / 排除项】（粘到 Exclude 框，不要写进 Style）
<no vocals, humming, ...>

【Lyrics / 歌词与结构】（粘到 Lyrics 框，≤5000 字符）
[Intro — 具体演奏指示写在方括号里]
...
[End]

💡 调优建议：
- 两个 take 都听完再判断；测试改动时 Variety 保持 0
- ...
（依据：Suno v6 官方公告与 FAQ + 发布周实测，本适配器核对于 2026-09-11）
```

## Troubleshooting table
| Symptom | Likely cause | Fix |
|---|---|---|
| **Style 被自动改写 / 风格跑偏** | **Variety 滑杆默认开启，会改写你的 Style** | **Variety 拉到 0**（最常见的"v6 不听话"原因） |
| 明明排除了却还是出现 | 否定词写在了 Style 框 | 移到 Exclude Styles；写在 Style 里的否定词会被当成"要包含" |
| 出来很"通用"/没特点 | Style Influence 默认只有 50% | 调高；并把 tag 砍到 8–15 个、强特征前置 |
| 两次结果差很多，判断不了 | v6 take 间方差大 | 两个 take 都听；A/B 时 Variety=0、一次只改一处 |
| 结构乱、段落不对 | 结构标签放进了 Style，或没独占一行 | 移到 Lyrics，一行一个，标签在内容之前 |
| 段落表现力平淡 | 只写了裸标签 `[Verse]` | 在方括号内写演唱/演奏指示，v6 会读 |
| 节奏不对 | 没写 BPM | Style 里写明数字 BPM |
| 结尾拖尾 | 没写结尾指令 | Style 末尾写明结尾方式，Lyrics 末尾加 `[End]` |
| 过于保守/无聊 | Weirdness 被设成 0 | 0 是"更保守"，中性是 50 |
| 找不到旧模型 | v4–v5.5 已于 2026-09-09 全部退役 | 只能用 v6 系列；旧版提示词经验需重新验证 |
| 触发版权过滤 | 写了歌手/作品名 | 拆成流派+乐器+时代+制作技术词 |

## Changelog
- 2026-06-29 — Initial adapter from official help + verified v5.5 metatag references.
- 2026-09-11 — **Rewritten for the v6 family.** v4–v5.5 retired 2026-09-09, so the previous adapter
  targeted models that no longer exist. Added Creative Sliders (Variety=0 is now rule #1), the
  Exclude Styles field (negatives must move out of Style), per-section performance direction inside
  brackets, multimodal input, section-level editing, and the take-to-take variance caveat. Field
  limits confirmed unchanged (Style 1,000 / Lyrics 5,000).
