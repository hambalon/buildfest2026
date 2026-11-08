# Stage 02: Cleaning and Validation

**Depends on:** 01. The code is verified structurally on the real file (0 FAIL); a human must
still do the manual checks below. **Read first:** [00_START_HERE.md](00_START_HERE.md)

## Goal
Trust the cleaned dataset. Every column is correctly identified, every answer
converts to the right number, and a human has spot-checked it against the raw Excel.

## What `src/clean.py` does (already built)
1. Loads the newest `.xlsx` in `data/` (or `--file` / `DATA_FILE`).
2. Normalizes text: Unicode NFKC, non-breaking spaces (1,947 cells), invisible
   left-to-right marks, whitespace runs, trailing/stray semicolons (100 cells).
   Placeholders like "None", "N/A" or "-" become missing (14 cells).
3. Detects column roles from headers and values (table in 00_START_HERE §4).
   Platform metadata (Id, Start/Completion time) is ignored.
4. Converts agree/disagree labels to 1–5 (English + Spanish), recommend and 988 to
   0–10, and dates to dates. Splits multi-select roles into `role_list`.
5. Adds `county_grp` / `language_grp`: missing becomes "Not reported", values with n<10 become "Other (n<10)".
6. Pairs each retrospective "before" item with its "after" item by sub-item text.
7. `python -m src.clean` writes `outputs/survey_clean.csv`, `clean_meta.json` and
   `cleaning_report.md` (all gitignored).

## Current verification status (`python scripts/verify_pipeline.py`)
0 FAIL, 5 known WARNs:

| WARN | Meaning | Action |
|---|---|---|
| aspect_01/02/03 unmapped labels (~23 answers each) | The three training-aspect items contain two non-standard labels, **"Very agree"** (14 respondents) and **"Satisfied"** (11 respondents), probably from an older form version. They are excluded (missing). | **Decided (D1): option A**, kept as missing |
| text_valuable / text_improve high % uncoded | Theme keywords were written before anyone read the answers | Stage 04 |

## Tasks

### Decisions (record each one in `docs/AI_LOG.md` and the memo's methods section)
- [x] **D1: Non-standard labels.** *(Decided 2026-11-07: option A.)* Option A (default): exclude as missing, about 2% of
      those items. Option B: map "Very agree" to 5 and "Satisfied" to 4 by uncommenting
      the line in `AGREE_SCALE` in `src/config.py`. Recommendation: A. The ordering
      of "Satisfied" on an agree scale is ambiguous, and items 04–06 are secondary.
      Set `NONSTANDARD_AGREE_LABELS` in `src/config.py` (section 1). Either way, mention it in the methods section.
- [ ] **D2: 988 "likely" cutoff.** `CALL_988_LIKELY_MIN_0_10 = 7` (7–10 = likely).
      Alternative: 9–10 ("very likely", NPS-style). Pick one and use it everywhere.
- [x] **D3: Duplicate rows.** The report shows the exact-duplicate count; duplicates are kept.
      If it's not 0, check by Id/time locally whether they are real double submissions.
      *(Checked 2026-11-07: 0 exact duplicates, nothing to decide.)*

### Manual checks (human only, on your own machine; never share the rows)
- [x] Run `python -m src.clean` and read `outputs/cleaning_report.md` end to end.
- [x] Open the raw Excel and `outputs/survey_clean.csv` side by side. For **10 random
      rows**, check that each Likert label matches its number, the date matches, the
      county matches, and multi-select roles split correctly. *(Done 2026-11-07: rows 5, 100,
      250, 400, 550, 700, 850, 1000, 1150, 1290; all 10 match.)*
- [x] Confirm the three before/after pairs (`before_01`↔`outcome_01`, etc.) by reading the full question text.
- [x] Check that the counts of non-missing values per column in Excel (COUNTA) match the
      `missing/unparseable` lines in the report.
- [x] Check when the 988 question started being answered: in Excel, filter
      `call_988` non-blank and look at the earliest training date. Write the date
      range (not the rows) in the memo limitations section. *(First answered 2026-04-08.
      Memo line still to add.)*
- [x] Look at the 10 county names in the report file. Are any spelling variants of
      the same county? If so, add a mapping. *(Done: variants are merged automatically in
      `clean.standardize_county`, 10 → 7 names; `COUNTY_ALIASES` in config.py for any others.)*
- [x] Open-text "None"/"N/A" answers are kept as answers in the text columns
      (`TEXT_ANSWER_TOKENS` in config.py), not dropped as missing.
- [x] Record what you checked and what you found in `docs/AI_LOG.md` ("Verified manually").

## Acceptance criteria
- `verify_pipeline.py`: 0 FAIL, and every WARN has a recorded decision.
- 10-row spot check done with 0 mismatches (or mismatches fixed and re-checked).
- Decisions D1–D3 are written in `docs/AI_LOG.md`.

## Pitfalls for AI assistants
- Don't ask for or invent sample rows. Use `scripts/make_fake_data.py` for development.
- Don't change thresholds inside scripts. Change `src/config.py`.
- `COLUMN_OVERRIDES` / `RETRO_PAIR_OVERRIDES` in `config.py` take **exact raw
  headers** (after whitespace normalization). Get them from `verify_pipeline.py` output.
- After any change, rerun `python scripts/verify_pipeline.py` and paste back only its output.

## AI prompt template
> Using 00_START_HERE.md and 02_cleaning_and_validation.md, plus `src/clean.py` and
> `src/config.py` (attached), implement <task, e.g. COUNTY_ALIASES>. Test it against
> the fake data layout. Give me the diff and the command to verify. I'll paste back
> the `verify_pipeline.py` output only.
