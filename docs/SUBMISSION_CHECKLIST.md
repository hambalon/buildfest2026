# Submission Checklist

**Due: Sunday, November 8, 2026, 9:00 AM ET.** The single source for the deliverables list.
Technical-artifact steps: [../TODO/10_submission.md](../TODO/10_submission.md).

**Build everything:** `python scripts/build_deliverables.py --team N --forbid "Name One,Name Two"`
→ `submission/TeamN_Memo.pdf`, `TeamN_AIAppendix.pdf`, `TeamN_TechnicalArtifact.zip`, with page-limit,
placeholder, name/e-mail and no-data checks. The deck and the demo video are made by hand.

Replace `#` with our team number. Before uploading, check that no file name,
slide, document property or video frame contains a personal name (judging is anonymous).

| # | Deliverable | File name | Source | Done |
|---|---|---|---|---|
| 1 | Memo | `Team#_Memo.pdf` | `docs/memo.md` | [ ] |
| 2 | AI appendix | `Team#_AIAppendix.pdf` | `docs/ai_appendix.md` + `docs/AI_LOG.md` | [ ] |
| 3 | Presentation | `Team#_Presentation.pptx` | `docs/deck_outline.md` | [ ] |
| 4 | Demo video (**2 min max**) | `Team#_Demo.mp4` | screen recording of `streamlit run app.py` | [ ] |
| 5 | Technical artifact | `Team#_TechnicalArtifact` | this repo / dashboard | [ ] |

## Sharing links
- [ ] Every shared link is set to **"Anyone with the link can view"**
- [ ] Each link tested in a private/incognito window while logged out
- [ ] If the repo is the technical artifact: it contains **no data** (`git log --stat` shows no .xlsx/.csv)

## Anonymity
- [ ] No names in documents, slides, speaker notes or file metadata
      (Word/PowerPoint: *File → Info → Inspect Document / Remove personal info*)
- [ ] No names, emails or faces in the demo video; desktop, browser tabs and bookmarks hidden
- [ ] Git commit authors and README contain no real names (or the repo is shared as a zip)

## Content
- [ ] Every reported number has its n; no group with n < 10 shown
- [ ] No open-text quote that could identify a respondent
- [ ] Demo video ≤ 2:00 (check the actual file length)
- [ ] AI appendix reflects AI_LOG.md, including errors and what we verified
- [ ] Final run on the latest data file; dashboard and memo numbers match
