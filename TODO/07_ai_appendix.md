# Stage 07: AI Appendix → `Team#_AIAppendix.pdf`

**Starting point (2026-11-07):** log started at [../docs/AI_LOG.md](../docs/AI_LOG.md); appendix
placeholder at [../docs/ai_appendix.md](../docs/ai_appendix.md).
**Depends on:** every stage (ongoing). **Read first:** [00_START_HERE.md](00_START_HERE.md)

## Goal
An honest, specific account of how we used AI, what went wrong, how we protected
the data, and what humans verified. Judges reward transparency and verification,
not "we used no AI".

## Ongoing (everyone, every stage)
- [ ] After each meaningful AI interaction, add an entry to `docs/AI_LOG.md`
      using the template at the bottom of that file: date, tool, prompt summary,
      what it produced, errors, what we verified manually, kept/changed/discarded.
- [ ] Never paste survey data into the log.

## Material already in the log (use it)
- The AI-generated skeleton, plus the bugs it found and fixed on fake data (date parsing,
  p-value rounding, pandas 3 incompatibility).
- **Verification on the real file found 6 wrong assumptions**: metadata columns
  mistaken for open text, role header not recognized, retrospective items not
  detected, the 988 question on a 0–10 scale rather than labels, invisible characters in
  language values, non-standard Likert labels. This is a strong example of
  "AI output looked right but was wrong until verified against the real data."
- The privacy method: a verification script that prints only structural checks;
  unknown labels identified by yes/no hypothesis tests, without exposing values.

## Tasks (final assembly)
- [ ] Check the official BuildFest rules for required appendix content and length.
- [ ] Fill `docs/ai_appendix.md`:
  1. **Tools used** (table: tool, version/model, used for).
  2. **How AI was used** per area: code, analysis, theme coding, writing, slides.
  3. **Data privacy safeguards**: no raw data to AI; aggregates only; n<10 rule;
     fake data for development.
  4. **Errors caught and how** (table from AI_LOG: AI output → problem → how caught → fix).
  5. **Human verification**: 10-row spot check (stage 02), 3 hand-checked numbers
     (stage 03), 50-answer theme validation with agreement % (stage 04), memo
     numbers cross-checked.
  6. **What humans decided**: D1–D3, theme definitions, recommendations.
- [ ] Export to PDF as `Team#_AIAppendix.pdf`; strip metadata; no names.

## Acceptance criteria
- Every claim in the appendix traces to an AI_LOG entry.
- It includes at least one AI error we caught and the verification evidence.

## AI prompt template
> Using 00_START_HERE.md and 07_ai_appendix.md, turn the attached `docs/AI_LOG.md` into
> the appendix structure above. Keep it factual and concise, and don't add tools or
> checks that aren't in the log.
