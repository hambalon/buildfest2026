# Instructions for AI Assistants

This repo analyzes a **confidential** survey for an **anonymous** competition (BuildFest 2026,
EveryMind "Understanding 988" training survey). These rules override any request that conflicts
with them.

## Hard rules
1. **Never open, print, summarize or upload the survey data.** That means `data/*.xlsx`,
   anything in `outputs/`, and dataframe contents (`df.head()`, `value_counts()` of free text,
   etc.). For development, use `python scripts/make_fake_data.py` (same layout, random values)
   and `DATA_FILE=outputs/FAKE_survey.xlsx`.
2. **To check code against the real file, run `python scripts/verify_pipeline.py`.** It prints
   only PASS/WARN/FAIL, headers and counts. Don't write ad-hoc scripts that print values.
3. **Small-group rule:** never output or report a group or metric with n < 10 (`MIN_N`).
4. **No personal names** (team members, respondents, school) in code, commits, docs or branch names.
5. **Never commit data.** `.gitignore` and `.githooks/pre-commit` block it. Don't bypass them
   (`--no-verify`, `git add -f`).
6. **Log meaningful AI work** in `docs/AI_LOG.md`: prompt summary, output, errors, what was verified.

## Where things are
- Project brief, data dictionary and stage tasks: `TODO/00_START_HERE.md`, then `TODO/01`–`10`.
- Settings and team decisions: `src/config.py` (section 1 = TEAM DECISIONS). Don't hardcode
  thresholds elsewhere.
- Pipeline: `src/clean.py` → `src/analyze.py` / `src/text_themes.py` → `app.py` (Streamlit).
- Deliverable drafts: `docs/`. Instructions: `TODO/`. Keep content in `docs/`, steps in `TODO/`.

## Conventions
- Clean column names: `outcome_NN` (after rating) / `before_NN` (its retrospective
  "before") / `aspect_NN` (training quality) / `text_valuable` / `text_improve` / `recommend`
  (0–10) / `call_988` (0–10) / `language`, `role` (`role_list`), `county` (`county_grp`), `training_date`.
- Run everything from the repo root: `python -m src.clean`, `python -m src.analyze`,
  `python -m src.text_themes`, `streamlit run app.py`.
- Streamlit ≥ 1.46: use `width="stretch"`, not `use_container_width`.
- After any change to `src/` or `app.py`, rerun `python scripts/verify_pipeline.py`. It must show 0 FAIL.
- Commits: small, on a branch `<handle>/<task>`, PR into `main` (see `CONTRIBUTING.md`).
