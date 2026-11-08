"""Shared settings for the BuildFest 2026 survey pipeline.

Section 1 (TEAM DECISIONS) holds the analytic choices the team owns. Change them
here, never inside the scripts, and log every change in docs/AI_LOG.md and the
memo's methods section.
Section 2 tells the cleaner how to read the survey file. Change it only when the
survey layout changes; rerun `python scripts/verify_pipeline.py` afterward.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"

# =========================================================================== #
# 1. TEAM DECISIONS
# =========================================================================== #

# Small-group rule: any group or metric answered by fewer than MIN_N people is
# hidden ("n<10") everywhere: tables, dashboard, memo, slides.
MIN_N = 10

# "% agree" = share answering at or above this on the 1-5 scale (4 = Agree).
TOP_BOX_MIN = 4

# 988 likelihood is a 0-10 question in the current file.
# "% likely to call 988" = share scoring at least this. Alternative: 9 (NPS-style).
CALL_988_LIKELY_MIN_0_10 = 7

# The three "aspects of the training" items contain two non-standard labels
# ("Very agree", "Satisfied"; ~25 answers total, probably from an older form
# version). Empty dict = treat them as MISSING (current decision).
# To count them instead, use: {"very agree": 5, "satisfied": 4}
NONSTANDARD_AGREE_LABELS: dict[str, int] = {}

# =========================================================================== #
# 2. HOW TO READ THE FILE (change only if the survey layout changes)
# =========================================================================== #

# Values treated as missing after whitespace normalization (compared lowercase).
MISSING_TOKENS = {
    "", "none", "n/a", "na", "nan", "null", "-", "--", ".", "no response",
    "no answer", "not applicable", "prefer not to say", "prefer not to answer",
}

# --- Ordinal scales (all mapped to 1-5, higher = more positive) -------------
# Keys are lowercase, whitespace-normalized. Spanish included (language column).
AGREE_SCALE = {
    "strongly disagree": 1, "totalmente en desacuerdo": 1, "muy en desacuerdo": 1,
    "disagree": 2, "somewhat disagree": 2, "en desacuerdo": 2,
    "neither agree nor disagree": 3, "neither agree or disagree": 3, "neutral": 3,
    "neither": 3, "ni de acuerdo ni en desacuerdo": 3, "unsure": 3, "not sure": 3,
    "agree": 4, "somewhat agree": 4, "de acuerdo": 4,
    "strongly agree": 5, "totalmente de acuerdo": 5, "muy de acuerdo": 5,
    **NONSTANDARD_AGREE_LABELS,
}

LIKELY_SCALE = {
    "very unlikely": 1, "extremely unlikely": 1, "not at all likely": 1, "muy improbable": 1,
    "unlikely": 2, "somewhat unlikely": 2, "improbable": 2, "poco probable": 2,
    "neither likely nor unlikely": 3, "neutral": 3, "unsure": 3, "not sure": 3,
    "maybe": 3, "no estoy seguro": 3, "no estoy segura": 3,
    "likely": 4, "somewhat likely": 4, "probable": 4,
    "very likely": 5, "extremely likely": 5, "muy probable": 5,
    # In case the 988 question is Yes / Maybe / No in a future export
    "no": 1, "yes": 5, "sí": 5, "si": 5, "tal vez": 3, "quizás": 3,
}

SCALES = {"agree": AGREE_SCALE, "likely": LIKELY_SCALE}

# A column counts as an ordinal scale if at least this share of its answers match.
SCALE_MATCH_THRESHOLD = 0.8

# --- Column detection --------------------------------------------------------
# Canonical name -> lowercase substrings to look for in the header (first match wins).
# Agree/disagree items are detected by their values, not their headers.
HEADER_KEYWORDS = {
    "language": ["language", "idioma"],
    "role": ["role", "participant type", "are you a", "i am a", "which best describes"],
    "training_date": ["date"],
    "county": ["county", "condado"],
    "recommend": ["recommend"],
    "call_988": ["call 988", "contact 988", "use 988 if"],
}

# Phrases marking a retrospective ("before the training") item.
RETRO_KEYWORDS = ["think back to before", "before the training", "before this training",
                  "prior to the training", "before training", "antes de la capacitación",
                  "antes del entrenamiento"]

# Survey-platform metadata columns (exact header, lowercase) that are never analyzed.
IGNORE_HEADERS = {"id", "start time", "completion time", "email", "name", "last modified time"}

# Open-text questions: header phrases -> clean column name.
# Columns that look like free text but match neither get text_1 / text_2.
TEXT_COLUMNS = {
    "text_valuable": ["most valuable", "most helpful", "learned", "most useful"],
    "text_improve": ["improve", "suggest", "change about", "do better"],
}
TEXT_KEYWORDS = [k for ks in TEXT_COLUMNS.values() for k in ks] + ["comments", "anything else"]

# Free-text fallback: string columns whose average answer is at least this long.
TEXT_MIN_AVG_LEN = 15

# --- Manual fixes if auto-detection guesses wrong ------------------------------
# Pin a raw header (as printed by verify_pipeline.py) to a role, e.g.
# {"What county do you live in?": "county", "Any other comments?": "ignore"}
# Valid roles: language, role, training_date, county, recommend, call_988,
#              likert (agree item), retro (before item), text_1, text_2, ignore
COLUMN_OVERRIDES: dict[str, str] = {}

# Pin a "before" item to its "after" item by RAW headers: {"<before header>": "<after header>"}
RETRO_PAIR_OVERRIDES: dict[str, str] = {}

# Minimum sub-item text similarity (0-1) to auto-pair a before item with an after item.
RETRO_PAIR_MIN_SIMILARITY = 0.45

# =========================================================================== #
# 3. DASHBOARD DISPLAY (labels only, no effect on any number)
# =========================================================================== #

# Short chart labels by clean column name. Columns not listed fall back to the
# question text from the survey header (res.label()).
SHORT_LABELS: dict[str, str] = {
    "outcome_01": "Can identify mental health crises",
    "outcome_02": "Can describe 988",
    "outcome_03": "Know when to use 988",
    "aspect_01": "Presenter engaged participants",
    "aspect_02": "Presenter knew the subject",
    "aspect_03": "Training well organized",
}
