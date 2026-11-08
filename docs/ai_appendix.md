# AI Appendix (draft source for Team#_AIAppendix.pdf)

> **Deliverable draft**, built from [AI_LOG.md](AI_LOG.md). Instructions: [../TODO/07_ai_appendix.md](../TODO/07_ai_appendix.md).
> Build with `python scripts/build_deliverables.py --team N` (must stay 1 page). No names.
> If teammates used other AI tools, add them to the table and to AI_LOG.md.

<!-- BEGIN DELIVERABLE -->

# AI Process Appendix · Team #

**Tools.** *Claude Code* (Anthropic Claude Opus model, in VS Code) was our main assistant: it wrote code
(cleaning, analysis, dashboard, tests), proposed analyses and drafted documentation. A palette
validator checked chart colors for color-blind readers. Every AI interaction is logged in
`docs/AI_LOG.md` (prompt, output, errors, human checks). Humans made every decision and
interpretation in the memo.

**Data rule we set before any AI use.** The AI never saw survey rows or open-ended answers. At first it saw
only column headers and pass/fail checks. Later it saw only aggregate tables in which every group has
10+ people. Open-ended themes were built from **word counts** (dictionary words appearing in 10+
answers, so no names), not from answers. When the AI began reading aggregate results before we had
re-confirmed permission, a team member stopped it, reviewed exactly what had been seen, and wrote the
rule into `AGENTS.md`, the instruction file every AI tool in our repo reads.

| Representative prompt (shortened) | How we refined the output |
|---|---|
| "Set up a project skeleton … cleaning, analysis by county, role and language with a suppress rule for groups under n = 10 … Do not read or print any survey data." | Added a git hook that blocks data files, and fake data with the real layout for all development |
| "Verify that the methods you have coded work on [the real file], but don't perform the analysis yet." | AI wrote a check that prints structure only. It revealed 6 wrong assumptions (below) |
| "Run the analysis and write the findings note." (stage 03) | Humans hand-checked numbers; AI added robustness tables (ceiling, 988 subset, sensitivity) |
| "Complete the technical artifact … high quality and useful to a real team." | Added a students-vs-adults split, session scorecard, plain-language test verdicts, launchers |

**AI errors, limitations and how we caught them**

| What went wrong | How it was caught → fixed |
|---|---|
| First pipeline **misread the real file in 6 ways**: timestamps taken as the open-ended questions, the 3 "before" items not detected, the 988 question assumed to be a label scale (it is 0–10), invisible characters in language names, an unrecognized role header, 2 stray answer labels | Our structure check showed 6 FAILs → detection rules fixed → 0 FAIL |
| Dates all unparsed; p-values rounded to 0 | AI's own test on fake data → fixed |
| County spelling variants counted as separate counties; "None" answers dropped instead of read as "nothing to change" | **Team member** reading the cleaning report → merged; kept as answers |
| First theme rules left 50–80% of answers uncoded; a "question" rule over-matched (it counted "Do more…" as a question) | Coverage stats + count of answers containing "?" (177 of 226) → rules rewritten; ~30% uncoded |
| The first findings draft compared counties directly and could only guess that the share of students explained the gap | We tested it (county × audience table): adults score high everywhere → memo compares counties within audience |
| Dashboard crashed on Python 3.9 / older Streamlit | Tested every control on two Python versions → compatibility fixes |

**What humans verified or did themselves.** (1) Read the full cleaning report and checked 10 rows of the
raw Excel against the cleaned data: all match. (2) Recomputed three headline numbers with Excel COUNTIF
(NPS +12, 73% likely to call 988, 92.3% "know when to use 988"): all match. (3) Made the analytic
decisions: non-standard labels count as missing (D1), "likely" = 7–10 (D2), "None" kept as an answer.
(4) Reviewed every dashboard tab in light and dark mode. (5) Chose the findings and recommendations.

**How final findings were validated against the data.** An independent script recomputes 12 headline
numbers straight from the raw Excel with separate, simple code: **12/12 match** the dashboard. The
structure check passes on the real file (0 failures), 21 automated tests pass, and every
before/after result holds when low-effort "same answer to everything" responses are removed.
**Limits:** theme counts are approximate keyword matches. Retrospective self-ratings measure perceived,
not tested, learning.
