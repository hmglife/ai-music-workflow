# Adapter — Lyria (Google, current: Lyria 3.5)

| | |
|---|---|
| **Official source** | Gemini API music-generation docs: https://ai.google.dev/gemini-api/docs/music-generation (updated 2026-09-04) ｜ DeepMind model card: https://deepmind.google/models/model-cards/lyria-3-5 |
| **Model version** | **Lyria 3.5** (`lyria-3.5`) + **Lyria 3 Clip** (`lyria-3-clip-preview`) |
| **Last checked** | 2026-09-11 |

> Everything in this adapter is from Google's own developer documentation — no community guesswork.
> Lyria 3.5 shipped in Google Flow Music on 2026-07-29 and reached the Gemini app + API on
> 2026-09-04. It is reachable via the Gemini app, Google Flow Music, Google AI Studio and Google Vids.
>
> When a newer Lyria appears, re-fetch both pages above, update the rules, bump the header + Changelog.

---

## The two models

| Model | Model ID | Best for | Duration | Output |
|---|---|---|---|---|
| **Lyria 3 Clip** | `lyria-3-clip-preview` | short clips, loops, previews | **always 30 s** | MP3 |
| **Lyria 3.5** | `lyria-3.5` | full songs with verses / choruses / bridges | a couple of minutes, **prompt-controllable** (up to ~3 min) | MP3 default, **WAV available** |

Both take **text and images**, and output **44.1 kHz stereo**.

**Official best practice — iterate cheap:** *"Use the faster `lyria-3-clip-preview` model to
experiment with prompts before committing to a full-length generation with `lyria-3.5`."*

**⚠️ Delivery-spec gap:** Lyria outputs **44.1 kHz**. Briefs in this workflow typically specify
**WAV 48 kHz 24-bit + stems**. Lyria can give WAV (via `response_format` on `lyria-3.5`) but **not
48 kHz, and not stems**. Treat Lyria output as demo / reference material, or resample and state
that it was resampled — never pass it off as meeting a 48 kHz deliverable.

---

## How Lyria prompting works (key difference vs Suno)

Lyria takes **one natural-language prompt**, not separate fields. Before generating, the model
**reasons through musical structure** (intro / verse / chorus / bridge) based on your prompt, which
is what gives it structural coherence. It also runs an **internal prompt rewriter** to interpret
natural language — but unlike Suno's Variety slider, this is not user-configurable and Google notes
it does **not** expose intermediate "thought" blocks.

So: write rich descriptive prose, not a Suno-style comma tag list. Both simple and detailed prompts
work; detail buys control.

## Timestamps — the feature that matches a CG brief exactly

**This is the highest-value part of this adapter for cutscene work.** Google documents an explicit
timestamp syntax for controlling *what happens when*:

```
[0:00 - 0:10] Intro: Begin with a soft lo-fi beat and muffled vinyl crackle.
[0:10 - 0:30] Verse 1: Add a warm Fender Rhodes piano melody and gentle vocals
              singing about a rainy morning.
[0:30 - 0:50] Chorus: Full band with upbeat drums and soaring synth leads.
[0:50 - 1:00] Outro: Fade out with the piano melody alone.
```

Official wording: *"You can specify exactly what happens at specific moments in the song using
timestamps. This is useful for controlling when instruments enter, when lyrics are delivered, and
how the song progresses."* Timestamps also **control duration**.

**Why this matters here:** the CG requirement template's timeline block (`0-Xs` / `X-Ys` / `Y-Zs`
rows) maps onto this **one-to-one**. When generating a Lyria prompt from a CG brief, translate each
timeline row into one `[m:ss - m:ss] Section: description` line instead of flattening the timeline
into prose. That is the single biggest quality lever for sync-critical cutscene music.

Looser one-off timing also works: *"Build to a drop at 12s"*, *"The chorus kicks in at 22s"*,
*"Someone says 'what' every 2 seconds"*.

## What to specify

