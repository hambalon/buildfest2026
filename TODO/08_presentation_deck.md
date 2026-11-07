# Stage 08: Presentation → `Team#_Presentation.pptx`

**Depends on:** 03, 04, 06 (memo findings final). **Read first:** [00_START_HERE.md](00_START_HERE.md)

## Goal
A clear slide deck telling the same story as the memo: question → data → findings →
recommendations → how we built it.

**Content lives in [../docs/deck_outline.md](../docs/deck_outline.md)**: the slide-by-slide
plan, titles and speaker notes. This file only says how to build and check the deck.

## Before building
- [ ] Check the official rules: slide limit, presentation length, template, and
      whether it's presented live or judged as a file. Adjust the outline to fit.
- [ ] Memo numbers are final (stage 06).

## Tasks
- [ ] Write each slide's title in `docs/deck_outline.md` as the message, a full sentence
      (e.g., "Confidence in knowing when to use 988 roughly doubled"). Max 3 bullets per slide.
- [ ] Build the slides in PowerPoint or Google Slides (export to .pptx).
- [ ] Charts: export from the dashboard (chart "⋯" menu → Save as PNG) or rebuild in
      PowerPoint from `outputs/*.csv`.
- [ ] Speaker notes for each slide (if presented).
- [ ] Remove personal info: File → Info → Inspect Presentation → remove document
      properties and personal information. Check slide masters and footers for names.
- [ ] Save as `Team#_Presentation.pptx`.

## Chart rules
- One message per slide. Put n on every chart. No 3D, no dual axes, no pie charts with
  more than 3 slices.
- Same colors as the dashboard: **before = orange `#eb6834`, after = blue `#2a78d6`**.

## Acceptance criteria
- Numbers match the memo exactly. No group with n<10, no identifying quotes.
- File metadata has no names.

## AI prompt template
> Using 00_START_HERE.md, 08_presentation_deck.md and docs/deck_outline.md, plus the
> final memo text `<paste>`, fill in the slide titles, max 3 bullets per slide and
> speaker notes. Use only numbers from the memo.
