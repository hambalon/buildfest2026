# Stage 09: Demo Video → `Team#_Demo.mp4` (2:00 max)

**Starting point (2026-11-07):** not started. **Depends on:** 05 (dashboard final).
**Read first:** [00_START_HERE.md](00_START_HERE.md)

## Goal
A ≤ 2-minute screen recording showing that the technical artifact works and is useful:
it loads the survey, cleans it transparently, shows the key findings, and handles new
data with no code changes.

## Script (target 1:50; timings are maximums)
| Time | Show | Say (roughly) |
|---|---|---|
| 0:00–0:10 | Dashboard Overview | What the tool is and who it's for (EveryMind staff) |
| 0:10–0:30 | Data quality tab | "It reads whatever export is in the data folder and cleans it automatically: invisible characters, mixed scales, multi-select roles. Here's how it interpreted each column." |
| 0:30–0:55 | Before vs. after tab | The headline finding with n |
| 0:55–1:20 | By group: county → role; one sidebar filter | Differences; groups under 10 are hidden automatically for anonymity |
| 1:20–1:40 | Open-text themes | Top valued / top improvement themes |
| 1:40–1:55 | Terminal: `python scripts/verify_pipeline.py` (or swapping a file into `data/`) | "A new export just works; the verification script confirms it." |
| 1:55–2:00 | Overview | One-line close |

## Tasks
- [ ] Final dashboard on the real data, or on fake data if the rules discourage
      showing real results. Don't show raw rows or text answers in any case.
- [ ] Clean the screen: close other tabs and apps, hide bookmarks bar, use a neutral
      desktop, turn off notifications. **No names** in the browser profile, terminal prompt
      (`PS1` often shows your username, so use `export PS1='$ '`), file paths or voice intro.
- [ ] Record (macOS: Cmd+Shift+5 → Record selected portion; or OBS). 1080p.
- [ ] Narration: script it, practice once, keep it under 2:00. Voice is fine; don't say names.
- [ ] Trim and export as **MP4 (H.264)**. Check the duration in the file's info: **≤ 2:00**.
- [ ] Name it `Team#_Demo.mp4`. Upload and set the link to **"Anyone with the link can view"**.

## Acceptance criteria
- Duration ≤ 2:00. Plays in a browser from the share link while logged out.
- No names, emails, usernames, raw rows or quotes visible or audible.
