# AI Usage Log

A running record for the AI appendix. Add an entry every time AI meaningfully
shaped code, analysis or writing. **Never paste survey rows or open-text
answers into an AI tool**, and never record them here.

**Fields:** date · tool/model · what we asked (summarized prompt) · what it produced ·
errors or problems · what we verified manually and how · kept / changed / discarded.

---

### 2026-11-07 · Claude Code (Claude Opus) · Project skeleton
- **Prompt (summary):** Set up a repo skeleton for the 988 survey analysis: cleaning
  script, pre/post and group analysis with n<10 suppression, keyword theme coding,
  Streamlit dashboard, docs and privacy rules. The AI was told not to read the data file.
- **Produced:** `src/clean.py`, `src/analyze.py`, `src/text_themes.py`, `app.py`,
  `scripts/make_fake_data.py`, docs, `.gitignore`.
- **Errors found during the AI's own testing on FAKE data:** (1) Excel date cells were
  coerced to numbers, so every date was unparseable; the parser was rewritten.
  (2) p-values were rounded to 0; now left unrounded. (3) A pandas 3 `.str` error
  on the role list was fixed.
- **Not yet verified (TODO for the team on the real file):**
  - [ ] Column detection in `outputs/cleaning_report.md` matches the real headers
  - [ ] Each "before" item is paired with the correct "after" item
  - [ ] Every Likert / likelihood label maps to a number (no "unmatched values" lines)
  - [ ] Spot-check 10 raw rows against cleaned values by hand (locally only)
  - [ ] Theme keywords tested against a hand-coded sample of ~50 responses per question
  - [ ] Totals (n) in the dashboard match a manual Excel count
- **Decision:** kept as a starting point.

---

### YYYY-MM-DD · Tool · Short title
- **Prompt (summary):**
- **Produced:**
- **Errors / hallucinations:**
- **Verified manually (how):**
- **Decision:**

---

### 2026-11-07 · Claude Code (Claude Opus) · Verify pipeline against the real file (no analysis)
- **Prompt (summary):** Data file is now in `data/`. Don't run the analysis yet; verify the
  coded methods work on it. Create TODO .md files for every project stage.
- **How privacy was kept:** wrote `scripts/verify_pipeline.py`, which runs all steps in
  memory and prints only PASS/WARN/FAIL, column headers and counts. Unknown answer labels
  were identified by testing candidate labels in code (yes/no), never by printing values.
  No results were computed for display; nothing was written to `outputs/`.
- **Errors found (first verification: 6 FAIL):**
  1. "Start time"/"Completion time" were detected as the open-text questions. Fixed by
     ignoring platform metadata columns and rejecting date-like text.
  2. Role column header "Are you a....?" was not recognized. Keyword added.
  3. Retro items start with "Now think back to before…", which wasn't a retro phrase, so 0
     retro items were found. Phrase added; pairing now compares the matrix sub-item text.
  4. The 988 question is a **0–10 numeric scale** answered by 293/1,299, not a label scale.
     Added 0–10 support, a configurable "likely" cutoff (≥7), and per-metric n suppression.
  5. Language values contained invisible left-to-right marks (`‎`). Now stripped.
  6. Three training-aspect items contain non-standard labels "Very agree" and
     "Satisfied" (~2% of answers). Left as missing pending a team decision.
- **After fixes:** 33 PASS, 5 WARN, 0 FAIL. Dashboard renders with 0 exceptions.
- **Still to verify by a human:** see `TODO/02_cleaning_and_validation.md`.

---

### 2026-11-07 · Claude Code (Claude Opus) · Structure clean-up for the team
- **Prompt (summary):** Make the project structure clear for humans and AI assistants.
- **Changes:** clean column names now say what they are (`outcome_NN`/`before_NN`/`aspect_NN`,
  `text_valuable`/`text_improve`) instead of `likert_NN`/`retro_NN`/`text_1`; team decisions
  grouped at the top of `src/config.py`; per-question theme sets (`THEMES_BY_COLUMN`);
  `AGENTS.md`/`CLAUDE.md` rules for AI coding tools; `.githooks/pre-commit` blocks data
  files and notebook outputs; `docs/` = deliverable drafts and `TODO/` = instructions, with
  no duplicated plans.
- **Verified:** `verify_pipeline.py` on the real file: 0 FAIL, dashboard renders.
  The hook was tested by staging a dummy .csv; it was blocked.
- **Note:** `text_improve` uncoded rose to ~80% once it stopped using the broad "988"
  pattern from the shared theme list. That's the more honest number; stage 04 fixes coverage.
