# Memo (draft source for Team#_Memo.pdf)

> **Deliverable draft.** How to write and check it: [../TODO/06_memo.md](../TODO/06_memo.md).
> Build the PDF with `python scripts/build_deliverables.py --team N` (must stay ≤ 2 pages).
> Only the text below the BEGIN DELIVERABLE line is printed. No names (anonymous judging).
> Every number comes from `python -m src.analyze` on the full file (1,299 responses) and has its n.

<!-- BEGIN DELIVERABLE -->

# The 988 training teaches well, but students aren't sold on it

<div class="meta"><b>To:</b> EveryMind Community Education team &nbsp;·&nbsp; <b>From:</b> Team # &nbsp;·&nbsp; <b>Date:</b> November 8, 2026 &nbsp;·&nbsp; <b>Re:</b> 988 training feedback (1,299 surveys, Oct 2025 – Oct 2026) and a tool to keep tracking it</div>

> **Bottom line:** After the training, about 9 in 10 participants say they understand 988 and when to use it.
> But students, who are 83% of participants, rate the experience far below adults, and their ratings are
> falling. The training's next gains will come from making it work for young people and turning knowledge
> into willingness to call. Our dashboard lets staff track that every month in about 15 minutes.

<div class="fig">
<div>
<h4>% who agree, before → after the training (n = 1,299)</h4>
<div class="bar"><span>Can describe 988</span><div class="track"><div class="fill" style="width:46%;background:#eb6834"></div></div><span>46%</span></div>
<div class="bar"><span></span><div class="track"><div class="fill" style="width:90%;background:#2a78d6"></div></div><span><b>90%</b></span></div>
<div class="bar"><span>Know when to use 988</span><div class="track"><div class="fill" style="width:56%;background:#eb6834"></div></div><span>56%</span></div>
<div class="bar"><span></span><div class="track"><div class="fill" style="width:92%;background:#2a78d6"></div></div><span><b>92%</b></span></div>
<div class="bar"><span>Can identify a crisis</span><div class="track"><div class="fill" style="width:72%;background:#eb6834"></div></div><span>72%</span></div>
<div class="bar"><span></span><div class="track"><div class="fill" style="width:90%;background:#2a78d6"></div></div><span><b>90%</b></span></div>
<div class="note"><span style="color:#eb6834">■</span> before (rated looking back) &nbsp; <span style="color:#2a78d6">■</span> after</div>
</div>
<div>
<h4>Would recommend the training (0–10 scale)</h4>
<div class="bar"><span>Adults: promoters (9–10)</span><div class="track"><div class="fill" style="width:82%;background:#1baf7a"></div></div><span>82%</span></div>
<div class="bar"><span>Adults: detractors (0–6)</span><div class="track"><div class="fill" style="width:2%;background:#1baf7a"></div></div><span>2%</span></div>
<div class="bar"><span>Students: promoters (9–10)</span><div class="track"><div class="fill" style="width:33%;background:#6250d6"></div></div><span>33%</span></div>
<div class="bar"><span>Students: detractors (0–6)</span><div class="track"><div class="fill" style="width:34%;background:#6250d6"></div></div><span>34%</span></div>
<div class="note">Net Promoter Score: adults +80 (n = 215), students −2 (n = 1,051)</div>
</div>
</div>

## Key findings

1. **The training meets its knowledge goals.** Agreement after the training is 90–92% on all three
   knowledge statements (n = 1,299). The largest gains are on 988 itself: "I can describe 988 and how it
   works" rose from 46% to 90%, and "I know when to use 988" from 56% to 92%. 77% rated themselves higher
   overall. The gains are statistically clear (p < 0.001) and hold when low-effort responses are removed.
2. **Students learn as much as adults but rate the experience far lower.** Knowledge after training is
   similar (91% vs 92% agree), but students' Net Promoter Score is −2 versus +80 for adults. Students also
   rate the presenters and organization lower (89% vs 96% agree) and are less likely to say they would
   call 988 (69%, n = 253, vs 98%, n = 40). These are large, statistically significant gaps.
3. **The student experience is slipping and varies a lot by session.** Student scores fell each quarter
   in 2026: +3 (Q2, n = 398), −4 (Q3, n = 363), −9 (Q4, n = 274). Their delivery ratings dropped from 90%
   to 80% agreement. Across 18 student sessions with 10+ responses, scores ranged from −69 to +64.
   12 of 27 sessions overall meet at least one follow-up flag.
