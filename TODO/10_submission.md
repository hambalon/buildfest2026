# Stage 10: Technical Artifact and Final Submission

**Depends on:** all stages. **Deadline: Sunday, November 8, 2026, 9:00 AM ET.** Aim to
finish by 8:00 AM. **Read first:** [00_START_HERE.md](00_START_HERE.md)

**The deliverables list and the final checklist live in
[../docs/SUBMISSION_CHECKLIST.md](../docs/SUBMISSION_CHECKLIST.md).** This file covers
the technical artifact and how to work through that checklist.

## Technical artifact: decide the format
- [ ] Check the official rules for what form it takes (repo link, zip, deployed app).
- [ ] **Anonymity problem:** the repo's history contains team names (first README
      commit) and a GitHub handle as commit author. Options:
  - **A (recommended): fresh, anonymous copy.** Create a new repo under an anonymous
    account or org, copy the current files (not `.git`), make one commit with an
    anonymous author, set it public or "anyone with the link". Commands:
    ```bash
    mkdir ../artifact && rsync -a --exclude .git --exclude data --exclude outputs --exclude .venv ./ ../artifact/
    cd ../artifact && mkdir -p data outputs && cp ../buildfest2026/data/README.md data/ && touch outputs/.gitkeep
    git init && git add . && git -c user.name="Team" -c user.email="team@example.com" commit -m "BuildFest 2026 technical artifact"
    ```
  - **B: zip.** `Team#_TechnicalArtifact.zip` of the same files, shared as a view-only link.
- [ ] Whichever you choose, verify **no data**: `git ls-files | grep -Ei '\.(xlsx|csv)$'`
      returns nothing, and `outputs/` and `data/` hold only placeholders.
- [ ] Verify **no names**: `grep -riE "<each teammate's first/last name>" .` returns nothing
      (run locally; don't commit the names you search for).
- [ ] README run instructions work from a fresh clone (another teammate tests with fake data).

## Final pass
- [ ] Run `python -m src.analyze` once more on the final data. Numbers must be identical
      across memo, deck, video and dashboard.
- [ ] Work through **every box** in `docs/SUBMISSION_CHECKLIST.md` (file names, links set to
      "Anyone with the link can view" and tested logged out, anonymity, content, video length).
- [ ] Submit, then screenshot the confirmation (keep it privately).

## AI prompt template
> Using 00_START_HERE.md and 10_submission.md, walk me through creating the anonymous
> artifact copy (option A) on <OS>. I'll paste back command output, which contains no data.
