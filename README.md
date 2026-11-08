# 988 Training Insights

A free, local dashboard and analysis pipeline that turns EveryMind's **988 awareness training
survey** (the Microsoft Forms export) into the answers program staff need:

- **Is the training working?** Knowledge before vs. after, with significance tests.
- **Will people act?** Likelihood to call 988, and how it relates to what they learned.
- **For whom does it work less well?** Students vs. adults, counties, roles, language, with
  small groups protected.
- **Is quality holding up?** Quarterly and monthly trends, plus a **session scorecard** that
  flags trainings for follow-up.
- **What do participants say?** Themes in the two open-ended questions.

Every number is an aggregate. Any group based on fewer than **10** people is hidden, results
from 10–29 people are flagged as *thin*, and no individual response is ever shown or exported.
A new survey export (`.xlsx` or `.csv`) works with **no code changes**: drop it in, or upload
it in the dashboard.

> **Confidential data:** the survey file never leaves your computer and is never committed
> to git (see [data/README.md](data/README.md)).

---

## Quick start (EveryMind staff, no coding)

1. **Install Python** (one time): from [python.org/downloads](https://www.python.org/downloads/),
   version 3.9 or newer. On Windows, tick **"Add python.exe to PATH"** during install.
2. **Get this folder** onto your computer (download the zip and unzip it).
3. **Put the survey export in the `data/` folder** (see [Updating the data](#updating-the-data)).
   You can also skip this and upload the file in the dashboard.
4. **Double-click the launcher:**
   - macOS: `start_dashboard.command` (first time: right-click → Open → Open, to allow it)
   - Windows: `start_dashboard.bat`

   The first run installs everything (2–5 minutes). After that it opens in seconds. The
   dashboard opens in your browser at http://localhost:8501. Close the black terminal
   window to stop it.

## Quick start (command line)

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Tested on Python 3.9 and 3.14 (macOS); runs anywhere Python and a web browser run.

## Updating the data

1. In Microsoft Forms, open the survey → **Responses** → **Open results in Excel**, and save
   the `.xlsx` (a `.csv` export works too). Don't edit it: the tool cleans it.
2. Either save it into `data/` (the newest `.xlsx`/`.csv` there is used), or click **Use a
   different survey export** in the dashboard sidebar.
3. Check **Data quality & methods → How the file was read** after each new export. It lists
   which column was recognized as what.

**If the form changes,** detection usually still works. The automated tests cover these
updates: reordered or renamed columns, an extra question, a missing role / date / 988 /
delivery / open-ended question, text-formatted dates, new counties and roles, a Spanish-only
file, a tiny file, and a CSV export. If a column is misread, pin it in `src/config.py` → `COLUMN_OVERRIDES`, then run
`python scripts/verify_pipeline.py` to confirm (0 FAIL). See the troubleshooting table below.

## Using the dashboard

The **Summary** tab opens with a **guide to every tab** (the question each one answers and
what you'll find there), and each tab starts with that same one-line purpose. **What the
data says** is written automatically from the current data and filters. It is grouped
into *What's working*, *Gaps to act on*, *What to watch* and *Data caveats*, and each
point carries its numbers, its n and a suggested action.

The **sidebar** has filters (audience, language, county, role, training dates), an upload box
(`.xlsx` or `.csv`) and **Download summary (Excel + CSV)**: privacy-safe tables for grant
reports and board updates. Charts work in light and dark mode.

| Tab | Answers | Look for |
|---|---|---|
| **Summary** | The headline results in five numbers, plus auto-written takeaways | "What the data says" updates itself for new data and filters |
| **Knowledge gains** | Did self-rated knowledge rise on each statement? | Before vs. after % agree; % who rated themselves higher; ceiling note |
| **Intent to call 988** | How likely are people to call, and does knowledge relate to intent? | The gap between those who do and don't agree they know when to use 988 |
| **Audiences & communities** | Where does the training land less well? | Turn on **Split by audience** before comparing counties; read the plain-language test verdicts |
| **Trends & sessions** | Is quality stable over time? Which sessions need follow-up? | Session scorecard flags (thresholds in `src/config.py`) |
| **Participant voice** | What did people value, and what would they change? | Compare students vs. adults |
| **Data quality & methods** | Can the numbers be trusted? | Quality checks, robustness table, cleaning report, definitions |

**Suggested routine:** run it monthly (or after each batch of trainings). Review the session
scorecard with facilitators, and use the quarterly Summary + download for reporting. It takes
about 15 minutes per month.

## Command-line tools

| Command | What it does |
|---|---|
| `python -m src.analyze` | Writes every result table to `outputs/` plus a shareable `outputs/summary_report.xlsx` (counts < 10 hidden) |
| `python -m src.text_themes` | Writes theme tables for the open-ended questions |
| `python scripts/verify_pipeline.py` | Checks the pipeline understands a (new) file. Prints structure only, never results |
| `python scripts/crosscheck.py` | Recomputes 12 headline numbers with independent code and compares them |
| `python scripts/validate_themes.py sample` / `score` | Blind human check of the theme coder (see below) |
| `python scripts/make_fake_data.py` | Creates a FAKE file with the same layout, for demos and testing |
| `python -m pytest -q` | 31 automated tests on fake data, including 9 data-update scenarios (`pip install -r requirements-dev.txt` first) |
| `python scripts/build_deliverables.py --team N` | Builds the BuildFest PDFs and artifact zip with checks |

Run them from this folder with the environment active. Add `--file path/to/file.xlsx` to the
scripts, or set `DATA_FILE=...`, to use a specific file.

### Checking the open-ended themes

1. `python scripts/validate_themes.py sample` writes `outputs/theme_validation.xlsx`: 50
   random answers per question, without the coder's labels.
2. A staff member marks 1 under each theme that applies. Do this locally, and never paste
   answers into AI tools.
3. `python scripts/validate_themes.py score` reports agreement, precision and recall per theme.
   Improve weak rules in `src/text_themes.py` and repeat.

## Settings (`src/config.py`)

| Setting | Default | Meaning |
|---|---|---|
| `MIN_N` | 10 | Small-group privacy threshold |
| `THIN_N` | 30 | Results from `MIN_N` to `THIN_N − 1` people are shown but flagged *thin* |
| `CALL_988_LIKELY_MIN_0_10` | 7 | "Likely to call 988" = score of 7 or more |
| `NONSTANDARD_AGREE_LABELS` | `{}` | Map odd labels (e.g. "Very agree") instead of treating them as missing |
| `YOUTH_ROLE_KEYWORDS` | student | Which roles count as the Students audience |
| `SESSION_ALERT_*` | NPS < 0, knowledge < 85%, delivery < 80% | Session scorecard flags |
| `TREND_PERIOD` | Q | Quarter (Q) or month (M) for exported trend tables |
| `COUNTY_ALIASES`, `COLUMN_OVERRIDES`, `RETRO_PAIR_OVERRIDES` | empty | Manual fixes if a new export is read wrongly |
| `SHORT_LABELS` | knowledge/delivery items | Chart labels only |

Full definitions and statistical methods: [docs/METHODS.md](docs/METHODS.md).

## Troubleshooting

| Problem | Fix |
|---|---|
| "No survey file found" | Put the `.xlsx` in `data/` or upload it in the sidebar |
| "This file could not be read" | Use the original Forms export (.xlsx, one sheet). Re-export if it was edited |
| A chart or group is missing | It has fewer than 10 responses in the current view. Remove a filter |
| A result says *thin* | It is based on 10–29 people: treat it as indicative, not conclusive |
| A column looks wrong after a form change | Run `python scripts/verify_pipeline.py`, then set `COLUMN_OVERRIDES` in `src/config.py` |
| macOS says the launcher "can't be opened" | Right-click `start_dashboard.command` → Open → Open |
| Port 8501 busy | `streamlit run app.py --server.port 8502` |

## Project structure

```
app.py                      The dashboard
start_dashboard.command/.bat One-click launchers (macOS / Windows)
src/config.py               All settings and team decisions
src/clean.py                Load + clean any export (column detection, scales, dates, counties, audience)
src/analyze.py              All measures, group tests, trends, intent gap, session scorecard, quality checks, safe export
src/text_themes.py          Open-ended theme rules + coding
src/insights.py             "What the data says": grouped takeaways with n, thin flags and suggested actions
scripts/                    verify_pipeline, crosscheck, validate_themes, make_fake_data, build_deliverables
tests/                      Automated tests (fake data only)
docs/                       METHODS.md, memo.md, ai_appendix.md, AI_LOG.md, deck_outline.md, SUBMISSION_CHECKLIST.md
TODO/                       Team task files per project stage (start with 00_START_HERE.md)
data/                       Put the survey export here (gitignored)
outputs/                    Generated tables (gitignored)
```

## For contributors

Read [CONTRIBUTING.md](CONTRIBUTING.md) (branch per task, PRs into `main`, no data or names in
commits) and turn on the data-leak guard once per clone: `git config core.hooksPath .githooks`.
AI assistants must follow [AGENTS.md](AGENTS.md). Team task files are in
[TODO/00_START_HERE.md](TODO/00_START_HERE.md).
