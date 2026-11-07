"""Generate a FAKE survey file for testing the pipeline without the real data.

Usage (from the repo root):
    python scripts/make_fake_data.py                      # -> outputs/FAKE_survey.xlsx
    DATA_FILE=outputs/FAKE_survey.xlsx python -m src.clean
    DATA_FILE=outputs/FAKE_survey.xlsx streamlit run app.py

The layout mirrors the real Microsoft Forms export (20 columns, metadata columns,
"Stem..Sub-item" matrix headers, a sparse 0-10 988 question), but the question
wording is paraphrased and every value is random. It deliberately includes the
messy patterns seen in the real file: non-breaking spaces, invisible
left-to-right marks, trailing semicolons, "None" in free text, tiny counties,
and two non-standard labels on the training-aspect items.
"""
import random
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs" / "FAKE_survey.xlsx"
random.seed(988)

NBSP, LRM = " ", "‎"
AGREE = ["Strongly disagree", "Disagree", "Neither agree nor disagree", "Agree", "Strongly agree"]
COUNTIES = (["County A"] * 40 + ["County B"] * 30 + ["County C"] * 20 + ["County D"] * 8
            + ["County E", "County F", "County G"])
ROLES = ["Community member", "Educator", "Health professional", "Student"]

AFTER_STEM = "Tell us how much you agree with these statements.."
RETRO_STEM = "Now think back to before you took part in the training. ."
ASPECT_STEM = "How much do you agree with these aspects of the training?."
OUTCOMES = ["I can spot a mental health crisis.", "I can explain how 988 works.", "I know when to use 988."]
RETRO_ITEMS = ["I could spot a mental health crisis.", "I could explain how 988 works.", "I knew when to use 988."]
ASPECTS = ["The presenter engaged the group.", "The presenter knew the topic.", "The training was organized."]

HELPFUL = ["The role play practice", "Learning what happens when you call 988", "None",
           "The presenter was very knowledgeable", "Warning signs", "Resources and handouts",
           "Todo fue muy útil, los ejemplos", "", "Everything"]
IMPROVE = ["Nothing", "More time for questions", "None", "More examples for youth",
           "Audio was hard to hear on Zoom", "Offer it in Spanish too", "", "N/A",
           "Nothing, it was great"]

rows = []
for i in range(300):
    start = pd.Timestamp("2025-06-01 09:00") + pd.Timedelta(minutes=random.randint(0, 500000))
    after = [random.choices(range(5), weights=[1, 2, 5, 25, 30])[0] for _ in OUTCOMES]
    r = {
        "Id": i + 1,
        "Start time": start.strftime("%m/%d/%y %H:%M:%S"),
        "Completion time": (start + pd.Timedelta(minutes=4)).strftime("%m/%d/%y %H:%M:%S"),
        "Language": random.choices([f"English (United States){LRM}", f"Español (México){LRM}"],
                                   weights=[90, 10])[0],
        "Are you a....?": ";".join(random.sample(ROLES, random.choice([1] * 20 + [2])))
                          + random.choice(["", ";"]),
        "Please enter the date of your training.": start.normalize(),
        "Which county is this training affiliated with?": random.choice(COUNTIES) + random.choice(["", NBSP]),
    }
    for item, a in zip(OUTCOMES, after):
        r[AFTER_STEM + item] = AGREE[a] + random.choice(["", NBSP])
    for item, a in zip(RETRO_ITEMS, after):
        r[RETRO_STEM + item] = AGREE[max(0, a - random.choice([0, 1, 1, 2]))]
    for item in ASPECTS:  # ~12% skipped, ~2% non-standard labels
        r[ASPECT_STEM + item] = (None if random.random() < 0.12 else
                                 random.choice(["Very agree", "Satisfied"]) if random.random() < 0.02 else
                                 AGREE[random.choices(range(5), weights=[2, 1, 6, 35, 50])[0]])
    r["How likely are you to recommend the training to a friend or colleague?"] = (
        random.choices(range(11), weights=[1] * 7 + [3, 5, 10, 15])[0] if random.random() < 0.97 else None)
    # 0-10 scale, answered by only ~25% (the question was added to the form later)
    r["How likely are you to call 988 if you or someone else needs help?"] = (
        random.choices(range(11), weights=[1] * 6 + [2, 3, 5, 8, 12])[0] if random.random() < 0.25 else None)
    r["What was the most valuable thing you learned?"] = random.choice(HELPFUL)
    r["How can we improve this training in the future?"] = random.choice(IMPROVE)
    rows.append(r)

out.parent.mkdir(exist_ok=True)
pd.DataFrame(rows).to_excel(out, index=False)
print(f"Wrote {len(rows)} FAKE responses to {out}")
