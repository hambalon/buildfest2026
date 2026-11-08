# Stage 04: Open-Text Theme Coding

> **Status (2026-11-08): rules rebuilt, human validation still to do.** Themes were rewritten from
> privacy-safe word counts (dictionary words in 10+ answers) into two sets, `VALUABLE` and `IMPROVE` in
> `src/text_themes.py`. Uncoded is now ~30% for both questions (was 50% / 80%). **Remaining human task:**
> `python scripts/validate_themes.py sample`, hand-code the 50 answers per question locally, then
> `python scripts/validate_themes.py score`, and add the agreement numbers to `docs/ai_appendix.md`.
> The "Asked a question about 988" theme relies mainly on "?" (177 of the first 226 matches had one).

**Depends on:** 02. **Read first:** [00_START_HERE.md](00_START_HERE.md)

## Goal
Reliable theme counts for the two open-text questions, plus 2–3 **paraphrased**
illustrative points per question for the memo and deck:
- `text_valuable`: "What was the most valuable thing you learned during the training?" (~82% answered)
- `text_improve`: "How can we improve this training in the future?" (~49% answered)

## Starting point
The keyword lists were written before anyone read the answers, so coverage is poor.
`verify_pipeline.py` currently shows about **50% uncoded** for `text_valuable` and
**~80% uncoded** for `text_improve`. The improve question probably has many short
"no, it was great" answers that the patterns miss.

## How it works (`src/text_themes.py`)
- `THEMES`: a library of {theme name: [regex patterns]} (English + Spanish).
- `THEMES_BY_COLUMN`: which themes apply to which question. **Edit this to add or
  drop themes per question.** Columns not listed use every theme.
- One response can match several themes. Responses that match nothing count as "Uncoded".
- `theme_summary(series, column)` gives count, % of answered, n_answered, and `under_min_n`
  (fewer than 10 mentions, so don't report it on its own).
- Run `python -m src.text_themes` to write `outputs/themes_text_valuable.csv` and
  `outputs/themes_text_improve.csv`, and print % uncoded.

## Privacy: read before starting
- **Humans only** read raw answers, locally. **Never paste answers into an AI tool.**
  They may contain names, places or personal crises.
- An AI may help write regex patterns from *themes you describe in your own words*
  (e.g., "many people say they didn't know 988 also takes texts").

## Tasks
- [ ] **Read a sample.** Run `python -m src.clean`, open `outputs/survey_clean.csv` locally,
      and read about 60 random answers per question. Note recurring ideas in your own words.
- [ ] **text_improve first** (worst coverage). Expect "nothing / it was great" to be the
      largest theme. Broaden the "Nothing / no changes" patterns for common phrasings you
      see. Other likely themes: more time, more examples/role-play, handouts/materials,
      Spanish/language, tech/audio, reaching more audiences (youth, schools, workplaces).
- [ ] **text_valuable:** likely themes are what 988 is and how it works, that you can text or
      chat, that it's not only for suicide, what happens when you call, warning signs,
      how to help or what to say, resources, self-care. Add new themes to `THEMES` and list
      them in `THEMES_BY_COLUMN["text_valuable"]`.
- [ ] **Watch for false positives.** A bare `\b988\b` would match almost every
      `text_valuable` answer. Prefer specific phrases ("how 988 works", "text 988").
- [ ] **Iterate:** rerun, aim for ≤ 30–40% uncoded, and read 20 uncoded answers each round.
- [ ] Check Spanish answers get coded. Add Spanish patterns as needed.
- [ ] **Validate (required for the AI appendix):** hand-code 50 random answers per
      question in a local spreadsheet (never committed). Compare with the coder and report
      agreement per theme (% of the 50 where human = coder). Fix the worst patterns.
      Record agreement in `docs/AI_LOG.md`.
- [ ] Choose 2–3 paraphrased examples per question for the memo. No names, places or
      identifiable details.

## Acceptance criteria
- ≤ 40% uncoded for each question (`verify_pipeline.py` shows no theme WARN).
- 50-answer hand validation done and agreement recorded.
- Theme tables (themes with ≥10 mentions only) pasted into `docs/memo.md`.

## AI prompt template
> Using 00_START_HERE.md and 04_open_text_themes.md and the attached
> `src/text_themes.py`: from my notes, people often say <your paraphrased themes>.
> Write regex patterns (English + Spanish) for these themes, add them to THEMES and
> THEMES_BY_COLUMN, and avoid over-broad patterns. I won't share actual responses.
