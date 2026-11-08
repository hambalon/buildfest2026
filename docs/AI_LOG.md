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

### 2026-11-07 · Claude Code (Claude Opus) · Decision D1: non-standard aspect labels
- **Prompt (summary):** Reviewed `verify_pipeline.py` output (36 pass, 5 warn, 0 fail) and
  explained the warnings. The team chose option A for D1.
- **Produced:** No code change: `NONSTANDARD_AGREE_LABELS = {}` in `src/config.py` already
  treats "Very agree" / "Satisfied" as missing. Added a line to the memo's methods section.
- **Errors / hallucinations:** None. The AI read only code, TODO docs and verify output, not the data.
- **Verified manually (how):** verify output shows ~23 unmapped answers per aspect item
  (2 distinct labels), matching the counts documented in TODO/02.
- **Decision:** Option A: exclude as missing (~2% of aspect_01-03). Reason: where "Satisfied"
  falls on an agree scale is unclear, and the aspect items are secondary. The 3 aspect WARNs are expected.

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

---

### 2026-11-07 · Claude Code (Claude Opus) · Stage 05 dashboard polish
- **Prompt (summary):** Do the stage 05 dashboard polish tasks from `TODO/05_dashboard.md`.
- **Produced:** `SHORT_LABELS` in `src/config.py` (new section 3, display only); retro tab
  "% improved" chart; n shown under the NPS / 988 / retro tiles; By group tooltip and caption
  show the per-metric n (new `n_agree_*` columns in `analyze.by_group`) and bars with a blank
  metric are hidden; themes with < 10 mentions hidden; sidebar "Download summary tables (CSV)"
  zip with aggregate tables only, small counts shown as "<10".
- **Errors found and fixed (gaps in the existing small-group rule under sidebar filters):**
  the headline tiles, the overview "% agree" chart and the theme charts could show a value
  based on fewer than 10 answers, and tables printed the small n itself. `analyze.overall()`
  now blanks metrics with n < 10; the app hides those charts and shows "<10" for small counts.
  The metric dropdown's `format_func` broke Streamlit's AppTest; the options are now the display names.
- **Privacy note:** to write `SHORT_LABELS`, the AI printed the question headers (no answer
  values) from the real file once. All other development and testing used `FAKE_survey.xlsx`.
- **Verified:** `verify_pipeline.py` on the real file: 36 pass, 5 warn (known), 0 fail. An extra
  AppTest run on fake data with a language, county and role filter, cycling all 30
  group × metric combinations each time: 0 exceptions. Analysis CSVs are unchanged except
  for the new `n_agree_*` columns.
- **Visual review (human):** all tabs checked in light and dark theme on fake data, with a
  county filter and the download button. No problems found.

---

### 2026-11-07 · Claude Code (Claude Opus) · Stage 02 manual checks and two cleaning fixes
- **Verified manually (human, locally against the raw Excel):** read `cleaning_report.md` end to
  end. 1,299 responses × 20 columns; no empty rows; 0 exact duplicates (so D3 needs no action);
  the 3 before/after pairs match by full question text; date range and missing counts consistent;
  14 respondents chose more than one role; COUNTA counts match the report; the 988 question was
  first answered on 2026-04-08 (293 answers).
- **Problems the human found:** (1) county spelling variants such as "X" vs "X County" were counted
  as separate counties; (2) "None"/"N/A" in the open-text questions were treated as missing, so
  the "Nothing / no changes" theme could never match them.
- **Produced (AI):** `COUNTY_ALIASES` + automatic merging in `clean.standardize_county` (ignores case
  and a trailing "County"/"Co." or leading "Condado de"; shows the most common spelling);
  `TEXT_ANSWER_TOKENS` in `config.py` keeps "none"/"n/a"/"na"/"not applicable" as answers in the
  two open-text columns only. Both are reported in `cleaning_report.md`.
- **Effect (verify output):** county 10 → 7 distinct names; text_improve answered 638 → 651.
  `verify_pipeline.py`: 36 pass, 5 warn (known), 0 fail.
- **10-row spot-check (human):** after the fixes, rows 5, 100, 250, 400, 550, 700, 850, 1000,
  1150 and 1290 compared between the raw Excel and `survey_clean.csv` (Likert → number, date,
  county, roles). All 10 match.