4. **County gaps are mostly about who attends.** Adults rate the training highly in every county
   (+78 to +87). Among students, Prince George's sessions score +39 (n = 169) versus −10 in Anne Arundel
   (n = 873). That makes Prince George's student sessions a useful model to learn from.
5. **Knowledge and intent go together, but intent lags.** 73% say they are likely to call 988 (7–10 on a
   0–10 scale; n = 293). Among people who don't agree they know when to use 988, only 52% are likely to
   call (n = 23), versus 75% of those who do (n = 270).
6. **What participants say.** Most valued (n = 1,063): learning that 988 exists and can be called (38%),
   that it is always available, including by text (15%), and that anyone can call for any reason (13%).
   Adults value *how* 988 works far more than students do (23% vs 7%). Asked how to improve (n = 651), 22%
   said nothing or praised it. **31% wrote a question about 988 instead** (students: 38%), which points to
   unanswered questions. Adults most often asked for more interactive content (18%).

## Recommendations (in priority order)

| # | Action | Why | Measure of success |
|---|---|---|---|
| 1 | **Redesign the student version:** shorter segments, interactive activities, peer scenarios. Learn from the highest-scoring student sessions (e.g., Prince George's). | 83% of participants; NPS −2 and falling | Student NPS ≥ +20 and delivery ≥ 90% agree within two quarters |
| 2 | **Build in a Q&A block and a take-home "What happens when you call 988" card** (who answers, confidentiality, difference from 911, texting). | 31% of improvement answers are questions; "how 988 works" reaches students least | Share of "question" answers halves; student "likely to call" ≥ 80% |
| 3 | **Review the session scorecard monthly** with facilitators. Pair low-scoring sessions with practices from high-scoring ones. | Session scores range from −69 to +64 | Share of flagged sessions below 25% (now 12 of 27) |
| 4 | **Fix the survey form:** make the 988 question required on every version, use one agree scale, add a session/facilitator field, and add a 30-day follow-up ("Did you use or share 988?"). | Only 23% answered the 988 question; behavior isn't measured | 988 question answered by ≥ 95% |
| 5 | **Grow Spanish-language and small-county reach** enough to evaluate them. | Spanish surveys n = 19; 3 counties under 10 responses | ≥ 30 Spanish responses per quarter |

## Methodology

We analyzed the Microsoft Forms export (1,299 responses, 20 questions). Our pipeline fixed formatting
problems (hidden characters, trailing semicolons, county spelling variants, inconsistent answer labels),
converted answers to numbers, and grouped participants as **students** or **adults** by their stated role.
Each participant rated three knowledge statements for *after* and, looking back, *before* the training. We
compared these pairs (Wilcoxon test) and compared groups with rank-based tests and effect sizes. Open-ended
answers were grouped into themes with transparent keyword rules, built only from word counts so no AI tool
saw individual answers. **Any group with fewer than 10 people is hidden.** We validated results in four
ways: a team member's 10-row check against the raw file, hand-calculations of three headline numbers in
Excel, an independent re-computation of 12 headline numbers (all match), and 21 automated tests.

## Implementation: how EveryMind would use the tool

- **Who:** the community education coordinator or any program staff member. No coding is needed.
- **How often:** monthly after each batch of trainings (about 15 minutes), plus a quarterly summary for
  grant reports.
- **What they need:** a computer with free Python installed (one time), and the Forms export. Double-click
  the launcher, drop in or upload the file, then review the Summary and the session scorecard and click
  **Download summary** for reports. The data never leaves the computer, small groups are hidden
  automatically, and new exports work without changes (a built-in check confirms the file was read correctly).

## Limitations

- "Before" ratings were given *after* the training (retrospective self-report). Gains reflect perceived
  learning and may be inflated by recall or politeness; there is no comparison group.
- The 988 question was added in spring 2026 and answered by only 23%. Those results describe that subset.
- 14–22% were already at the top score before the training, so they could not show a gain.
- Students dominate recent quarters, so trends mix changes in quality with changes in audience.
- Spanish-language (n = 19) and small-county results are too thin to draw conclusions.
- Theme counts come from keyword rules and are approximate (about 30% of answers are unclassified).
  A blind validation tool is included for staff to confirm them.
