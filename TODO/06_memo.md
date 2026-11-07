# Stage 06: Memo → `Team#_Memo.pdf`

**Starting point (2026-11-07):** placeholder at [../docs/memo.md](../docs/memo.md). **Depends on:** 03, 04.
**Read first:** [00_START_HERE.md](00_START_HERE.md)

## Goal
A short, decision-oriented memo to EveryMind: what the survey shows about the
"Understanding 988" training and what they should do next.

## Before writing
- [ ] **Check the official BuildFest rules** for page/word limits, required sections,
      font or format requirements, and the team-number format. This file doesn't know
      them; don't guess. Add them here once known.
- [ ] Have the stage 03 findings note and the stage 04 theme tables ready (aggregates only).

## Structure (fill the matching headings in `docs/memo.md`)
1. **Bottom line** (2–3 sentences): the single most important finding and the
   single most important recommendation.
2. **Key findings** (4–6 bullets, each with n):
   - Before→after change on the 3 outcome items (% agree before vs after; % improved).
   - Likelihood to call 988 (n≈293 subset; say so) and recommend/NPS (n≈1,266).
   - Training quality (presenter engagement, knowledge, organization).
   - Group differences by county / role / language (only n≥10; descriptive).
   - What participants valued most and want improved (top themes, %).
3. **Recommendations** (3, each tied to a finding): e.g., where to expand,
   what content to strengthen, survey improvements. **Recommend fixing the survey
   instrument**: make the 988 question required, keep one consistent agree scale
   (the old "Very agree"/"Satisfied" labels), and use single-select or a clear
   multi-select for role.
4. **Methods & limitations** (short): n, date range, cleaning summary, retrospective
   pre-test caveat, 988 subset, n<10 suppression, keyword theme coding validated
   on 50 hand-coded answers, decisions D1–D3 from stage 02.

## Style
- Audience: nonprofit program staff, not statisticians. Plain language, active voice.
- Lead with percentages ("82% agreed after vs 41% before"), then means.
- No causal claims ("the training caused…"). Use "participants reported…".
- No names, no identifying quotes, no team member names. "Team #" only.

## Export
- [ ] Convert to PDF (VS Code Markdown PDF extension, Pandoc
      `pandoc docs/memo.md -o Team#_Memo.pdf`, or paste into Docs/Word → PDF).
- [ ] Remove author metadata (Word: File → Info → Inspect Document; PDF: check Properties).
- [ ] Name it `Team#_Memo.pdf` with our number.

## Acceptance criteria
- Every number matches `outputs/*.csv` and has its n.
- Within the official length limit. Checked by a second teammate.

## AI prompt template
> Using 00_START_HERE.md and 06_memo.md, plus these aggregate findings `<paste the
> findings note + theme table>`, draft the memo in Markdown following the structure.
> Use only the numbers I gave you, invent nothing, and mark any gap as [TODO].
