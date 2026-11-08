"""Specific, actionable takeaways generated from the aggregate tables.

Used by the dashboard's Summary tab ("What the data says"), so a new survey export
produces updated takeaways with no analyst involved. Rules:
- Only numbers based on at least MIN_N respondents are used (smaller groups never appear).
- Numbers based on fewer than THIN_N respondents are marked "thin" (indicative only).
- A group difference is only called real when its significance test says p < 0.05.
- Every statement carries its n; most carry a suggested action.
Each takeaway is an Insight(kind, title, detail, action). kind is one of
"working", "gap", "watch" or "caveat" and decides which heading it appears under.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src import config as C

KINDS = {
    "working": "What's working",
    "gap": "Gaps to act on",
    "watch": "What to watch",
    "caveat": "Data caveats",
}


@dataclass
class Insight:
    kind: str
    title: str
    detail: str
    action: str = ""


def _ok(v) -> bool:
    return v is not None and not (isinstance(v, float) and v != v) and v is not pd.NA


def n_(v) -> str:
    """'n = 1,234', with a thin marker under THIN_N."""
    v = int(v)
    return f"n = {v:,}" + (" — *thin*" if v < C.THIN_N else "")


def pct(v) -> str:
    return f"{v:.0f}%"


def signed(v) -> str:
    return f"{v:+.0f}".replace("-", "\u2212")  # true minus sign


def _get(t: pd.DataFrame | None) -> pd.DataFrame:
    return t if isinstance(t, pd.DataFrame) else pd.DataFrame()


def build(res, tables: dict[str, pd.DataFrame], themes: dict[str, pd.DataFrame],
          label=lambda c: c) -> list[Insight]:
    out: list[Insight] = []
    n_all = len(res.df) if res is not None else 0
    ov = _get(tables.get("overall"))
    ov = ov.set_index("metric")["value"] if not ov.empty else pd.Series(dtype=object)

    # ---- Knowledge (working, or a gap if an item is low) ----------------------
    rc = _get(tables.get("retro_change"))
    if not rc.empty and (~rc["suppressed"]).any():
        r = rc[~rc["suppressed"]].copy()
        r["gain"] = r["top_box_after"] - r["top_box_before"]
        r = r.sort_values("gain", ascending=False)
        parts = [f"*{label(x.item)}* {pct(x.top_box_before)} → **{pct(x.top_box_after)}**"
                 for x in r.itertuples()]
        lo, hi = r["top_box_after"].min(), r["top_box_after"].max()
        imp = ov.get("Retro change: % who improved on average")
        out.append(Insight(
            "working", "Knowledge goals are met",
            f"After the training {pct(lo)}–{pct(hi)} agree with each knowledge statement "
            f"({n_(r['n'].min())}). Agreement before → after, biggest gain first: " + "; ".join(parts) + "."
            + (f" {pct(imp)} rated themselves higher overall." if _ok(imp) else ""),
            "Keep the 988 explainer content: it produces the largest gains."))
        weak = r[r["top_box_after"] < C.SESSION_ALERT_AGREE_BELOW]
        for x in weak.itertuples():
            out.append(Insight(
                "gap", f"Knowledge is lagging on “{label(x.item)}”",
                f"Only {pct(x.top_box_after)} agree after the training ({n_(x.n)}).",
                "Add an example or short exercise on this point."))

    # ---- Delivery ------------------------------------------------------------
    deliv = ov.get("Delivery: % agree (avg of presenter/organization items)")
    n_deliv = ov.get("Delivery: n answered")
    if _ok(deliv) and _ok(n_deliv) and n_deliv >= C.MIN_N:
        kind = "working" if deliv >= C.SESSION_ALERT_DELIVERY_BELOW + 5 else "gap"
        out.append(Insight(kind, "Presenters and organization are rated " + ("well" if kind == "working" else "lower than ideal"),
                           f"{pct(deliv)} agree on average that the presenter engaged them, knew the "
                           f"subject and that the session was organized ({n_(n_deliv)})."))

    # ---- Audience gap -----------------------------------------------------------
    aud = _get(tables.get("by_audience"))
    tests = _get(tables.get("group_tests"))
    if not aud.empty and {"Students", "Adults"} <= set(aud["group"]):
        a = aud.set_index("group")
        s, ad = a.loc["Students"], a.loc["Adults"]
        t = tests[(tests.get("grouping", pd.Series(dtype=str)) == "audience")
                  & tests["metric"].str.startswith("Likelihood to recommend")] if not tests.empty else pd.DataFrame()
        sig = len(t) and t["p_value"].iloc[0] < 0.05
        if _ok(s["nps"]) and _ok(ad["nps"]) and sig and abs(s["nps"] - ad["nps"]) >= 15:
            low, high = ("Students", "Adults") if s["nps"] < ad["nps"] else ("Adults", "Students")
            share = s["n"] / (s["n"] + ad["n"]) * 100
            k_s = [s[f"pct_agree_{c}"] for c in res.likert_cols if c.startswith("outcome_") and f"pct_agree_{c}" in s]
            k_a = [ad[f"pct_agree_{c}"] for c in res.likert_cols if c.startswith("outcome_") and f"pct_agree_{c}" in ad]
            d_s = [s[f"pct_agree_{c}"] for c in res.likert_cols if c.startswith("aspect_") and f"pct_agree_{c}" in s]
            d_a = [ad[f"pct_agree_{c}"] for c in res.likert_cols if c.startswith("aspect_") and f"pct_agree_{c}" in ad]
            mean = lambda xs: sum(x for x in xs if _ok(x)) / max(1, sum(1 for x in xs if _ok(x)))
            bits = [f"Net Promoter Score **{signed(s['nps'])}** for students ({n_(s['n_recommend'])}) vs "
                    f"**{signed(ad['nps'])}** for adults ({n_(ad['n_recommend'])})"]
            if k_s and k_a:
                bits.append(f"knowledge after training {pct(mean(k_s))} vs {pct(mean(k_a))}")
            if d_s and d_a and all(map(_ok, d_s + d_a)):
                bits.append(f"delivery ratings {pct(mean(d_s))} vs {pct(mean(d_a))}")
            if _ok(s.get("pct_likely_988")) and _ok(ad.get("pct_likely_988")):
                bits.append(f"likely to call 988 {pct(s['pct_likely_988'])} ({n_(s['n_988'])}) vs "
                            f"{pct(ad['pct_likely_988'])} ({n_(ad['n_988'])})")
            similar = k_s and k_a and abs(mean(k_s) - mean(k_a)) < 5
            out.append(Insight(
                "gap", f"{low} rate the training far below {high.lower()}",
                f"Students are {share:.0f}% of respondents. " + "; ".join(bits) + ". "
                + ("Knowledge gains are similar, so the gap is in engagement, not learning. " if similar else "")
                + f"The difference is statistically significant ({'p < 0.001' if t['p_value'].iloc[0] < 0.001 else f'p = {t.p_value.iloc[0]:.3f}'}, "
                  f"{t['effect'].iloc[0]} effect).",
                f"Redesign the version for {low.lower()}: shorter segments, interactive activities, built-in Q&A."))

    # ---- Intent gap --------------------------------------------------------------
    p988, n988 = ov.get("Likely to call 988: % likely"), ov.get("Likely to call 988: n answered")
    ig = _get(tables.get("intent_gap"))
    if _ok(p988) and _ok(n988):
        detail = (f"{pct(p988)} say they are likely to call 988 (score "
                  f"{C.CALL_988_LIKELY_MIN_0_10}–10; {n_(n988)}).")
        if not ig.empty:
            last = ig[ig["item"] == ig["item"].max()]
            if len(last) == 2 and last["pct_likely_988"].notna().all():
                ag = last[last["knowledge"].str.startswith("Agrees")].iloc[0]
                no = last[~last["knowledge"].str.startswith("Agrees")].iloc[0]
                detail += (f" Among people who do **not** agree “{label(ag['item']).lower()}”, only "
                           f"{pct(no['pct_likely_988'])} are likely to call ({n_(no['n'])}), vs "
                           f"{pct(ag['pct_likely_988'])} of those who do ({n_(ag['n'])}).")
        out.append(Insight("gap" if p988 < 85 else "working",
                           "Intent to call 988 lags knowledge" if p988 < 85 else "Most say they would call 988",
                           detail, "Walk through what actually happens when you call or text 988 "
                                   "(who answers, confidentiality, how it differs from 911)." if p988 < 85 else ""))

    # ---- Trend (students if present, else everyone) --------------------------------
    tba = _get(tables.get("trend_by_audience"))
    tr = _get(tables.get("trend"))
    series, who = pd.DataFrame(), "everyone"
    if not tba.empty and "Students" in set(tba.get("audience", [])):
        series, who = tba[tba["audience"] == "Students"], "students"
    elif not tr.empty:
        series = tr
    if not series.empty:
        series = series[(~series["suppressed"]) & series["nps"].notna()].tail(3)
        if len(series) >= 2:
            vals = series["nps"].tolist()
            direction = ("falling" if all(b < a for a, b in zip(vals, vals[1:]))
                         else "rising" if all(b > a for a, b in zip(vals, vals[1:])) else "mixed")
            steps = ", ".join(f"{p} **{signed(v)}** ({n_(n)})" for p, v, n in
                              zip(series["period"], series["nps"], series["n_recommend"]))
            out.append(Insight(
                "watch", f"Recommend score for {who} is {direction}",
                f"Last {len(series)} periods: {steps}.",
                "Check the session scorecard for the latest period." if direction == "falling" else ""))

    # ---- Sessions -------------------------------------------------------------------
    ses = _get(tables.get("sessions"))
    if not ses.empty:
        flagged = ses[ses["needs_follow_up"]]
        detail = (f"{len(flagged)} of {len(ses)} sessions with {C.MIN_N}+ responses meet at least one "
                  f"follow-up flag.")
        if len(flagged):
            worst = flagged.dropna(subset=["nps"]).sort_values("nps").head(3)
            if len(worst):
                detail += " Lowest: " + "; ".join(
                    f"{pd.Timestamp(x.date):%b %d, %Y} {x.county} (NPS {signed(x.nps)}, {n_(x.n)})"
                    for x in worst.itertuples()) + "."
            # Compare like with like: if the weakest sessions are mostly students, name the best
            # student session (not an adult one) as the model to learn from.
            pool, who = ses.dropna(subset=["nps"]), "session"
            if len(worst) and "pct_students" in ses and worst["pct_students"].mean() >= 50:
                pool, who = pool[pool["pct_students"] >= 50], "student session"
            best = pool.sort_values("nps", ascending=False).head(1)
            if len(best):
                b = best.iloc[0]
                detail += (f" Highest-scoring {who}: {pd.Timestamp(b['date']):%b %d, %Y} {b['county']} "
                           f"(NPS {signed(b['nps'])}, {n_(b['n'])}).")
        out.append(Insight("watch", "Some sessions need follow-up", detail,
                           "Debrief flagged sessions with their facilitators and borrow from the highest-scoring ones."
                           if len(flagged) else ""))

    # ---- County within audience -----------------------------------------------------
    cba = _get(tables.get("county_by_audience"))
    if not cba.empty:
        for aud_name in ("Students", "Adults"):
            g = cba[(cba["split"] == aud_name) & (~cba["suppressed"]) & cba["nps"].notna()
                    & (cba["group"] != "Other (n<10)")]
            if len(g) >= 2:
                lo, hi = g.sort_values("nps").iloc[0], g.sort_values("nps").iloc[-1]
                if hi["nps"] - lo["nps"] >= 25:
                    out.append(Insight(
                        "watch", f"Among {aud_name.lower()}, results differ by county",
                        f"{hi['group']}: NPS {signed(hi['nps'])} ({n_(hi['n_recommend'])}) vs "
                        f"{lo['group']}: {signed(lo['nps'])} ({n_(lo['n_recommend'])}). Comparing within one "
                        f"audience removes the effect of audience mix.",
                        f"Find out what {hi['group']} sessions do differently for {aud_name.lower()}."))

    # ---- Participant voice -------------------------------------------------------------
    for col, t in themes.items():
        if col.endswith("_by_audience") or t is None or t.empty:
            continue
        top = t[(~t["under_min_n"]) & ~t["theme"].str.startswith("Other")].head(3)
        if not len(top):
            continue
        n_ans = int(t["n_answered"].iloc[0])
        q = ("Most valuable" if "valuable" in col else "How to improve" if "improve" in col else res.label(col))
        detail = f"Top themes ({n_(n_ans)} answers): " + "; ".join(
            f"*{x.theme}* {pct(x.pct_of_answered)}" for x in top.itertuples()) + "."
        tb = _get(themes.get(f"{col}_by_audience"))
        action = ""
        if not tb.empty and {"Students", "Adults"} <= set(tb["group"]):
            pv = tb.pivot(index="theme", columns="group", values="pct_of_answered").dropna()
            pv = pv[~pv.index.str.startswith("Other")]
            if len(pv):
                gap = (pv["Adults"] - pv["Students"]).abs().sort_values(ascending=False)
                th = gap.index[0]
                if gap.iloc[0] >= 8:
                    detail += (f" Biggest audience difference: *{th}* (adults {pct(pv.loc[th, 'Adults'])}, "
                               f"students {pct(pv.loc[th, 'Students'])}).")
        qrow = t[t["theme"].str.startswith("Asked a question")]
        if len(qrow) and qrow["pct_of_answered"].iloc[0] >= 15:
            action = "Many 'improve' answers are questions: add a Q&A block and a take-home FAQ card."
        out.append(Insight("working" if "valuable" in col else "watch", f"Participant voice: {q.lower()}",
                           detail + " (Keyword-coded; see Participant voice.)", action))

    # ---- Caveats ------------------------------------------------------------------------
    if _ok(n988) and n_all and n988 / n_all < 0.6:
        out.append(Insight("caveat", "The 988 question has low coverage",
                           f"Only {n988 / n_all * 100:.0f}% of respondents answered it ({n_(n988)}), so 988 results "
                           "describe that subset.", "Make the question required on every form version."))
    thin = []
    for g in ("by_language", "by_county", "by_role"):
        t = _get(tables.get(g))
        if not t.empty:
            for x in t[(~t["suppressed"]) & (t["n"] < C.THIN_N)].itertuples():
                if x.group not in ("Other (n<10)", "Not reported"):
                    thin.append(f"{x.group} (n = {int(x.n)})")
    if thin:
        out.append(Insight("caveat", "Some groups are too small for firm conclusions",
                           "Results for " + ", ".join(thin) + f" are based on fewer than {C.THIN_N} people: "
                           "treat them as indicative only."))
    if res is not None and res.retro_pairs:
        out.append(Insight("caveat", "Before-ratings are retrospective",
                           "Participants rated their 'before' knowledge after the training. Gains show "
                           "perceived learning and may be inflated by recall or politeness."))
    return out


def to_markdown(items: list[Insight]) -> str:
    """Render grouped markdown (headings in KINDS order)."""
    lines = []
    for kind, heading in KINDS.items():
        group = [i for i in items if i.kind == kind]
        if not group:
            continue
        lines.append(f"**{heading}**")
        for i in group:
            line = f"- **{i.title}.** {i.detail}"
            if i.action:
                line += f"  \n  ↳ *Suggested action:* {i.action}"
            lines.append(line)
        lines.append("")
    return "\n".join(lines)
