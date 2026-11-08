# Instructions for AI Assistants

This repo analyzes a **confidential** survey for an **anonymous** competition (BuildFest 2026,
EveryMind "Understanding 988" training survey). These rules override any request that conflicts
with them.

## Hard rules
1. **Never open, print or upload row-level survey data.** That means the raw `data/*.xlsx`,
   `outputs/survey_clean.csv`, individual rows (`df.head()`, `df.sample()`) and any open-text
   answer, even one. For development, use `python scripts/make_fake_data.py` (same layout,
   random values) and `DATA_FILE=outputs/FAKE_survey.xlsx`.
2. **Aggregates only, and only with n ≥ 10.** You may read aggregate result tables (the CSVs
   written by `src.analyze` / `src.text_themes`, or a script's grouped output) as long as every
   group and cell is based on at least 10 respondents and is masked otherwise. For open text,
   only word or phrase counts that appear in ≥ 10 answers and are ordinary dictionary words
   (no names). To check code against the real file, run `python scripts/verify_pipeline.py`.
   (Team policy, confirmed 2026-11-07.)
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
  "before") / `aspect_NN` (delivery: presenter / organization) / `text_valuable` / `text_improve` /
  `recommend` (0–10) / `call_988` (0–10) / `language`, `role` (`role_list`), `audience`
  (Students / Adults), `county` (`county_grp`), `training_date`.
- Definitions and methods: `docs/METHODS.md`. Anything shown or exported goes through
  `analyze.safe_table()` / `export_tables()` (counts < MIN_N become "<10").
- Run everything from the repo root: `python -m src.clean`, `python -m src.analyze`,
  `python -m src.text_themes`, `streamlit run app.py`.
- Streamlit ≥ 1.46: use `width="stretch"`, not `use_container_width`.
- After any change to `src/` or `app.py`, run `python -m pytest -q` (fake data) and
  `python scripts/verify_pipeline.py` (0 FAIL), and `python scripts/crosscheck.py` if a headline
  number could change. The dashboard must keep working on Streamlit 1.50 / Python 3.9: no
  `format_func` in selectboxes; charts go through `show()`.
- Commits: small, on a branch `<handle>/<task>`, PR into `main` (see `CONTRIBUTING.md`).