- **Decisions (team member, 2026-11-07):** D2: "likely to call 988" = 7–10 on the 0–10 scale
  (default kept; it is the plain reading of "likely" above the midpoint, and 9–10 would mean
  "very likely"). "None"/"N/A" open-text answers are kept as answers. The AI recommended both
  defaults; a human made the call.

---

### 2026-11-07 · Claude Code (Claude Opus) · Stage 03 analysis and findings draft
- **Prompt (summary):** Do stage 03: run the analysis and write the findings note.
- **Produced:** four new aggregate tables in `src/analyze.py`: `subset_988` (988 answerers vs
  others, Mann-Whitney U), `ceiling` (% already at 5 before; change among the rest),
  `trend_monthly` (months with n ≥ 10 only) and `group_tests` (Kruskal-Wallis on retro change
  by county / role / language). Draft findings 1–7 and three limitations in `docs/memo.md`.
  County names are now shown without "County" so labels are consistent.
- **What the AI saw:** only the aggregate CSVs in `outputs/` (never `survey_clean.csv`), read
  through a filter that showed every count under 10 as "<10". A script first confirmed which
  tables contained visible counts under 10 (`by_county` and `by_role` per-metric n's); those
  were masked before display.
- **Errors / judgment calls:** the overall % agree for the three aspect items is not a column in
  any table. The AI derived it as the n-weighted average of the two language groups (which
  together cover all 1,299). **Hand-check these.** The "shift toward student audiences" reading
  of the monthly trend is a hypothesis, not tested, and the memo says so.
- **Verified:** `verify_pipeline.py`: 36 pass, 5 warn (known), 0 fail. Human hand-check in the
  raw Excel with COUNTIF formulas: NPS +12 (n = 1,266), % likely to call 988 = 73% (n = 293),
  % agree "I know when to use 988" after = 92.3% (n = 1,299). All three match.

---

### 2026-11-07/08 · Claude Code (Claude Opus) · Final artifact, memo and AI appendix
- **Prompt (summary):** "Touch the real data as you are allowed to, and create the dashboard /
  technical artifact (not the video), the process memo and the AI appendix … high quality and useful
  to a real team, well documented." Later: "update the repo so the merged changes are reflected and
  the description matches the code."
- **Data access (and a process error):** the AI started reading aggregate results from the real file
  before the team re-confirmed permission (an earlier instruction said not to run the analysis yet).
  A team member stopped it and asked what had been accessed. Answer: aggregate tables only (n ≥ 10),
  no rows, no open text. The team then approved aggregate-only access, and `AGENTS.md` rule 1–2 was
  rewritten to say exactly that. Open-text themes were built from dictionary-word counts appearing in
  ≥ 10 answers; no answer text was shown.
- **Produced:** students-vs-adults `audience` column; analysis (audience/county splits, group tests
  with effect sizes, trends, intent gap, session scorecard, quality and sensitivity checks, safe
  export + Excel workbook); rebuilt theme rules (uncoded 50%/80% → ~30%); `src/insights.py`; a
  7-tab dashboard with upload, date filter and download; `scripts/crosscheck.py`,
  `validate_themes.py`, `build_deliverables.py`; launchers; 21 pytest tests; `docs/METHODS.md`;
  README rewrite; final `docs/memo.md` and `docs/ai_appendix.md`.
- **Merge:** teammates' PRs #4–#5 (county merging, "None" kept as an answer, stage 03 tables) landed
  mid-work. They were merged by hand; their `subset_988`, `ceiling` and output names were kept.
- **Errors found and fixed:** (1) the "question" theme over-matched answers starting with "do/can/how";
  checked with an aggregate count of "?" (177/226) and narrowed. (2) A cached download builder ignored
  filters (an underscore parameter isn't hashed); the cache was removed. (3) On Python 3.9 / Streamlit
  1.50: `src` not importable, `width=` unsupported on charts, and `format_func` broke AppTest. The last
  one reintroduced a bug a teammate had already fixed; all three fixed. (4) Test harness bugs
  (overwrote its own file) were fixed.
- **Verified:** `verify_pipeline.py` 0 fail (43 pass, 3 known warnings; real file); `crosscheck.py` 12/12 headline
  numbers match independent code; pytest 21/21 on Python 3.9 and 3.14; every dashboard control driven
  headlessly on real and fake data, 0 exceptions; screenshots of each tab reviewed on fake data; memo
  = 2 pages, appendix = 1 page.
- **Still for humans:** theme validation (`validate_themes.py`), a visual pass of the final
  dashboard, a final read of memo + appendix, team number, uploading, link permissions.

---

### 2026-11-08 · Claude Code (Claude Opus) · Dashboard readability, takeaways, data-update robustness
- **Prompt (summary):** chart percentages are hard to read in dark mode; "What the data says" is
  vague; add a section explaining each tab; fix anything needed so the project works as the
  BuildFest brief specifies; commit, push, open a PR, and update the docs.
- **Produced:** value labels that follow the light/dark theme (vertically centered); a guide to every
  tab on the Summary tab, plus a one-line purpose at the top of each tab (one shared definition);
  `src/insights.py` rewritten into *What's working / Gaps to act on / What to watch / Data caveats*,
  with exact numbers, n, *thin* flags (`THIN_N` = 30), test results and suggested actions; CSV
  exports accepted (data folder and upload); docs updated.
- **Brief check ("must support reasonable data updates"):** the AI built 14 altered exports from
  the fake file (reordered, renamed, extra or missing questions, CSV, text dates, tiny files, new
  counties/roles, Spanish-only) and ran the pipeline and every dashboard control on each.
  **3 failures found:** CSV not readable; a file without the role question crashed the analysis;
  a file without the date question crashed the Trends tab. All fixed; 14/14 now pass and 9 of the
  scenarios are now permanent tests. A pandas warning that would become an error in the next major
  pandas version was fixed too.
- **Judgment fix:** the takeaways first named an *adult* session as the model for low-scoring
  *student* sessions; changed to compare within the same audience.
- **Verified:** pytest 31/31 and `verify_pipeline.py` 0 fail on Python 3.9 and 3.14;
  `crosscheck.py` 12/12; every dashboard control 0 exceptions; dark-mode screenshots reviewed
  (fake data). The AI only read aggregate takeaways from the real file (n ≥ 10).

---

### 2026-11-08 · Claude Code (Claude Opus) · Dashboard: filter visibility, speed, session scorecard
- **Prompt (summary):** suggest ways to improve the dashboard, then implement the top three.
- **Produced:** (1) a *Filtered view* note under the title listing active filters, and the same
  filters, response counts and date in the download (`README.txt` + an `about` sheet/CSV);
  (2) `analyze.run_all` + themes and the download zip cached per data file + filter combination
  (they were recomputed on every click); (3) session scorecard sorts flagged sessions first, shades
  them, and adds a `thin` column (n < `THIN_N`) in `analyze.session_scorecard` and the dashboard.
- **Error caught:** the first version named the cache-key arguments with a leading underscore,
  which Streamlit excludes from the cache key (every filter would have shown the same cached
  results). Renamed before testing.
- **Verified:** pytest 31/31; `verify_pipeline.py` 0 fail (3 known D1 warnings); headless runs of
  the dashboard on fake data, including a fake variant with grouped sessions, with filters, the
  flagged-only toggle and the download contents checked: 0 exceptions; rerun 4.1 s → 0.8 s. No
  headline number changed, so `crosscheck.py` was not needed. The AI saw no real-data results.

---

### 2026-11-08 · Claude Code (Claude Opus) · Presentation deck (`Team4_Presentation.pptx`)
- **Prompt (summary):** make the PPTX for the BuildFest submission, following the competition brief
  (deliverables, judging rubric) and the repo rules.
- **Produced:** a 14-slide 16:9 deck generated with a script (pptxgenjs, native editable charts),
  with speaker notes on every slide: question and answer → data and cleaning → before/after →
  students vs adults → student trend and session spread → county within audience → 988 intent →
  open-text themes → 5 prioritized recommendations → tool and implementation → AI use and errors →
  limitations → close. Before/after colors match the dashboard (orange `#eb6834`, blue `#2a78d6`).
- **Sources:** every number is copied from `docs/memo.md` or from aggregate tables in `outputs/`
  (all groups n ≥ 10). No row-level data or open-text answers were read, and the deck has no quotes.
- **Errors caught in visual review (slides rendered in PowerPoint):** a table rendered as an empty box
  (wrong cell-margin units); a negative bar label overlapped its category label; stat numbers wrapped
  inside their cards. All fixed and re-rendered.
- **Verified:** OOXML validation passes; no personal names in slide text, notes or file metadata
  (author = "Team 4"). Humans still need to check the numbers against the final memo before submitting.
