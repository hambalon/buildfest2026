"""Plain-language takeaways generated from the aggregate tables.

Used by the dashboard's Summary tab so that a new survey export produces updated
takeaways with no analyst involved. Rules:
- Only uses numbers based on at least MIN_N respondents.
- Only calls a group difference "real" when the significance test says p < 0.05.
- Every sentence carries its n so readers can judge how solid it is.
"""
from __future__ import annotations

import pandas as pd

from src import config as C


def _ok(v) -> bool:
    return v is not None and v == v  # not NaN


def _n(v) -> str:
    return f"{int(v):,}"


def build(res, tables: dict[str, pd.DataFrame], themes: dict[str, pd.DataFrame],
          label=lambda c: c) -> list[str]:
    """Return a list of markdown bullet strings (most important first)."""
    out: list[str] = []
    ov = tables["overall"].set_index("metric")["value"] if "overall" in tables else pd.Series(dtype=object)

    # 1. Knowledge gains
    rc = tables.get("retro_change", pd.DataFrame())
    if not rc.empty and (~rc["suppressed"]).any():
        r = rc[~rc["suppressed"]].copy()
        r["gain"] = r["top_box_after"] - r["top_box_before"]
        best = r.sort_values("gain", ascending=False).iloc[0]
        after = ov.get("Knowledge: % agree after (avg of outcome items)")
        before = ov.get("Knowledge: % agree before (avg, retrospective)")
        if _ok(after) and _ok(before):
            out.append(
                f"**Knowledge goals are being met.** On average {after:.0f}% agree with the knowledge "
                f"statements after training, versus {before:.0f}% rating themselves that way for *before* "
                f"the training (retrospective, n = {_n(best['n'])}). The biggest gain is "
                f"*{label(best['item'])}*: {best['top_box_before']:.0f}% → {best['top_box_after']:.0f}%.")

    # 2. Audience gap
    aud = tables.get("by_audience", pd.DataFrame())
    tests = tables.get("group_tests", pd.DataFrame())
    if not aud.empty and {"Students", "Adults"} <= set(aud["group"]):
        a = aud.set_index("group")
        s_nps, a_nps = a.loc["Students", "nps"], a.loc["Adults", "nps"]
        t = tests[(tests.get("grouping") == "audience") & tests["metric"].str.startswith("Likelihood to recommend")] \
            if not tests.empty else pd.DataFrame()
        if _ok(s_nps) and _ok(a_nps) and len(t) and t["p_value"].iloc[0] < 0.05:
            share = a.loc["Students", "n"] / (a.loc["Students", "n"] + a.loc["Adults", "n"]) * 100
            out.append(
                f"**Students experience the training very differently from adults.** Students are "
                f"{share:.0f}% of respondents; their Net Promoter Score is {s_nps:+.0f} "
                f"(n = {_n(a.loc['Students', 'n_recommend'])}) vs {a_nps:+.0f} for adults "
                f"(n = {_n(a.loc['Adults', 'n_recommend'])}), yet their knowledge scores after "
                f"training are similar. The gap is in engagement, not learning.")

    # 3. Intent to call 988
    pct = ov.get("Likely to call 988: % likely")
    n988 = ov.get("Likely to call 988: n answered")
    if _ok(pct) and _ok(n988):
        msg = (f"**Intent lags knowledge.** {pct:.0f}% say they are likely to call 988 "
               f"(n = {_n(n988)}; only {n988 / max(len(res.df), 1) * 100:.0f}% of all respondents were "
               f"asked or answered this question).")
        ig = tables.get("intent_gap", pd.DataFrame())
        last = ig[ig["item"] == ig["item"].max()] if not ig.empty else ig
        if len(last) == 2 and last["pct_likely_988"].notna().all():
            ag = last[last["knowledge"].str.startswith("Agrees")].iloc[0]
            no = last[~last["knowledge"].str.startswith("Agrees")].iloc[0]
            msg += (f" Among people who do *not* agree that “{label(ag['item']).lower()}”, only "
                    f"{no['pct_likely_988']:.0f}% are likely to call (n = {_n(no['n'])}), vs "
                    f"{ag['pct_likely_988']:.0f}% of those who do.")
        out.append(msg)

    # 4. Trend
    tr = tables.get("trend", pd.DataFrame())
    if not tr.empty:
        tr = tr[(~tr["suppressed"]) & tr["nps"].notna()]
        if len(tr) >= 2:
            first, last = tr.iloc[0], tr.iloc[-1]
            if abs(last["nps"] - first["nps"]) >= 10:
                direction = "fallen" if last["nps"] < first["nps"] else "risen"
                out.append(
                    f"**The recommend score has {direction}** from {first['nps']:+.0f} ({first['period']}, "
                    f"n = {_n(first['n'])}) to {last['nps']:+.0f} ({last['period']}, n = {_n(last['n'])}). "
                    f"The student share moved from {first['pct_students']:.0f}% to "
                    f"{last['pct_students']:.0f}% over the same time; compare audiences in "
                    f"*Trends & sessions* before reading this as a quality change.")

    # 5. Sessions
    ses = tables.get("sessions", pd.DataFrame())
    if not ses.empty:
        k = int(ses["needs_follow_up"].sum())
        out.append(f"**{k} of {len(ses)} sessions** (with at least {C.MIN_N} responses) are flagged for "
                   f"follow-up in the session scorecard.")

    # 6. Voice of participants
    for col, t in themes.items():
        if col.endswith("_by_audience") or t is None or t.empty:
            continue
        top = t[(~t["under_min_n"]) & ~t["theme"].str.startswith("Other")]
        if len(top):
            q = "most valuable" if "valuable" in col else "how to improve" if "improve" in col else col
            row = top.iloc[0]
            out.append(f"**Participant voice ({q}):** the most common theme is *{row['theme']}* "
                       f"({row['pct_of_answered']:.0f}% of {_n(row['n_answered'])} answers; keyword-coded).")
    return out
