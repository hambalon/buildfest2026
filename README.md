# BuildFest 2026: 988 Training Survey Analysis

This repo analyzes the EveryMind 988 training survey: about 1,300 responses with
language, role, county, six Likert items, three retrospective "before the
training" items, a 0–10 recommend score, likelihood of calling 988, and two
open-text questions.

> **The data is confidential and is never committed.** See [data/README.md](data/README.md).
> Judging is anonymous, so no personal names go anywhere in this repo.
> See [CONTRIBUTING.md](CONTRIBUTING.md).

**New here?** Do the setup below, then open [TODO/00_START_HERE.md](TODO/00_START_HERE.md):
it has the data dictionary and one task file per project stage. Using an AI assistant?
It must follow [AGENTS.md](AGENTS.md).

## Repo layout

```
app.py                  Streamlit dashboard (reads whatever .xlsx is in data/)
src/config.py           Settings: small-group threshold, scales, column overrides
src/clean.py            Load + clean the survey, write a cleaning report
src/analyze.py          Before/after change; results by county, role, language
src/text_themes.py      Keyword theme coding of the two open-text questions
scripts/verify_pipeline.py  Checks the pipeline works on the data (prints no results)
scripts/make_fake_data.py   Generates FAKE data (same layout as the real file) for testing
TODO/                   Step-by-step task files for each project stage (human- and AI-readable)
data/                   Put the .xlsx here (gitignored)
outputs/                Generated tables and reports (gitignored)
notebooks/              Scratch analysis (clear outputs before committing; see notebooks/README.md)
docs/                   Deliverable drafts: memo, AI appendix, deck outline, AI log, submission checklist
AGENTS.md, CLAUDE.md    Rules for AI coding tools
.githooks/pre-commit    Blocks data files from being committed
```

## 1. Setup (once)

You need Python 3.11 or newer. Check with `python3 --version`.

**macOS / Linux**
```bash
git clone <repo-url>
cd buildfest2026
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
git config core.hooksPath .githooks   # turns on the data-leak guard
```

**Windows (PowerShell)**
```powershell
git clone <repo-url>
cd buildfest2026
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
git config core.hooksPath .githooks
```

Then copy `BuildFest_EveryMind_Survey_Data_FULL.xlsx` into `data/`.

Activate the environment (`source .venv/bin/activate`) every time you open a new terminal.

## 2. Verify, then run the cleaning

Run every command from the repo root. First confirm the pipeline understands the file.
This prints only PASS/WARN/FAIL checks, column headers and counts, never results:

```bash
python scripts/verify_pipeline.py
```

Expected on the current file: **0 FAIL**, with WARNs only for the known items listed in
[TODO/02_cleaning_and_validation.md](TODO/02_cleaning_and_validation.md). Then:

```bash
python -m src.clean          # clean + write outputs/cleaning_report.md
python -m src.analyze        # write outputs/overall.csv, retro_change.csv, by_*.csv
python -m src.text_themes    # write outputs/themes_text_valuable.csv, themes_text_improve.csv
```

**Read the cleaning report the first time you run it.** It shows which column was
detected as what, and which "before" item was paired with which "after" item.
If something is wrong, pin it in [src/config.py](src/config.py) with
`COLUMN_OVERRIDES` or `RETRO_PAIR_OVERRIDES`, then rerun.

Console output contains only counts and column headers, never individual responses.

## 3. Run the dashboard

```bash
streamlit run app.py
```

It opens at http://localhost:8501. The dashboard reads the newest `.xlsx` in `data/`
and reloads when that file changes, so an updated export needs no code changes.

## Testing without the real data

```bash
python scripts/make_fake_data.py
DATA_FILE=outputs/FAKE_survey.xlsx python -m src.analyze
DATA_FILE=outputs/FAKE_survey.xlsx streamlit run app.py
```

On Windows PowerShell, set the variable first: `$env:DATA_FILE="outputs/FAKE_survey.xlsx"`.

## Method notes

| Topic | Rule |
|---|---|
| Likert → numbers | Strongly disagree = 1 … Strongly agree = 5. "% agree" = Agree + Strongly agree. Spanish labels included. |
| 988 likelihood | In the current file this is a **0–10** scale answered by only ~23% of respondents (added to the form later). "% likely" = score ≥ 7 (`CALL_988_LIKELY_MIN_0_10`). Always report its own n. Label scales (Very unlikely … Very likely) are also supported. |
| Recommend | 0–10. NPS = % 9–10 minus % 0–6. |
| Before/after | Retrospective pre-test: "before" and "after" are both reported after the training. Change = after − before, using only people who answered both. Wilcoxon signed-rank p-value included. |
| Missing | Blank, "None", "N/A" and similar become missing. Every statistic reports its own n. Two non-standard labels on the training-aspect items ("Very agree", "Satisfied") are excluded by default (see `src/config.py`). |
| Small groups | Groups with **n < 10** are suppressed (values hidden, `suppressed = True`). Within a group, each metric is also blanked if fewer than 10 people answered *that* question (`n_recommend`, `n_988`, `n_retro` columns). County and language values with < 10 responses are folded into "Other (n<10)". |
| Roles | Multi-select. A respondent who picked two roles counts in both role groups. |
| Text themes | Keyword rules, multi-label. A first pass only: validate by hand before quoting. |

Change thresholds in [src/config.py](src/config.py), not in the scripts.

## Deliverables

See [docs/SUBMISSION_CHECKLIST.md](docs/SUBMISSION_CHECKLIST.md). Log AI use as you go in
[docs/AI_LOG.md](docs/AI_LOG.md).
