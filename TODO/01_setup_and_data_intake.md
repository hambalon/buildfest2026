# Stage 01: Setup and Data Intake

**Starting point (2026-11-07):** done on the lead machine; each teammate repeats it locally.
**Depends on:** nothing. **Read first:** [00_START_HERE.md](00_START_HERE.md)

## Goal
Every teammate can run the pipeline locally. The data file is on their machine only
and git ignores it.

## Tasks
- [ ] Install Python 3.11+ (`python3 --version`). Tested on 3.14 with pandas 3.1, Streamlit 1.67.
- [ ] Clone the repo and create the environment:
  ```bash
  git clone <repo-url> && cd buildfest2026
  python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```
- [ ] **Turn on the data-leak guard** (once per clone). It blocks commits of data files,
      anything in `data/`/`outputs/`, and notebooks with saved outputs:
  ```bash
  git config core.hooksPath .githooks
  ```
- [ ] Copy `BuildFest_EveryMind_Survey_Data_FULL.xlsx` into `data/` from the official
      source. Never via GitHub or an AI tool.
- [ ] Confirm git ignores it. Expected output is a line starting `.gitignore:` that names the file:
  ```bash
  git check-ignore -v data/BuildFest_EveryMind_Survey_Data_FULL.xlsx
  ```
- [ ] Run the structural check (stage 02 explains the output):
  ```bash
  python scripts/verify_pipeline.py
  ```
  Expected right now: **0 fail**, with 5 known warnings (listed in stage 02).
- [ ] Teammates without the data: `python scripts/make_fake_data.py`, then prefix
      commands with `DATA_FILE=outputs/FAKE_survey.xlsx`.
- [ ] Set your git identity to something anonymous before the first commit (judging
      is anonymous):
  ```bash
  git config user.name "team-member-1"
  git config user.email "<github-id>+<handle>@users.noreply.github.com"
  ```

## Acceptance criteria
- `verify_pipeline.py` shows 0 FAIL on each machine with the data.
- `git status` never lists anything under `data/` except `data/README.md`.

## Known issues
- The repo's first commit (made before the anonymity rule) has team names in
  README.md and a GitHub handle as author. Decide in stage 10 whether to share
  a fresh repo or a zip.

## AI prompt template
> Using 00_START_HERE.md and this file, help me fix this setup error. Here is the
> exact error text (it contains no survey data): `<paste>`. I'm on <OS>, Python <version>.