- **Genre first** — lead with it. Blends are encouraged ("a fusion of metal and rap", "a classical
  piece with electronic drone elements"). Eras work ("early 90s hip-hop", "60s French ye-ye pop").
  Bespoke/regional variants ("Berlin techno") are attempted but may miss.
- **Instruments** — defaults suit the genre, so you only need to name what you specifically want
  ("a saxophone solo should come in during the bridge"). Describing how instruments *interact*
  creates texture: *"a dirty, distorted bassline fighting against clean, crisp hi-hats"*,
  *"warm, analog synthesizer pads swelling underneath a dry, intimate acoustic guitar"*.
- **Song structure** — arrows or a list:
  `[Intro]` -> `[Verse 1]` -> `[Chorus]` -> `[Bridge]` -> `[Outro]`, or describe the flow in prose
  ("start with a quiet piano intro, build into a loud verse, drop into silence, then explode into
  the chorus").
- **Energy changes between sections** — "build tension in the pre-chorus, then drop to silence
  before a massive, explosive chorus"; "gradual crescendo, adding one instrument at a time".
- **BPM** — "120 BPM", "slow tempo around 70 BPM".
- **Key / scale** — "in G major", "D minor".
- **Mood** — "nostalgic", "aggressive", "ethereal", "dreamy".
- **Duration** — Clip is fixed at 30 s; for `lyria-3.5` state it ("create a 2-minute song") or let
  timestamps define it.

## Vocals

Official guidance: *"specify a detailed singer profile covering gender, timbre, and vocal range."*
Google's own archetypes:

- **Female Soprano** — clear, crystalline timbre, agile and soaring; whistly high notes, airy breathy texture.
- **Female Alto** — rich, warm, husky lower range; smoky with a touch of vocal fry, soulful.
- **Male Tenor** — bright, piercing, energetic; youthful with a slight nasal edge, high belting power.
- **Male Baritone** — deep, chocolatey, velvet-smooth; resonant chest voice, crooning delivery.
- **Weathered Rocker (Male)** — raspy, gravelly, 90s grunge; strained upper range for intensity.

## Lyrics

- Vocals and lyrics are generated **by default**.
- **Your own lyrics**: include them after a `Lyrics:` prefix, with section tags:
  ```
  Lyrics:

  [Intro]
  Oooh, oooh

  [Verse 1]
  Let's go
  Go with the flow
  ```
  Section titles: `[Intro]` `[Verse 1]` `[Pre-chorus]` `[Chorus]` `[Outro]`.
- **Echo / backing singers**: put the repeat in round brackets — `Let's go (go)`.
- **Let Lyria write them**: state what they should be about, or the model infers a subject from the
  music prompt and may guess wrong. Ask explicitly for a repeating chorus if you want one.
- **Language**: lyrics come out in the language you prompt in; the model adapts vocal style and
  pronunciation. You can also ask ("Write the lyrics in French").
- **Non-lyric vocal events** are promptable: *"right before the drop the sound all stops and a
  little voice says '…', then the music drops."*
- **Separate lyrics from musical direction** — official best practice.

## Instrumental (this skill's main case)

Official example: *"A bright chiptune melody in C Major, retro 8-bit video game style.
**Instrumental only, no vocals.**"* — state it plainly in the prompt; there is no separate field.

## Images as input

**Up to 10 images** can be supplied alongside the text prompt; the model composes music inspired by
the visual content. This pairs directly with this skill's delivery folder — concept art and key
visuals archived in `Image/` can be fed in rather than only described. Only use it when the
designer actually provided images.

**No audio input.** Inputs are text and images only. If the designer wants a temp track to drive
the result, Lyria is the wrong tool — steer them to a platform that accepts audio upload.

## Avoiding the "commercial / obviously-AI" sound (from designer feedback, 2026-06-29)
Lyria's default drifts toward a generic, synth-tinged "commercial film" sound. For a high-end,
human, acoustic result:
1. Demand **live / acoustic / real-recorded** instruments; name them and add playing techniques
   (rubato, con sordino, sul ponticello, tremolo).
2. Add **negative constraints**: "no pop, no electronic, no synths, no modern pop production,
   not commercial."
3. Add **texture/era words**: "intimate room ambience, natural dynamics, organic and human,
   slightly imperfect, analog warmth, vintage film-score grain."

## Official limitations (tell the designer these)
- **Safety filters** block prompts requesting specific artist voices or copyrighted lyrics.
- **SynthID watermark** on *all* generated audio — imperceptible, but every track is identifiable
  as AI-generated. Relevant before anything ships in a game build.
- **Single-turn only** — *"Iterative editing or refining a generated clip through multiple prompts
  is not supported."* Re-run with a revised prompt. (Contrast: Suno v6 *can* edit a section.)
- **Length** — Clip fixed at 30 s; `lyria-3.5` a couple of minutes, prompt-influenced.
- **Non-deterministic** — *"Results may vary between calls, even with the same prompt."*

## Hard rules (do / don't)
- ✅ Write **descriptive natural language**, not a comma tag list (opposite of Suno).
- ✅ **Translate a CG timeline into `[m:ss - m:ss]` lines** rather than prose.
- ✅ Lead with genre; state BPM, key, and specific instruments.
- ✅ Prototype on `lyria-3-clip-preview`, then commit on `lyria-3.5`.
- ✅ Say "Instrumental only, no vocals." when there should be no singing.
- ✅ Flag the 44.1 kHz / no-stems gap against the brief's delivery spec.
- ❌ Don't expect audio-reference conditioning — text + images only.
- ❌ Don't plan on iterating a generated clip; each run is single-shot.
- ❌ Don't reference copyrighted artists / IP; describe the technical and era signature instead.
- ❌ Don't lean on Suno-style `[]` voice/energy metatags — Lyria prefers prose for delivery and
  dynamics (structure tags are fine).

## Output presentation (Chinese)
```
### 🎵 Lyria 提示词方案（Lyria 3.5）

【模型】lyria-3.5（完整曲目）／lyria-3-clip-preview（30 秒试听，先用它试提示词）

【Prompt / 自然语言提示词】（粘到 Gemini 应用或 API input）
<流派+时代 → BPM → 调性 → 具体乐器与相互关系 → 情绪 → 段落能量流动>

[0:00 - 0:0X] Intro: <这一段发生什么>
[0:0X - 0:YY] <Section>: <这一段发生什么>
...
Instrumental only, no vocals.      ← 纯音乐时写明

（如需人声，另起 Lyrics: 区块，并给出详细 singer profile）

⚠️ 交付提醒：Lyria 输出 44.1kHz，且不提供分轨；若需求是 WAV 48kHz 24bit + Stem，
   只能当 demo / 参考，不能直接当交付。所有输出含 SynthID 水印。

💡 调优建议：
- ...
（依据：Google 官方 Gemini API 音乐生成文档，本适配器核对于 2026-09-11）
```

### Worked example shape (CG timeline → timestamps)
> An epic cinematic orchestral piece at 92 BPM in D minor, in the Japanese anime film-score
> tradition. Live orchestra, no synths.
>
> [0:00 - 0:08] Intro: a lone cello in the low register, sparse and tense, faint timpani pulse.
> [0:08 - 0:20] Build: warm strings enter and rise, French horn states the main theme.
> [0:20 - 0:32] Climax: full orchestra with timpani and choir, wide hall reverb, then a hard stop.
>
> Instrumental only, no vocals. Intimate room ambience, natural dynamics, organic and human.

## Troubleshooting table
| Symptom | Likely cause | Fix |
|---|---|---|
| 卡点对不上画面 | 用散文描述了时间轴 | 改用官方 `[0:00 - 0:10] Section: ...` 时间戳语法，逐段对应 CG 时间轴行 |
| 输出只有 30 秒 | 用的是 Clip 模型 | 换 `lyria-3.5`，并在提示里写时长或用时间戳 |
| 结构平淡、没起伏 | 没描述段落能量变化 | 写清"安静钢琴→爆发副歌"这类流动 |
| 乐器不对 | 乐器写得太泛 | 指名具体乐器，并描述乐器之间的关系 |
| 人声不对 | 没写 singer profile | 按官方档案写性别/音域/音色 |
| 想要和声没出来 | 没用圆括号 | `Lyrics:` 里用 `(round brackets)` 标注回声/和声 |
| 节奏/调性飘 | 没明确 BPM/key | 写明 "92 BPM"、"D minor" |
| 想用参考曲驱动 | Lyria 不接受音频输入 | 只能文字+图片；需要音频条件化就换平台 |
| 想改一段却得重跑 | Lyria 单轮生成，不支持迭代编辑 | 改提示重跑；需要局部改写就用 Suno v6 |
| 同样提示结果不同 | 官方明示非确定性 | 多跑几次挑，或用 Clip 先快速筛提示词 |
| 交付被打回 | 44.1kHz、无分轨、带 SynthID 水印 | 当 demo 用；正式交付走音乐公司或重制 |
| 像某作曲家被拒 | 引用了版权艺人/IP | 拆成时代+编制+技法的技术描述 |

## Changelog
- 2026-06-29 — Initial adapter from DeepMind Lyria prompt guide + Gemini API docs.
- 2026-06-29 — Confirmed inputs = text + images only, no audio upload, no multi-turn editing. Added
  "avoiding the commercial/AI sound" rules from designer feedback.
- 2026-09-11 — **Updated to Lyria 3.5** (was Lyria 3; model ID `lyria-3-pro-preview` no longer the
  current id). Added the official **timestamp syntax** and mapped it onto the CG timeline block —
  the most useful addition for cutscene work. Added the Clip-first iteration practice, official
  singer-profile archetypes, WAV output on `lyria-3.5`, and the explicit
  **44.1 kHz / no-stems / SynthID** delivery caveats. File renamed `lyria3.md` → `lyria.md` so the
  version lives in the header, not the filename.
